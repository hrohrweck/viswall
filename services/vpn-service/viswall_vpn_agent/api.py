"""FastAPI control surface for the Viswall VPN agent.

Every endpoint except ``/health`` requires the ``X-Instance-Key`` header to
match ``INSTANCE_API_KEY`` (constant-time compare). ``main.py`` refuses to
start the process when the key is unset; if this module is imported directly
without the env var, the middleware answers 401 on everything except /health
instead of serving unauthenticated requests.

For NOW only ``/health`` is exposed. The ``/vpn/*`` control endpoints
(apply/start/stop/status/generate-keys) land in todo 16, wired onto
``viswall_vpn_agent.wg_client.WgClientManager`` — the app is already
importable as ``viswall_vpn_agent.api.app`` so todo 16 only adds routes.
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - fastapi is a runtime dependency
    FASTAPI_AVAILABLE = False


if FASTAPI_AVAILABLE:
    app = FastAPI(title="Viswall VPN Agent", version="1.0.0")

    INSTANCE_API_KEY = os.getenv("INSTANCE_API_KEY")

    class InstanceKeyAuthMiddleware:
        """Pure-ASGI middleware: /health is open for liveness probes; every
        other endpoint requires X-Instance-Key to match INSTANCE_API_KEY."""

        def __init__(self, app, instance_api_key: Optional[str]):
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

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "vpn-agent"}
