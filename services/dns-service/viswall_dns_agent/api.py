"""FastAPI control surface for the Viswall DNS agent.

All mutating endpoints require the X-Instance-Key header to match the
INSTANCE_API_KEY shared with the gateway. /health stays unauthenticated for
container liveness probes.
"""

from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import anyio
from fastapi import Depends, FastAPI, Header, HTTPException

from viswall_dns_agent.agent import DNSAgent
from viswall_dns_agent.config import AgentConfig, load_config
from viswall_dns_agent.heartbeat import heartbeat_loop
from viswall_dns_agent.payloads import (
    ApplyResult,
    DNSServerConfigPayload,
    DNSZonePayload,
    SignResult,
)

logger = logging.getLogger(__name__)

config: AgentConfig = load_config()
agent = DNSAgent(config)


async def require_instance_key(
    x_instance_key: str | None = Header(default=None, alias="X-Instance-Key"),
) -> None:
    if config.instance_api_key is None:
        raise HTTPException(
            status_code=503,
            detail="INSTANCE_API_KEY not configured on agent; refusing mutations",
        )
    provided = x_instance_key or ""
    if not secrets.compare_digest(provided, config.instance_api_key):
        raise HTTPException(status_code=401, detail="invalid instance key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(heartbeat_loop, config)
        yield


app = FastAPI(title="Viswall DNS Agent", version="2.0.0", lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "dns-agent",
        "named_conf": str(agent.named_conf_path),
        "named_options": str(agent.named_options_path),
        "zones_dir": str(agent.zones_path),
        "keys_dir": str(agent.keys_path),
        "commands_enabled": config.allow_commands,
        "auth_configured": config.instance_api_key is not None,
        "heartbeat_enabled": config.heartbeat_enabled,
    }


@app.post("/dns/apply", response_model=ApplyResult)
async def apply_dns_config(
    payload: DNSServerConfigPayload,
    _: None = Depends(require_instance_key),
) -> ApplyResult:
    try:
        agent.write_configs(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"failed to write config: {exc}") from exc

    reload_result = agent.reload_bind()
    if not reload_result.get("skipped") and reload_result.get("returncode", 1) != 0:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to reload BIND", "result": reload_result},
        )
    return ApplyResult(
        success=True,
        message="DNS configuration applied",
        updated_at=datetime.utcnow(),
    )


@app.post("/dns/sign-zone/{zone_id}", response_model=SignResult)
async def sign_zone(
    zone_id: int,
    zone: DNSZonePayload,
    _: None = Depends(require_instance_key),
) -> SignResult:
    if zone.id != zone_id:
        raise HTTPException(status_code=400, detail="Zone ID mismatch")
    return agent.sign_zone(zone)


@app.post("/dns/generate-tsig")
async def generate_tsig(
    algorithm: str = "hmac-sha256",
    _: None = Depends(require_instance_key),
) -> Dict[str, Any]:
    try:
        return {
            "success": True,
            "algorithm": algorithm,
            "secret": agent.generate_tsig_secret(algorithm=algorithm),
            "generated_at": datetime.utcnow().isoformat(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/dns/reload")
async def reload_dns(_: None = Depends(require_instance_key)) -> Dict[str, Any]:
    result = agent.reload_bind()
    if not result.get("skipped") and result.get("returncode", 1) != 0:
        raise HTTPException(status_code=500, detail=result)
    return {"status": "success", "result": result}


@app.get("/dns/status")
async def dns_status(_: None = Depends(require_instance_key)) -> Dict[str, Any]:
    return {"status": "success", "result": agent.bind_status()}
