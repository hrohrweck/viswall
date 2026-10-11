"""Environment configuration for the Viswall node agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Immutable runtime configuration parsed from the environment."""

    instance_api_key: str | None
    gateway_url: str | None
    instance_id: int | None
    heartbeat_interval: float
    api_host: str
    api_port: int
    # Read-only view of the host filesystem root for network state that
    # is not exposed through the shared network namespace (reserved for
    # future host telemetry; interface state comes from netlink directly).
    host_root: str
    # Directory containing host netplan config, bind-mounted read-write so
    # applied interface configuration survives reboots. Empty disables
    # persistence (live apply only).
    netplan_dir: str
    netplan_file: str
    ip_binary: str

    @property
    def heartbeat_enabled(self) -> bool:
        return (
            self.gateway_url is not None
            and self.instance_id is not None
            and self.instance_api_key is not None
        )

    @property
    def netplan_path(self) -> str | None:
        if not self.netplan_dir:
            return None
        return os.path.join(self.netplan_dir, self.netplan_file)


def load_config() -> AgentConfig:
    """Parse agent configuration from environment variables."""
    instance_id_raw = os.getenv("INSTANCE_ID")
    return AgentConfig(
        instance_api_key=os.getenv("INSTANCE_API_KEY") or None,
        gateway_url=os.getenv("GATEWAY_URL") or None,
        instance_id=int(instance_id_raw) if instance_id_raw else None,
        heartbeat_interval=float(os.getenv("HEARTBEAT_INTERVAL", "30")),
        api_host=os.getenv("AGENT_HOST", "0.0.0.0"),
        api_port=int(os.getenv("AGENT_PORT", "8085")),
        host_root=os.getenv("HOST_ROOT", "/host"),
        netplan_dir=os.getenv("NETPLAN_DIR", "/etc/netplan"),
        netplan_file=os.getenv("NETPLAN_FILE", "60-viswall.yaml"),
        ip_binary=os.getenv("IP_BINARY", "ip"),
    )
