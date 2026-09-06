"""Periodic heartbeat to the viswall gateway so the console sees liveness."""

from __future__ import annotations

import logging

import anyio
import httpx

from viswall_dns_agent.config import AgentConfig

logger = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT = 5.0


async def heartbeat_loop(config: AgentConfig) -> None:
    """POST /instances/{id}/heartbeat every heartbeat_interval seconds.

    Runs forever; individual failures are logged and never propagate so the
    loop outlives gateway restarts. Disabled unless gateway_url, instance_id
    and instance_api_key are all configured.
    """
    if not config.heartbeat_enabled:
        logger.warning(
            "heartbeat disabled: GATEWAY_URL/INSTANCE_ID/INSTANCE_API_KEY incomplete"
        )
        return

    url = f"{config.gateway_url}/api/v1/instances/{config.instance_id}/heartbeat"
    payload = {"api_key": config.instance_api_key}

    while True:
        try:
            async with httpx.AsyncClient(timeout=HEARTBEAT_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.warning(
                        "heartbeat to %s returned %s", url, response.status_code
                    )
                else:
                    logger.debug("heartbeat ok")
        except httpx.HTTPError as exc:
            logger.warning("heartbeat to %s failed: %s", url, exc)
        await anyio.sleep(config.heartbeat_interval)
