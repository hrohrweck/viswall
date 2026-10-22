"""Host interface management: discovery, guarded live apply, netplan persistence.

The agent container shares the host network namespace with NET_ADMIN,
so `ip` invocations here reconfigure the host's real interfaces.
Desired state is additionally rendered into a netplan file so it
survives reboots.

Safety model, in two layers:

1. Soft guard (``guard_plan``): a plan that touches the interface carrying
   the default route — typically the management connection — or the default
   route itself is refused unless the caller explicitly sets force=True.
2. Hard WAN guardrails (``check_wan_guardrails``): keyed on LIVE host state
   read at apply time. Refuse any plan that removes the WAN address
   (default 46.4.63.216/32), removes the 0.0.0.0/0 default route, edits an
   interface enslaved to a docker bridge (docker0/br-*), or targets an
   interface absent from the host netplan files. ``force`` cannot bypass
   these. Applies to both live and try-mode applies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from viswall_node_agent.config import AgentConfig
from viswall_node_agent.payloads import (
    IFACE_NAME_PATTERN,
    ApplyChange,
    ApplyRequest,
    ApplyResult,
    InterfaceConfig,
    LiveAddress,
    LiveInterface,
    ProbeResult,
)

logger = logging.getLogger(__name__)

IP_TIMEOUT_SECONDS = 10.0
PROBE_TIMEOUT_SECONDS = 10.0
NETPLAN_TRY_EXTRA_WAIT_SECONDS = 60.0

KEEP_SNAPSHOTS = 10
DOCKER_BRIDGE_MASTERS = ("docker0",)
BRIDGE_MASTER_PREFIX = "br-"
CONFIRM_NEWLINE = b"\n"


class PlanRefused(Exception):
    """A planned change would likely cut management connectivity."""


class WanGuardrailRefused(ValueError):
    """A plan trips a hard WAN safety guardrail; force cannot bypass it."""


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

async def run_command(
    binary: str,
    *args: str,
    timeout: float = IP_TIMEOUT_SECONDS,
) -> tuple[int, str, str]:
    """Run ``<binary> <args>`` and return (returncode, stdout, stderr)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            binary,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        return 127, "", str(exc)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "", "timeout"
    return (
        proc.returncode or 0,
        stdout.decode(errors="replace").strip(),
        stderr.decode(errors="replace").strip(),
    )


async def run_ip(config: AgentConfig, *args: str) -> tuple[int, str, str]:
    """Run `ip <args>` and return (returncode, stdout, stderr)."""
    return await run_command(config.ip_binary, *args)


