"""FastAPI control surface for the Viswall firewall agent.

Ported from the former single-file agent with one behavioral change: every
endpoint except ``/health`` now requires the ``X-Instance-Key`` header to
match ``INSTANCE_API_KEY`` (constant-time compare) — this closes the
previously unauthenticated :8081 hole. ``main.py`` refuses to start the
process when the key is unset; if this module is imported directly without the
env var, the middleware answers 401 on everything except /health instead of
serving unauthenticated requests.

``ContentFilterManager`` from the old file was intentionally not ported: no
endpoint in the old agent and no later todo (7-14) references it — unreachable
dead code (squid config generation), documented here so the omission is
deliberate, not accidental.
"""

import asyncio
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from viswall_firewall_agent.nft import NATRule, NFTablesManager, FirewallRule
from viswall_firewall_agent.qos import TrafficControlManager
from viswall_firewall_agent.routing import RoutingManager

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    from typing import List as TypingList

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class FirewallAgent:
    """Main firewall agent coordinating all components"""

    def __init__(self):
        self.nftables = NFTablesManager()
        self.tc = TrafficControlManager()
        self.routing = RoutingManager()

    async def deploy_firewall_config(
        self,
        interfaces: List[Dict[str, str]],
        rules: List[Dict[str, Any]],
        nat_rules: List[Dict[str, Any]],
        routing_rules: List[Dict[str, Any]],
        qos_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Deploy complete firewall configuration"""

        # Convert dict rules to objects
        fw_rules = [FirewallRule(**r) for r in rules]
        nat = [NATRule(**r) for r in nat_rules]

        # Generate and apply nftables
        ruleset = self.nftables.generate_ruleset(
            interfaces=interfaces, firewall_rules=fw_rules, nat_rules=nat
        )

        nft_ok = await self.nftables.apply_ruleset(ruleset)

        # Apply QoS if configured
        tc_ok = True
        if qos_config:
            for interface, config in qos_config.items():
                tc_ok = await self.tc.setup_qos(
                    interface=interface,
                    download_rate=config["download"],
                    upload_rate=config["upload"],
                    algorithm=config.get("algorithm", "cake"),
                )
                if not tc_ok:
                    break

        # Apply routing rules
        routing_ok = True
        for rule in routing_rules:
            routing_ok = await self.routing.add_policy_rule(
                table=rule.get("table", 254),
                priority=rule.get("priority", 100),
                source=rule.get("source"),
                destination=rule.get("destination"),
                mark=rule.get("mark"),
                interface=rule.get("interface"),
            )
            if not routing_ok:
                break

        return nft_ok and tc_ok and routing_ok

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive firewall statistics"""

        # Get nftables stats
        nft_stats = await self.nftables.get_stats()

        # Get conntrack info
        conntrack_count = 0
        try:
            proc = await asyncio.create_subprocess_exec(
                "conntrack",
                "-C",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            conntrack_count = int(stdout.decode().strip())
        except:
            pass

        return {
            "nftables": nft_stats,
            "connections": {
                "tracked": conntrack_count,
                "max": 262144,  # Default nf_conntrack_max
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def block_ip(self, ip: str, reason: str = "manual") -> bool:
        """Block an IP address"""
        return await self.nftables.add_to_blacklist(ip)

    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        return await self.nftables.remove_from_blacklist(ip)


# ============================================================================
# HTTP API Server (for API gateway → agent communication)
# ============================================================================

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Viswall Firewall Agent", version="1.0.0")
    agent = FirewallAgent()

    INSTANCE_API_KEY = os.getenv("INSTANCE_API_KEY")

    class InstanceKeyAuthMiddleware:
        """Pure-ASGI middleware: /health is open for liveness probes, every
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

    class QoSApplyRequest(BaseModel):
        interface: str
        algorithm: str
        download_kbps: int
        upload_kbps: int
        classes: TypingList[dict] = []

    class QoSClearRequest(BaseModel):
        interface: str

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "firewall-agent"}

    @app.post("/qos/apply")
    async def api_apply_qos(request: QoSApplyRequest):
        ok = await agent.tc.setup_qos(
            interface=request.interface,
            download_rate=request.download_kbps,
            upload_rate=request.upload_kbps,
            algorithm=request.algorithm,
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to apply QoS")
        return {
            "success": True,
            "interface": request.interface,
            "algorithm": request.algorithm,
        }

    @app.post("/qos/clear")
    async def api_clear_qos(request: QoSClearRequest):
        try:
            await agent.tc._run_tc(["qdisc", "del", "dev", request.interface, "root"])
            return {"success": True, "interface": request.interface}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clear QoS: {e}")

    @app.get("/qos/stats/{interface}")
    async def api_qos_stats(interface: str):
        stats = await agent.tc.get_stats(interface)
        return {"interface": interface, "stats": stats}

    @app.get("/stats")
    async def api_system_stats():
        return await agent.get_system_stats()

    @app.post("/block")
    async def api_block_ip(ip: str, reason: str = "manual"):
        ok = await agent.block_ip(ip, reason)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to block IP")
        return {"success": True, "ip": ip}

    @app.post("/unblock")
    async def api_unblock_ip(ip: str):
        ok = await agent.unblock_ip(ip)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to unblock IP")
        return {"success": True, "ip": ip}
