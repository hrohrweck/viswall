"""FastAPI control surface for the Viswall VPN agent.

Every endpoint except ``/health`` requires the ``X-Instance-Key`` header to
match ``INSTANCE_API_KEY`` (constant-time compare). ``main.py`` refuses to
start the process when the key is unset; if this module is imported directly
without the env var, the middleware answers 401 on everything except /health
instead of serving unauthenticated requests.

The ``/vpn/*`` endpoints (todo 16) sit on top of
``viswall_vpn_agent.wg_client.WgClientManager`` (todo 15) — this module adds
no unit steering or config writing of its own; it only CALLS the manager.

``/vpn/start`` and ``/vpn/stop`` accept a Pydantic BODY (``{protocol, name}``)
— the pre-package ``vpn_agent.py`` read ``protocol`` as a query parameter,
which made the gateway's JSON-body calls 422. ``name`` is optional because
the gateway's current ``/servers/{id}/start|stop`` dispatch sends only
``{"protocol": ...}``.

Env (read at import, same lifecycle as INSTANCE_API_KEY):

  * ``WG_CONF_DIR`` — directory for ``client.conf`` (default
    ``/etc/wireguard``). The verification smoke points it at a temp dir so
    the real host config is never written.
  * ``WG_SERVICE`` — systemd unit (default ``wg-quick@client``).
  * ``STATE_DIR`` — agent state dir (default ``/var/lib/viswall-vpn``).
"""

from __future__ import annotations

import asyncio
import os
import re
import secrets
import subprocess
from pathlib import Path

from viswall_vpn_agent.wg_client import (
    WgApplyError,
    WgClientConfig,
    WgClientError,
    WgClientManager,
    WgUnitError,
    validate_allowed_ips,
    validate_endpoint,
    validate_local_address,
    validate_wg_key,
)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, field_validator

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - fastapi is a runtime dependency
    FASTAPI_AVAILABLE = False

_WG_KEY_RE = re.compile(r"^[A-Za-z0-9+/]{43}=$")