def parse_addr_json(rows: list[dict[str, Any]]) -> list[LiveInterface]:
    """Parse `ip -j addr show` output into LiveInterface models (v4 and v6)."""
    interfaces: list[LiveInterface] = []
    for row in rows:
        name = row.get("ifname")
        if not name:
            continue
        addresses = [
            LiveAddress(
                address=info["local"],
                prefixlen=info["prefixlen"],
                family=info.get("family", "inet"),
            )
            for info in row.get("addr_info", [])
            if info.get("family") in ("inet", "inet6") and info.get("local")
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


def link_master(link_rows: list[dict[str, Any]], ifname: str) -> str | None:
    """Return the master interface of ``ifname`` per `ip -j link` output."""
    for row in link_rows:
        if row.get("ifname") == ifname:
            return row.get("master")
    return None


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

    interfaces = parse_addr_json(json.loads(addr_out or "[]"))
    default_iface, default_gw = parse_default_route(json.loads(route_out or "[]"))
    for iface in interfaces:
        iface.has_default_route = iface.name == default_iface
    return interfaces, default_iface, default_gw


async def read_link_rows(config: AgentConfig) -> list[dict[str, Any]]:
    """Live `ip -j link` rows (interface master relationships)."""
    rc, out, err = await run_ip(config, "-j", "link", "show")
    if rc != 0:
        raise RuntimeError(f"ip link show failed: {err}")
    return json.loads(out or "[]")


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
        # Live apply diffs IPv4 only; IPv6 desired state is rendered into the
        # netplan file and takes effect there (netplan apply / reboot).
        current_addrs = {(a.address, a.prefixlen) for a in current.addresses if a.family == "inet"}
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
# Hard WAN guardrails (live state, both apply modes)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GuardrailContext:
    steps: list[PlannedStep]
    desired: list[InterfaceConfig]
    link_rows: list[dict[str, Any]]
    netplan_dir: str
    old_content: str | None
    new_render: str | None
    wan_ip: str


def _netplan_interface_names(directory: str) -> set[str]:
    """Interface names configured across all *.yaml files in a netplan dir.

    Interface keys sit at exactly 4-space indentation under the
    ethernets/bonds/bridges/vlans/wifis sections; section keys and option
    keys are indented 2 and 6+ spaces respectively. No YAML parser is
    required, which keeps the agent image free of a PyYAML dependency.
    """
    names: set[str] = set()
    if not directory:
        return names
    netplan_dir = Path(directory)
    if not netplan_dir.is_dir():
        return names
    for path in netplan_dir.iterdir():
        if path.suffix not in (".yaml", ".yml"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in content.splitlines():
            if not (line.startswith("    ") and not line.startswith("     ")):
                continue
            stripped = line.strip()
            if not stripped.endswith(":"):
                continue
            candidate = stripped[:-1]
            if IFACE_NAME_PATTERN.match(candidate):
                names.add(candidate)
    return names


def _has_default_route(content: str) -> bool:
    return any(
        token in content
        for token in ("to: default", "to: 0.0.0.0/0", 'to: "0.0.0.0/0"')
    )


def check_wan_guardrails(ctx: GuardrailContext) -> None:
    """Refuse plans that would damage WAN connectivity or docker plumbing.

    Guardrails 1-4 are keyed on the live host state read at apply time and
    apply to both live and try-mode applies. ``force`` cannot bypass them.
    """
    wan_bare = ctx.wan_ip.split("/", 1)[0]

    for step in ctx.steps:
        if step.action == "stale-address" and len(step.argv) >= 3:
            removed = step.argv[2]
            if removed in (ctx.wan_ip, wan_bare):
                raise WanGuardrailRefused(
                    f"plan removes WAN address {removed}; {ctx.wan_ip} is "
                    "excluded from automation (guardrail 1)"
                )
        if step.action == "gateway" and "remove default route" in step.detail:
            raise WanGuardrailRefused(
                "plan removes the 0.0.0.0/0 default route; WAN reachability "
                "is excluded from automation (guardrail 2)"
            )
        master = link_master(ctx.link_rows, step.interface)
        if master and (master in DOCKER_BRIDGE_MASTERS or master.startswith(BRIDGE_MASTER_PREFIX)):
            raise WanGuardrailRefused(
                f"interface {step.interface} is enslaved to bridge {master}; "
                "docker networking is excluded from automation (guardrail 3)"
            )

    known = _netplan_interface_names(ctx.netplan_dir)
    if known:
        for cfg in ctx.desired:
            if cfg.name not in known:
                raise WanGuardrailRefused(
                    f"interface {cfg.name} is absent from the host netplan "
                    "files; add a base netplan entry before automating it "
                    "(guardrail 4)"
                )

    if ctx.old_content and ctx.new_render is not None:
        if wan_bare in ctx.old_content and wan_bare not in ctx.new_render:
            raise WanGuardrailRefused(
                "the persisted netplan config carries the WAN address but "
                "the new render drops it (guardrail 1)"
            )
        if _has_default_route(ctx.old_content) and not _has_default_route(ctx.new_render):
            raise WanGuardrailRefused(
                "the persisted netplan config carries the default route but "
                "the new render drops it (guardrail 2)"
            )


# ---------------------------------------------------------------------------
# Netplan persistence
# ---------------------------------------------------------------------------

def _yaml_scalar(value: str) -> str:
    """Quote netplan scalar values the YAML plain style cannot express."""
    return f'"{value}"' if ":" in value else value


def _route_lines(to: str, via: str | None, on_link: bool) -> list[str]:
    lines = [f"- to: {_yaml_scalar(to)}"]
    if via:
        lines.append(f"  via: {via}")
    if on_link:
        lines.append("  on-link: true")
    return lines


def render_netplan(interfaces: list[InterfaceConfig]) -> str:
    """Render managed interfaces as a netplan ethernets config."""
    lines = ["network:", "  version: 2", "  ethernets:"]
    for cfg in sorted(interfaces, key=lambda c: c.name):
        lines.append(f"    {cfg.name}:")
        dhcp = cfg.enabled and cfg.config_type == "dhcp"
        managed_static = cfg.enabled and cfg.config_type == "static" and (
            cfg.ip_address or cfg.ipv6_address
        )
        lines.append(f"      dhcp4: {'true' if dhcp else 'false'}")
        addresses: list[str] = []
        if managed_static:
            if cfg.ip_address and cfg.prefixlen is not None:
                addresses.append(f"{cfg.ip_address}/{cfg.prefixlen}")
            if cfg.ipv6_address:
                addresses.append(cfg.ipv6_address)
        if addresses:
            quoted = ", ".join(f'"{address}"' for address in addresses)
            lines.append(f"      addresses: [{quoted}]")
        route_entries: list[str] = []
        if managed_static:
            if cfg.gateway:
                route_entries.extend(_route_lines("default", cfg.gateway, False))
            if cfg.ipv6_gateway:
                route_entries.extend(_route_lines("::/0", cfg.ipv6_gateway, False))
        for route in cfg.routes:
            route_entries.extend(_route_lines(route.to, route.via, route.on_link))
        if route_entries:
            lines.append("      routes:")
            lines.extend(f"        {entry}" for entry in route_entries)
        if cfg.dns_servers:
            quoted = ", ".join(f'"{server}"' for server in cfg.dns_servers)
            lines.append(f"      nameservers: {{addresses: [{quoted}]}}")
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


def read_existing_netplan(config: AgentConfig) -> str | None:
    """Current content of the managed netplan file, or None if absent."""
    path = config.netplan_path
    if not path or not os.path.isfile(path):
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        logger.warning("cannot read existing netplan file %s", path)
        return None


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

def _utc_stamp() -> str:
    """UTC timestamp that sorts lexicographically (``%Y%m%d-%H%M%S-%f``)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _prune_snapshots(snapshots_root: Path, keep: int) -> None:
    entries = sorted(
        (p for p in snapshots_root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    for stale in entries[:-keep] if keep > 0 else entries:
        shutil.rmtree(stale, ignore_errors=True)
        logger.info("pruned old snapshot %s", stale)


def snapshot_netplan(config: AgentConfig) -> str | None:
    """Copy the host netplan dir to $STATE_DIR/snapshots/<ts>; keep 10.

    Returns the snapshot directory, or None when netplan persistence is
    disabled or the source directory is unavailable.
    """
    if not config.netplan_dir:
        logger.info("netplan persistence disabled; skipping pre-apply snapshot")
        return None
    source = Path(config.netplan_dir)
    if not source.is_dir():
        logger.warning("netplan dir %s missing; skipping pre-apply snapshot", source)
        return None
    target = Path(config.state_dir) / "snapshots" / _utc_stamp()
    target.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, target / "netplan")
    _prune_snapshots(target.parent, KEEP_SNAPSHOTS)
    logger.info("netplan snapshot captured: %s", target)
    return str(target)


# ---------------------------------------------------------------------------
# Try-mode apply (netplan try + health probes + confirm/revert)
# ---------------------------------------------------------------------------

async def probe_ssh_listener(config: AgentConfig) -> ProbeResult:
    name = f"ssh-listener:{config.probe_ssh_port}"
    rc, out, err = await run_command(
        config.ss_binary, "-ltn", timeout=PROBE_TIMEOUT_SECONDS
    )
    if rc != 0:
        return ProbeResult(name=name, ok=False, detail=f"ss exited {rc}: {err[:200]}")
    listening = re.search(rf":{config.probe_ssh_port}[ \t\r\n]", out) is not None
    return ProbeResult(
        name=name,
        ok=listening,
        detail="listener found" if listening else f"no listener on port {config.probe_ssh_port}",
    )


async def probe_gateway_health(config: AgentConfig) -> ProbeResult:
    name = "gateway-health"
    rc, _out, err = await run_command(
        config.curl_binary,
        "-fsS",
        "-m",
        "5",
        config.probe_gateway_url,
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    return ProbeResult(
        name=name,
        ok=rc == 0,
        detail="ok" if rc == 0 else (err[:200] or f"curl exited {rc}"),
    )


async def probe_ping_wan(config: AgentConfig) -> ProbeResult:
    name = f"ping-wan:{config.probe_ping_target}"
    rc, _out, err = await run_command(
        config.ping_binary,
        "-c1",
        "-W2",
        config.probe_ping_target,
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    return ProbeResult(
        name=name,
        ok=rc == 0,
        detail="ok" if rc == 0 else (err[:200] or f"ping exited {rc}"),
    )


async def run_health_probes(config: AgentConfig) -> list[ProbeResult]:
    """Run the pre-confirm probes sequentially; never raises."""
    results: list[ProbeResult] = []
    for coro in (probe_ssh_listener, probe_gateway_health, probe_ping_wan):
        try:
            results.append(await coro(config))
        except Exception as exc:  # noqa: BLE001 — see docstring: a probe crash reverts, never aborts
            results.append(ProbeResult(name="probe", ok=False, detail=str(exc)))
    return results


@dataclass(frozen=True, slots=True)
class TryApplyContext:
    rendered: str
    snapshot_dir: str | None
    default_iface: str | None


async def apply_try_mode(
    config: AgentConfig,
    ctx: TryApplyContext,
) -> ApplyResult:
    """Render → `netplan try` → probe → confirm ("\\n") or auto-revert.

    The new netplan file is written inside the container (bind-mounted host
    dir); `netplan try` runs inside the host's namespaces via nsenter with
    stdin held open. Only when ALL health probes pass is a newline written
    (accept); otherwise stdin is closed and netplan auto-reverts.
    """
    path = config.netplan_path
    if not path:
        raise ValueError("try mode requires netplan persistence (NETPLAN_DIR unset)")

    changes: list[ApplyChange] = []
    stamp = _utc_stamp()

    if os.path.exists(path):
        backup_dir = os.path.join(config.netplan_dir, f"backup-{stamp}")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, config.netplan_file)
        shutil.copyfile(path, backup_path)
        os.chmod(backup_path, 0o600)
        changes.append(
            ApplyChange(
                interface="*",
                action="netplan",
                detail=f"previous file backed up to {backup_path}",
            )
        )

    if not write_netplan(path, ctx.rendered):
        raise ValueError(f"cannot write netplan file {path}; aborting try mode")

    argv = [
        config.nsenter_binary, "-t", "1", "-m", "-u", "-i", "-n", "--",
        "env", f"DBUS_SYSTEM_BUS_ADDRESS={config.dbus_system_bus_address}",
        config.netplan_binary, "try", "--timeout", str(config.netplan_try_timeout),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        raise ValueError(f"cannot spawn netplan try: {exc}") from exc

    if config.try_settle_seconds > 0:
        await asyncio.sleep(config.try_settle_seconds)

    probes = await run_health_probes(config)
    all_ok = all(probe.ok for probe in probes)

    if proc.stdin is None:
        confirm = "error"
    elif all_ok:
        try:
            proc.stdin.write(CONFIRM_NEWLINE)
            await proc.stdin.drain()
            confirm = "accepted"
        except (BrokenPipeError, ConnectionResetError):
            confirm = "error"
        finally:
            proc.stdin.close()
    else:
        proc.stdin.close()
        confirm = "reverted"

    try:
        _stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=config.netplan_try_timeout + NETPLAN_TRY_EXTRA_WAIT_SECONDS,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        stderr = b"netplan try did not finish; killed"

    rc = proc.returncode or 0
    if confirm == "accepted" and rc != 0:
        confirm = "error"
    netplan_outcome = confirm

    changes.append(
        ApplyChange(
            interface="*",
            action="netplan",
            detail=f"netplan try exited {rc}: {netplan_outcome}" + (
                f" — {stderr.decode(errors='replace').strip()[:300]}" if stderr else ""
            ),
            ok=netplan_outcome == "accepted",
        )
    )

    success = netplan_outcome == "accepted"
    if not success:
        failed = [p for p in probes if not p.ok]
        first_failure = failed[0].detail if failed else "netplan try errored"
        message = f"netplan try {netplan_outcome}; first failing probe: {first_failure}"
    else:
        message = "netplan try accepted and committed"

    return ApplyResult(
        success=success,
        changes=changes,
        default_route_interface=ctx.default_iface,
        netplan_file=path,
        netplan_written=True,
        message=message,
        try_mode=True,
        probes=probes,
        netplan_outcome=netplan_outcome,
        snapshot_dir=ctx.snapshot_dir,
    )


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

async def apply_interfaces(config: AgentConfig, request: ApplyRequest) -> ApplyResult:
    """Plan, guard (soft + hard WAN guardrails), snapshot, then apply."""
    interfaces, default_iface, default_gw = await discover(config)
    link_rows = await read_link_rows(config)

    planned = plan_changes(interfaces, default_iface, default_gw, request.interfaces)
    guard_plan(planned, default_iface, request.force)

    rendered = render_netplan(request.interfaces)
    check_wan_guardrails(
        GuardrailContext(
            steps=planned,
            desired=request.interfaces,
            link_rows=link_rows,
            netplan_dir=config.netplan_dir,
            old_content=read_existing_netplan(config),
            new_render=rendered,
            wan_ip=config.wan_ip,
        )
    )

    snapshot_dir = snapshot_netplan(config)

    if request.try_mode:
        return await apply_try_mode(
            config,
            TryApplyContext(
                rendered=rendered,
                snapshot_dir=snapshot_dir,
                default_iface=default_iface,
            ),
        )

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

    netplan_written = write_netplan(config.netplan_path, rendered)
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
        snapshot_dir=snapshot_dir,
    )
