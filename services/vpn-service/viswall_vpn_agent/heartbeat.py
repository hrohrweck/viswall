"""Periodic heartbeat to the viswall gateway so the console sees liveness.

The gateway route ``POST /api/v1/instances/{id}/heartbeat`` authenticates on
the request **body** ``api_key`` field (not the ``X-Instance-Key`` header used
by the agent API). This module posts ``{"api_key": ..., "status": "ok"}``
every 30 seconds using only the standard library, so the agent needs no extra
runtime dependency.

Failures are retried silently; a warning is emitted only after three
consecutive failures and at most once per minute, so a gateway outage cannot
flood the logs. Same contract and loop shape as the firewall agent (todo 12).
"""

from __future__ import annotations

import asyncio
import http.client
import json
import logging
import time
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from viswall_vpn_agent.main import AgentConfig

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30.0
HEARTBEAT_TIMEOUT = 5.0
FAILURE_LOG_THRESHOLD = 3
FAILURE_LOG_INTERVAL = 60.0

_NETWORK_ERRORS = (OSError, http.client.HTTPException)


def heartbeat_url(config: AgentConfig) -> str:
    """Build the gateway heartbeat URL from the agent configuration."""
    base = config.gateway_url.rstrip("/")
    return f"{base}/api/v1/instances/{config.instance_id}/heartbeat"


def _post_heartbeat(url: str, api_key: str) -> int:
    """POST the heartbeat body and return the HTTP status code."""
    body = json.dumps({"api_key": api_key, "status": "ok"}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HEARTBEAT_TIMEOUT) as response:
        response.read()
        return response.status


async def heartbeat_loop(config: AgentConfig) -> None:
    """Heartbeat forever; individual failures never stop the loop."""
    url = heartbeat_url(config)
    consecutive_failures = 0
    last_warning = 0.0

    while True:
        try:
            status = await asyncio.to_thread(
                _post_heartbeat, url, config.instance_api_key
            )
            logger.debug("heartbeat to %s ok (HTTP %s)", url, status)
            if consecutive_failures:
                logger.info(
                    "heartbeat to %s recovered after %d failure(s)",
                    url,
                    consecutive_failures,
                )
            consecutive_failures = 0
        except _NETWORK_ERRORS as exc:
            consecutive_failures += 1
            now = time.monotonic()
            if (
                consecutive_failures >= FAILURE_LOG_THRESHOLD
                and now - last_warning >= FAILURE_LOG_INTERVAL
            ):
                logger.warning(
                    "heartbeat to %s failed %d consecutive times: %s",
                    url,
                    consecutive_failures,
                    exc,
                )
                last_warning = now

        await asyncio.sleep(HEARTBEAT_INTERVAL)
