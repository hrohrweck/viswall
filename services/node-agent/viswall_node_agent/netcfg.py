"""Host interface management: discovery, guarded live apply, netplan persistence.

The agent container shares the host network namespace with NET_ADMIN,
so `ip` invocations here reconfigure the host's real interfaces.
Desired state is additionally rendered into a netplan file so it
survives reboots.

Safety model: every mutation is planned first (pure functions, unit
tested); a plan that touches the interface carrying the default route —
typically the management connection — or the default route itself is
refused unless the caller explicitly sets force=True.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Any

from viswall_node_agent.config import AgentConfig
from viswall_node_agent.payloads import (
    ApplyChange,
    ApplyRequest,
    ApplyResult,
    InterfaceConfig,
    LiveAddress,
    LiveInterface,
)

logger = logging.getLogger(__name__)

IP_TIMEOUT_SECONDS = 10.0


class PlanRefused(Exception):
    """A planned change would likely cut management connectivity."""


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

async def run_ip(config: AgentConfig, *args: str) -> tuple[int, str, str]:
    """Run `ip <args>` and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        config.ip_binary,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=IP_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return (
        proc.returncode or 0,
        stdout.decode(errors="replace").strip(),
        stderr.decode(errors="replace").strip(),
    )


def parse_addr_json(rows: list[dict[str, Any]]) -> list[LiveInterface]:
    """Parse `ip -j addr show` output into LiveInterface models (v4 only)."""
    interfaces: list[LiveInterface] = []
    for row in rows:
        name = row.get("ifname")
        if not name:
            continue
        addresses = [
            LiveAddress(address=info["local"], prefixlen=info["prefixlen"])
            for info in row.get("addr_info", [])
            if info.get("family") == "inet" and info.get("local")
        ]
        interfaces.append(
            LiveInterface(
                name=name,
                operstate=row.get("operstate", "unknown"),
                up="UP" in (row.get("flags") or []),
                mtu=row.get("mtu"),
                mac=row.get("address"),
                addresses=addresses,
            )
        )
    return interfaces


