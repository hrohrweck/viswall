"""FastAPI control surface for the Viswall node agent.

Mutating and introspecting endpoints require the X-Instance-Key header
to match the INSTANCE_API_KEY shared with the gateway. /health stays
unauthenticated for container liveness probes.
"""

from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from typing import Any, Dict

import anyio
from fastapi import Depends, FastAPI, Header, HTTPException

from viswall_node_agent.config import AgentConfig, load_config
from viswall_node_agent.heartbeat import heartbeat_loop
from viswall_node_agent.netcfg import (
    PlanRefused,
    WanGuardrailRefused,
    apply_interfaces,
    discover,
)
from viswall_node_agent.payloads import ApplyRequest, ApplyResult

logger = logging.getLogger(__name__)

config: AgentConfig = load_config()


async def require_instance_key(
    x_instance_key: str | None = Header(default=None, alias="X-Instance-Key"),
) -> None:
    if config.instance_api_key is None:
        raise HTTPException(
            status_code=503,
            detail="INSTANCE_API_KEY not configured on agent; refusing requests",
        )
    provided = x_instance_key or ""
    if not secrets.compare_digest(provided, config.instance_api_key):
        raise HTTPException(status_code=401, detail="invalid instance key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(heartbeat_loop, config)
        yield


app = FastAPI(title="Viswall Node Agent", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "node-agent",
        "auth_configured": config.instance_api_key is not None,
        "heartbeat_enabled": config.heartbeat_enabled,
        "netplan_persistence": config.netplan_path,
    }


@app.get("/interfaces")
async def list_interfaces(_: None = Depends(require_instance_key)) -> Dict[str, Any]:
    try:
        interfaces, default_iface, default_gw = await discover(config)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "interfaces": [iface.model_dump() for iface in interfaces],
        "default_route_interface": default_iface,
        "default_gateway": default_gw,
    }


@app.post("/interfaces/apply", response_model=ApplyResult)
async def apply_interface_config(
    request: ApplyRequest,
    _: None = Depends(require_instance_key),
) -> ApplyResult:
    try:
        return await apply_interfaces(config, request)
    except PlanRefused as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WanGuardrailRefused as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
