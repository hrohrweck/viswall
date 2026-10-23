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
    # Container-local state dir: pre-apply netplan snapshots live at
    # $STATE_DIR/snapshots/<ts> (newest 10 kept).
    state_dir: str
    # Try-mode execution surface (executed inside the host's namespaces).
    nsenter_binary: str
    netplan_binary: str
    dbus_system_bus_address: str
    netplan_try_timeout: int
    try_settle_seconds: float
    # Pre-confirm health probes for try-mode applies.
    probe_ssh_port: int
    probe_gateway_url: str
    probe_ping_target: str
    curl_binary: str
    ping_binary: str
    ss_binary: str
    # WAN address excluded from automation (never removable, with prefix).
    wan_ip: str

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
        state_dir=os.getenv("STATE_DIR", "/var/lib/viswall-node"),
        nsenter_binary=os.getenv("NSENTER_BINARY", "nsenter"),
        netplan_binary=os.getenv("NETPLAN_BINARY", "netplan"),
        dbus_system_bus_address=os.getenv(
            "DBUS_SYSTEM_BUS_ADDRESS", "/run/dbus/system_bus_socket"
        ),
        netplan_try_timeout=int(os.getenv("NETPLAN_TRY_TIMEOUT", "120")),
        try_settle_seconds=float(os.getenv("NETPLAN_TRY_SETTLE_SECONDS", "3.0")),
        probe_ssh_port=int(os.getenv("PROBE_SSH_PORT", "22")),
        probe_gateway_url=os.getenv(
            "PROBE_GATEWAY_URL", "http://127.0.0.1:8010/health"
        ),
        probe_ping_target=os.getenv("PROBE_PING_TARGET", "46.4.63.193"),
        curl_binary=os.getenv("CURL_BINARY", "curl"),
        ping_binary=os.getenv("PING_BINARY", "ping"),
        ss_binary=os.getenv("SS_BINARY", "ss"),
        wan_ip=os.getenv("WAN_IP", "46.4.63.216/32"),
    )
