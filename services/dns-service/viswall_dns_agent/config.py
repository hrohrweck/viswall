"""Environment configuration for the Viswall DNS agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Immutable runtime configuration parsed from the environment."""

    named_conf_path: str
    named_options_path: str
    zones_dir: str
    keys_dir: str
    allow_commands: bool
    instance_api_key: str | None
    gateway_url: str | None
    instance_id: int | None
    heartbeat_interval: float
    api_host: str
    api_port: int

    @property
    def heartbeat_enabled(self) -> bool:
        return (
            self.gateway_url is not None
            and self.instance_id is not None
            and self.instance_api_key is not None
        )


def load_config() -> AgentConfig:
    """Parse agent configuration from environment variables."""
    instance_id_raw = os.getenv("INSTANCE_ID")
    return AgentConfig(
        named_conf_path=os.getenv("NAMED_CONF_PATH", "/etc/bind/named.conf.local"),
        named_options_path=os.getenv(
            "NAMED_OPTIONS_PATH", "/etc/bind/named.conf.options"
        ),
        zones_dir=os.getenv("ZONES_DIR", "/var/lib/bind/viswall-zones"),
        keys_dir=os.getenv("DNS_KEYS_DIR", "/var/lib/bind/keys"),
        allow_commands=os.getenv("DNS_AGENT_ALLOW_COMMANDS", "false").lower() == "true",
        instance_api_key=os.getenv("INSTANCE_API_KEY") or None,
        gateway_url=os.getenv("GATEWAY_URL") or None,
        instance_id=int(instance_id_raw) if instance_id_raw else None,
        heartbeat_interval=float(os.getenv("HEARTBEAT_INTERVAL", "30")),
        api_host=os.getenv("AGENT_HOST", "0.0.0.0"),
        api_port=int(os.getenv("AGENT_PORT", "8082")),
    )
