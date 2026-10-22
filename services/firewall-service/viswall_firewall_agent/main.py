"""Process entrypoint for the Viswall firewall agent.

Reads configuration from the environment (``INSTANCE_API_KEY`` is mandatory —
the process exits non-zero without it) and serves the FastAPI control surface
from ``viswall_firewall_agent.api`` on ``FIREWALL_AGENT_PORT``. The old
``run_server`` helper (hardcoded host "::" port 8081) is superseded by this
config-driven startup.

A gateway heartbeat task starts once uvicorn has bound its socket and is
cancelled on shutdown, so the console sees liveness for exactly as long as the
agent is serving.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
from dataclasses import dataclass

import uvicorn

from viswall_firewall_agent.heartbeat import heartbeat_loop


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Immutable runtime configuration parsed from the environment."""

    instance_api_key: str
    gateway_url: str
    instance_id: int
    port: int
    state_dir: str
    host: str = "::"


def load_config() -> AgentConfig:
    """Parse agent configuration; exits non-zero if INSTANCE_API_KEY is unset."""
    instance_api_key = os.getenv("INSTANCE_API_KEY")
    if not instance_api_key:
        print(
            "FATAL: INSTANCE_API_KEY is not set. Refusing to start the firewall "
            "agent without authentication (every endpoint except /health "
            "requires the X-Instance-Key header).",
            file=sys.stderr,
        )
        sys.exit(1)

    return AgentConfig(
        instance_api_key=instance_api_key,
        gateway_url=os.getenv("GATEWAY_URL", "http://127.0.0.1:8010"),
        instance_id=int(os.getenv("INSTANCE_ID", "1")),
        port=int(os.getenv("FIREWALL_AGENT_PORT", "8081")),
        state_dir=os.getenv("STATE_DIR", "/var/lib/viswall-firewall"),
    )


async def _run_heartbeat_when_serving(
    server: uvicorn.Server, config: AgentConfig
) -> None:
    """Wait for uvicorn to bind, then run the heartbeat loop forever."""
    while not server.started:
        await asyncio.sleep(0.1)
    await heartbeat_loop(config)


async def main() -> None:
    """Start uvicorn serving viswall_firewall_agent.api:app plus heartbeat."""
    config = load_config()
    os.makedirs(config.state_dir, exist_ok=True)
    server = uvicorn.Server(
        uvicorn.Config(
            "viswall_firewall_agent.api:app",
            host=config.host,
            port=config.port,
            log_level="info",
        )
    )
    heartbeat_task = asyncio.create_task(
        _run_heartbeat_when_serving(server, config),
        name="gateway-heartbeat",
    )
    try:
        await server.serve()
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


if __name__ == "__main__":
    asyncio.run(main())