def parse_default_route(
    rows: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Extract (interface, gateway) from `ip -j route show` output."""
    for row in rows:
        if row.get("dst") == "default":
            return row.get("dev"), row.get("gateway")
    return None, None


async def discover(
    config: AgentConfig,
) -> tuple[list[LiveInterface], str | None, str | None]:
    """Live interface and default-route state of the host."""
    rc_addr, addr_out, addr_err = await run_ip(config, "-j", "addr", "show")
    if rc_addr != 0:
        raise RuntimeError(f"ip addr show failed: {addr_err}")
    rc_route, route_out, route_err = await run_ip(config, "-j", "route", "show")
    if rc_route != 0:
        raise RuntimeError(f"ip route show failed: {route_err}")

    import json

    interfaces = parse_addr_json(json.loads(addr_out or "[]"))
    default_iface, default_gw = parse_default_route(json.loads(route_out or "[]"))
    for iface in interfaces:
        iface.has_default_route = iface.name == default_iface
    return interfaces, default_iface, default_gw


# ---------------------------------------------------------------------------
# Planning (pure)
# ---------------------------------------------------------------------------

@dataclass
class PlannedStep:
    interface: str
    action: str  # address | stale-address | gateway | mtu | link | note
    detail: str
    argv: list[str] = field(default_factory=list)


def plan_changes(
    live: list[LiveInterface],
    default_iface: str | None,
    default_gw: str | None,
    desired: list[InterfaceConfig],
) -> list[PlannedStep]:
    """Compute the netlink mutations that bring live state to desired.

    Idempotent: only differences produce steps. Raises ValueError for
    structurally impossible requests (unknown interface, static config
    without netmask, duplicate names).
    """
    names = [cfg.name for cfg in desired]
    if len(names) != len(set(names)):
        raise ValueError("duplicate interface names in request")

    live_map = {iface.name: iface for iface in live}
    steps: list[PlannedStep] = []

    for cfg in desired:
        current = live_map.get(cfg.name)

        if current is None:
            raise ValueError(
                f"interface {cfg.name} does not exist on the host; "
                "physical interfaces cannot be created"
            )

        manage_address = cfg.enabled and cfg.config_type == "static"
        desired_addr = None
        if manage_address:
            if cfg.ip_address and not cfg.prefixlen:
                raise ValueError(
                    f"static configuration for {cfg.name} requires a netmask"
                )
            if cfg.ip_address:
                desired_addr = (cfg.ip_address, cfg.prefixlen)
            elif cfg.gateway:
                raise ValueError(
                    f"static configuration for {cfg.name} has a gateway but no address"
                )

        # --- address -------------------------------------------------------
        current_addrs = {(a.address, a.prefixlen) for a in current.addresses}
        if desired_addr is not None:
            if desired_addr not in current_addrs:
                steps.append(
                    PlannedStep(
                        interface=cfg.name,
                        action="address",
                        detail=f"set address {desired_addr[0]}/{desired_addr[1]}",
                        argv=["addr", "replace", f"{desired_addr[0]}/{desired_addr[1]}", "dev", cfg.name],
                    )
                )
            for stale in sorted(current_addrs - {desired_addr}):
                steps.append(
                    PlannedStep(
                        interface=cfg.name,
                        action="stale-address",
                        detail=f"remove address {stale[0]}/{stale[1]}",
                        argv=["addr", "del", f"{stale[0]}/{stale[1]}", "dev", cfg.name],
                    )
                )
        elif cfg.config_type == "static" and not cfg.enabled:
            # Explicitly disabled static interface: drop its live addresses.
            for stale in sorted(current_addrs):
                steps.append(
                    PlannedStep(
                        interface=cfg.name,
                        action="stale-address",
                        detail=f"remove address {stale[0]}/{stale[1]} (interface disabled)",
                        argv=["addr", "del", f"{stale[0]}/{stale[1]}", "dev", cfg.name],
                    )
                )
        # DHCP-managed addresses are owned by the DHCP client — untouched live.

        # --- mtu -----------------------------------------------------------
        if cfg.mtu is not None and current.mtu != cfg.mtu:
            steps.append(
                PlannedStep(
                    interface=cfg.name,
                    action="mtu",
                    detail=f"set mtu {cfg.mtu} (current {current.mtu})",
                    argv=["link", "set", "dev", cfg.name, "mtu", str(cfg.mtu)],
                )
            )

        # --- link state ----------------------------------------------------
        if cfg.enabled and not current.up:
            steps.append(
                PlannedStep(
                    interface=cfg.name,
                    action="link",
                    detail="bring interface up",
                    argv=["link", "set", "dev", cfg.name, "up"],
                )
            )
        elif not cfg.enabled and current.up:
            steps.append(
                PlannedStep(
                    interface=cfg.name,
                    action="link",
                    detail="bring interface down",
                    argv=["link", "set", "dev", cfg.name, "down"],
                )
            )

        # --- gateway -------------------------------------------------------
        if manage_address:
            live_default_here = default_iface == cfg.name
            if cfg.gateway and (not live_default_here or default_gw != cfg.gateway):
                steps.append(
                    PlannedStep(
                        interface=cfg.name,
                        action="gateway",
                        detail=f"set default route via {cfg.gateway}",
                        argv=["route", "replace", "default", "via", cfg.gateway, "dev", cfg.name],
                    )
                )
            elif not cfg.gateway and live_default_here:
                steps.append(
                    PlannedStep(
                        interface=cfg.name,
                        action="gateway",
                        detail="remove default route",
                        argv=["route", "del", "default"],
                    )
                )
        if cfg.config_type == "dhcp" and cfg.enabled:
            steps.append(
                PlannedStep(
                    interface=cfg.name,
                    action="note",
                    detail="dhcp4 enabled in netplan; takes effect at next boot or netplan apply",
                )
            )

    return steps


def guard_plan(
    steps: list[PlannedStep],
    default_iface: str | None,
    force: bool,
) -> None:
    """Refuse plans that can cut management connectivity without force."""
    if force or default_iface is None:
        return
    touching = [
        step for step in steps
        if step.interface == default_iface and step.action in (
            "address", "stale-address", "gateway", "link",
        )
    ]
    if touching:
        details = "; ".join(f"{s.action}: {s.detail}" for s in touching)
        raise PlanRefused(
            f"interface {default_iface} carries the default route; the plan "
            f"would alter it ({details}). Retry with force to acknowledge "
            "possible loss of management connectivity."
        )


# ---------------------------------------------------------------------------
# Netplan persistence
# ---------------------------------------------------------------------------

def render_netplan(interfaces: list[InterfaceConfig]) -> str:
    """Render managed interfaces as a netplan ethernets config."""
    lines = ["network:", "  version: 2", "  ethernets:"]
    for cfg in sorted(interfaces, key=lambda c: c.name):
        lines.append(f"    {cfg.name}:")
        managed_static = cfg.enabled and cfg.config_type == "static" and cfg.ip_address
        lines.append(f"      dhcp4: {'true' if cfg.enabled and cfg.config_type == 'dhcp' else 'false'}")
        if managed_static:
            lines.append(f'      addresses: ["{cfg.ip_address}/{cfg.prefixlen}"]')
            if cfg.gateway:
                lines.append("      routes:")
                lines.append("        - to: default")
                lines.append(f"          via: {cfg.gateway}")
        if not cfg.enabled:
            # Unconfigured at boot; optional avoids boot delays waiting for it.
            lines.append("      optional: true")
        if cfg.mtu is not None:
            lines.append(f"      mtu: {cfg.mtu}")
    return "\n".join(lines) + "\n"


def write_netplan(path: str | None, content: str) -> bool:
    """Atomically persist the netplan file. Returns False if unavailable."""
    if not path:
        return False
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        logger.warning("netplan directory %s missing; skipping persistence", directory)
        return False
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".viswall-", suffix=".yaml")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except OSError:
        logger.exception("failed to write netplan file %s", path)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False
    return True


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

async def apply_interfaces(config: AgentConfig, request: ApplyRequest) -> ApplyResult:
    """Plan, guard, then execute interface changes and persist them."""
    interfaces, default_iface, default_gw = await discover(config)

    planned = plan_changes(interfaces, default_iface, default_gw, request.interfaces)
    guard_plan(planned, default_iface, request.force)

    changes: list[ApplyChange] = []
    success = True
    for step in planned:
        if not step.argv:
            changes.append(
                ApplyChange(interface=step.interface, action=step.action, detail=step.detail)
            )
            continue
        rc, _out, err = await run_ip(config, *step.argv)
        ok = rc == 0
        success = success and ok
        changes.append(
            ApplyChange(
                interface=step.interface,
                action=step.action,
                detail=f"{step.detail}" + ("" if ok else f" — failed: {err}"),
                ok=ok,
            )
        )

    netplan_written = write_netplan(
        config.netplan_path, render_netplan(request.interfaces)
    )
    if not netplan_written and config.netplan_path:
        changes.append(
            ApplyChange(
                interface="*",
                action="netplan",
                detail=f"netplan file not written ({config.netplan_path} unavailable); "
                "changes are live-only",
                ok=False,
            )
        )
        success = False

    return ApplyResult(
        success=success,
        changes=changes,
        default_route_interface=default_iface,
        netplan_file=config.netplan_path,
        netplan_written=netplan_written,
        message="interface configuration applied" if success else "apply completed with errors",
    )