if FASTAPI_AVAILABLE:
    app = FastAPI(title="Viswall VPN Agent", version="1.0.0")

    INSTANCE_API_KEY = os.getenv("INSTANCE_API_KEY")

    manager = WgClientManager(
        interface="client",
        wg_service=os.getenv("WG_SERVICE", "wg-quick@client"),
        config_path=Path(os.getenv("WG_CONF_DIR", "/etc/wireguard")) / "client.conf",
        state_dir=Path(os.getenv("STATE_DIR", "/var/lib/viswall-vpn")),
    )

    class InstanceKeyAuthMiddleware:
        """Pure-ASGI middleware: /health is open for liveness probes; every
        other endpoint requires X-Instance-Key to match INSTANCE_API_KEY."""

        def __init__(self, app, instance_api_key: str | None):
            self.app = app
            self.instance_api_key = instance_api_key

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or scope["path"] == "/health":
                await self.app(scope, receive, send)
                return

            provided = ""
            for name, value in scope["headers"]:
                if name == b"x-instance-key":
                    provided = value.decode("latin-1")
                    break

            if self.instance_api_key is None or not secrets.compare_digest(
                provided, self.instance_api_key
            ):
                response = JSONResponse(
                    status_code=401, content={"detail": "invalid instance key"}
                )
                await response(scope, receive, send)
                return

            await self.app(scope, receive, send)

    app.add_middleware(InstanceKeyAuthMiddleware, instance_api_key=INSTANCE_API_KEY)

    class VpnApplyRequest(BaseModel):
        """Body of ``POST /vpn/apply`` (todo 16 contract).

        ``private_key`` is optional: a partial model must render to a
        parseable file (key commented out) instead of failing validation.
        Every value that lands in client.conf is validated here (F2 BLOCKER
        #3): newline/CR/`=` injection, bad CIDRs, bad addresses/endpoints and
        malformed keys are rejected with 422 before any file is written.
        """

        protocol: str
        name: str
        address: str
        private_key: str | None = None
        endpoint: str
        peer_public_key: str
        allowed_ips: str
        persistent_keepalive: int = Field(default=25, ge=0, le=65535)

        @field_validator("address")
        @classmethod
        def _valid_address(cls, value: str) -> str:
            return validate_local_address(value)

        @field_validator("endpoint")
        @classmethod
        def _valid_endpoint(cls, value: str) -> str:
            return validate_endpoint(value)

        @field_validator("allowed_ips")
        @classmethod
        def _valid_allowed_ips(cls, value: str) -> str:
            return validate_allowed_ips(value)

        @field_validator("peer_public_key")
        @classmethod
        def _valid_peer_key(cls, value: str) -> str:
            result = validate_wg_key(value, "peer_public_key")
            assert result is not None
            return result

        @field_validator("private_key")
        @classmethod
        def _valid_private_key(cls, value: str | None) -> str | None:
            return validate_wg_key(value, "private_key")

    class VpnUnitRequest(BaseModel):
        """Body of ``POST /vpn/start`` / ``POST /vpn/stop``.

        ``name`` is optional because the gateway's start/stop dispatch sends
        only ``{"protocol": ...}`` today.
        """

        protocol: str
        name: str | None = None

    def _require_wireguard(protocol: str) -> None:
        """Reject non-WireGuard protocols with a clean 400 (not a 500)."""
        if protocol != "wireguard":
            raise HTTPException(
                status_code=400,
                detail=f"unsupported protocol {protocol!r}: only 'wireguard' "
                "is supported by this agent",
            )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "vpn-agent"}

    @app.post("/vpn/apply")
    async def vpn_apply(request: VpnApplyRequest):
        """Render + atomically write client.conf + restart the wg-quick unit.

        On a failed unit restart the manager restores the ``.viswall-backup``
        file and restarts the unit with it before raising; the caller
        surfaces that as a 500 with the stderr detail.
        """
        _require_wireguard(request.protocol)
        model = WgClientConfig(
            address=request.address,
            endpoint=request.endpoint,
            peer_public_key=request.peer_public_key,
            allowed_ips=request.allowed_ips,
            private_key=request.private_key,
            persistent_keepalive=request.persistent_keepalive,
        )
        try:
            await asyncio.to_thread(manager.apply, model)
        except WgApplyError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except WgClientError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {
            "applied": True,
            "name": request.name,
            "interface": manager.interface,
            "service": manager.wg_service,
            "config_path": str(manager.config_path),
        }

    @app.post("/vpn/start")
    async def vpn_start(request: VpnUnitRequest):
        """start = ``systemctl enable`` + ``systemctl start`` (state-sync rule)."""
        _require_wireguard(request.protocol)
        try:
            await asyncio.to_thread(manager.start)
        except WgUnitError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {
            "success": True,
            "action": "start",
            "service": manager.wg_service,
            "name": request.name,
        }

    @app.post("/vpn/stop")
    async def vpn_stop(request: VpnUnitRequest):
        """stop = ``systemctl disable`` + ``systemctl stop`` (state-sync rule)."""
        _require_wireguard(request.protocol)
        try:
            await asyncio.to_thread(manager.stop)
        except WgUnitError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {
            "success": True,
            "action": "stop",
            "service": manager.wg_service,
            "name": request.name,
        }

    @app.get("/vpn/status")
    async def vpn_status():
        """Live tunnel status via the manager's ``wg show``/``ip`` parser.

        A down/absent interface is tolerated (``up: false``), never an error.
        """
        status = await asyncio.to_thread(manager.status)
        return {
            "up": status.up,
            "interface": status.interface,
            "address": status.address,
            "endpoint": status.endpoint,
            "latest_handshake_sec": status.latest_handshake_sec,
            "transfer_rx": status.transfer_rx,
            "transfer_tx": status.transfer_tx,
            "allowed_ips": status.allowed_ips,
        }

    def _generate_keys() -> tuple[str, str]:
        """``wg genkey`` + ``wg pubkey`` (read-only, never touches netlink).

        Runs in a worker thread; keys are returned to the caller and are
        NEVER written to ``/etc/wireguard`` by this function.
        """
        try:
            gen = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if gen.returncode != 0:
                raise WgClientError(
                    f"wg genkey exited {gen.returncode}: {gen.stderr.strip()}"
                )
            private = gen.stdout.strip()
            pub = subprocess.run(
                ["wg", "pubkey"],
                input=private,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if pub.returncode != 0:
                raise WgClientError(
                    f"wg pubkey exited {pub.returncode}: {pub.stderr.strip()}"
                )
            public = pub.stdout.strip()
        except OSError as exc:
            raise WgClientError(f"cannot execute wg: {exc}") from exc
        if not _WG_KEY_RE.fullmatch(private) or not _WG_KEY_RE.fullmatch(public):
            raise WgClientError("wg produced malformed key material")
        return private, public

    @app.post("/vpn/generate-keys")
    async def vpn_generate_keys():
        """Fresh keypair; keys are returned, never persisted by the agent."""
        try:
            private, public = await asyncio.to_thread(_generate_keys)
        except WgClientError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"private_key": private, "public_key": public}
