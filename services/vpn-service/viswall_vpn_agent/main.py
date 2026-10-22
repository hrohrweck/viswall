"""Process entrypoint for the Viswall VPN agent.

Reads configuration from the environment (``INSTANCE_API_KEY`` is mandatory —
the process exits non-zero without it) and serves the FastAPI control surface
from ``viswall_vpn_agent.api`` on ``VPN_AGENT_PORT``.

Startup reconcile is GATED behind ``$STATE_DIR/takeover``: without that
marker the agent never touches the wg-quick unit's run/enabled state (the
host still owns the tunnel until the todo-42 live validation flips the
marker). The marker check is logged at boot; the reconcile loop itself lands
with the endpoints in todo 16.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import uvicorn

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Immutable runtime configuration parsed from the environment."""

    instance_api_key: str
    gateway_url: str
    instance_id: int
    port: int
    state_dir: Path
    wg_service: str
    host: str = "::"


def load_config() -> AgentConfig:
    """Parse agent configuration; exits non-zero if INSTANCE_API_KEY is unset."""
    instance_api_key = os.getenv("INSTANCE_API_KEY")
    if not instance_api_key:
        print(
            "FATAL: INSTANCE_API_KEY is not set. Refusing to start the vpn "
            "agent without authentication (every endpoint except /health "
            "requires the X-Instance-Key header).",
            file=sys.stderr,
        )
        sys.exit(1)

    return AgentConfig(
        instance_api_key=instance_api_key,
        gateway_url=os.getenv("GATEWAY_URL", "http://127.0.0.1:8010"),
        instance_id=int(os.getenv("INSTANCE_ID", "1")),
        port=int(os.getenv("VPN_AGENT_PORT", "8083")),
        state_dir=Path(os.getenv("STATE_DIR", "/var/lib/viswall-vpn")),
        wg_service=os.getenv("WG_SERVICE", "wg-quick@client"),
    )


async def main() -> None:
    """Start uvicorn serving viswall_vpn_agent.api:app."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    config = load_config()
    config.state_dir.mkdir(parents=True, exist_ok=True)

    if (config.state_dir / "takeover").exists():
        logger.info(
            "takeover marker present — startup reconcile enabled "
            "(wired with the endpoints in todo 16)"
        )
    else:
        logger.info(
            "takeover marker absent — startup reconcile disabled; "
            "the host still owns the tunnel and the agent will not touch "
            "the unit's run/enabled state"
        )

    server = uvicorn.Server(
        uvicorn.Config(
            "viswall_vpn_agent.api:app",
            host=config.host,
            port=config.port,
            log_level="info",
        )
    )
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
