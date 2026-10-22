"""Gateway heartbeat — the loop itself is implemented in todo 12.

Todo 12 defines the real behavior: ``POST {GATEWAY_URL}/api/v1/instances/
{INSTANCE_ID}/heartbeat`` every 30 s with body ``{"api_key": ..., "status":
"ok"}`` (the gateway authenticates on the BODY api_key, not the
X-Instance-Key header). This module only declares the task interface; calling
it fails loudly so a stub can never be mistaken for a working implementation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from viswall_firewall_agent.main import AgentConfig

logger = logging.getLogger(__name__)


async def heartbeat_loop(config: AgentConfig) -> None:
    """Interface stub — the 30-second heartbeat loop lands in todo 12."""
    raise NotImplementedError("heartbeat loop is implemented in todo 12")
