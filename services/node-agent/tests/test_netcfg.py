"""Unit tests for the node agent's interface planning and persistence."""

import asyncio
import json
import uuid

import pytest
import yaml
from pydantic import ValidationError

from viswall_node_agent.config import AgentConfig, load_config
from viswall_node_agent.netcfg import (
    GuardrailContext,
    PlanRefused,
    WanGuardrailRefused,
    check_wan_guardrails,
    guard_plan,
    parse_addr_json,
    parse_default_route,
    plan_changes,
    render_netplan,
    snapshot_netplan,
    write_netplan,
)
from viswall_node_agent.payloads import (
    ApplyRequest,
    InterfaceConfig,
    LiveAddress,
    LiveInterface,
    RouteConfig,
)


def make_live(name, addresses=None, up=True, mtu=1500):
    return LiveInterface(
        name=name,
        operstate="UP" if up else "DOWN",
        up=up,
        mtu=mtu,
        mac="aa:bb:cc:dd:ee:ff",
        addresses=addresses or [],
    )


# ---------------------------------------------------------------------------
# Payload validation
# ---------------------------------------------------------------------------


def test_interface_config_rejects_loopback():
    with pytest.raises(ValidationError):
        InterfaceConfig(name="lo")


def test_interface_config_rejects_bad_netmask():
    with pytest.raises(ValidationError):
        InterfaceConfig(name="ens18", ip_address="10.0.0.5", netmask="not-a-mask")


def test_interface_config_rejects_bad_ip():
    with pytest.raises(ValidationError):
        InterfaceConfig(name="ens18", ip_address="10.0.0.999", netmask="255.255.255.0")


def test_prefixlen_from_netmask():
    cfg = InterfaceConfig(name="ens18", ip_address="10.0.0.5", netmask="255.255.255.0")
    assert cfg.prefixlen == 24


def test_apply_request_rejects_duplicate_names():
    with pytest.raises(ValidationError):
        ApplyRequest(
            interfaces=[
                InterfaceConfig(name="ens18", config_type="dhcp"),
                InterfaceConfig(name="ens18", config_type="dhcp"),
            ]
        )


# ---------------------------------------------------------------------------
# Discovery parsers
# ---------------------------------------------------------------------------


def test_parse_addr_json_extracts_ipv4_ipv6_and_up_flag():
    rows = [
        {
            "ifname": "lo",
            "flags": ["LOOPBACK", "UP"],
            "mtu": 65536,
            "operstate": "UNKNOWN",
            "addr_info": [{"family": "inet", "local": "127.0.0.1", "prefixlen": 8}],
        },
        {
            "ifname": "ens18",
            "flags": ["BROADCAST", "MULTICAST", "UP"],
            "mtu": 1500,
            "operstate": "UP",
            "address": "aa:bb:cc:dd:ee:ff",
            "addr_info": [
                {"family": "inet", "local": "10.0.0.5", "prefixlen": 24},
                {"family": "inet6", "local": "fe80::1", "prefixlen": 64},
                {"family": "inet6", "local": "2a01:4f8:140:22ef::2", "prefixlen": 64},
            ],
        },
    ]

    interfaces = parse_addr_json(rows)

    by_name = {iface.name: iface for iface in interfaces}
    assert by_name["lo"].up is True
    assert by_name["ens18"].addresses == [
        LiveAddress(address="10.0.0.5", prefixlen=24, family="inet"),
        LiveAddress(address="fe80::1", prefixlen=64, family="inet6"),
        LiveAddress(address="2a01:4f8:140:22ef::2", prefixlen=64, family="inet6"),
    ]
    assert by_name["ens18"].mtu == 1500


def test_parse_default_route():
    rows = [
        {"dst": "10.0.0.0/24", "dev": "ens18", "protocol": "kernel"},
        {"dst": "default", "gateway": "10.0.0.1", "dev": "ens18"},
    ]
    assert parse_default_route(rows) == ("ens18", "10.0.0.1")
    assert parse_default_route([{"dst": "10.0.0.0/24", "dev": "ens18"}]) == (None, None)


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def static(name="ens18", ip="10.0.0.5", gw="10.0.0.1", mtu=None, enabled=True):
    return InterfaceConfig(
        name=name,
        config_type="static",
        ip_address=ip,
        netmask="255.255.255.0",
        gateway=gw,
        mtu=mtu,
        enabled=enabled,
    )


def test_plan_is_idempotent_when_state_matches():
    live = [make_live("ens18", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    steps = plan_changes(live, "ens18", "10.0.0.1", [static()])
    assert steps == []


def test_plan_sets_address_mtu_and_link():
    live = [make_live("ens18", [], up=False, mtu=9000)]
    steps = plan_changes(live, None, None, [static(mtu=1500)])

    actions = [step.action for step in steps]
    assert actions == ["address", "mtu", "link", "gateway"]
    assert steps[0].argv == ["addr", "replace", "10.0.0.5/24", "dev", "ens18"]
    assert steps[1].argv == ["link", "set", "dev", "ens18", "mtu", "1500"]
    assert steps[2].argv == ["link", "set", "dev", "ens18", "up"]
    assert steps[3].argv == ["route", "replace", "default", "via", "10.0.0.1", "dev", "ens18"]


def test_plan_removes_stale_addresses():
    live = [
        make_live(
            "ens18",
            [
                LiveAddress(address="10.0.0.5", prefixlen=24),
                LiveAddress(address="10.0.0.99", prefixlen=24),
            ],
        )
    ]
    steps = plan_changes(live, None, None, [static()])
    stale = [step for step in steps if step.action == "stale-address"]
    assert len(stale) == 1
    assert stale[0].argv == ["addr", "del", "10.0.0.99/24", "dev", "ens18"]


def test_plan_disabled_static_drops_addresses_and_links_down():
    live = [make_live("ens18", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    steps = plan_changes(live, None, None, [static(ip="10.0.0.5", gw=None, enabled=False)])

    actions = sorted(step.action for step in steps)
    assert actions == ["link", "stale-address"]


def test_plan_dhcp_only_renders_note():
    live = [make_live("ens18", [])]
    cfg = InterfaceConfig(name="ens18", config_type="dhcp")
    steps = plan_changes(live, None, None, [cfg])
    assert [step.action for step in steps] == ["note"]


def test_plan_rejects_static_without_netmask():
    live = [make_live("ens18", [])]
    cfg = InterfaceConfig(name="ens18", config_type="static", ip_address="10.0.0.5")
    with pytest.raises(ValueError, match="netmask"):
        plan_changes(live, None, None, [cfg])


def test_plan_rejects_unknown_interface():
    with pytest.raises(ValueError, match="does not exist"):
        plan_changes([], None, None, [static(name="eth9")])


# ---------------------------------------------------------------------------
# Safety guard
# ---------------------------------------------------------------------------


def test_guard_refuses_changes_to_default_route_interface():
    live = [make_live("wan0", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    steps = plan_changes(live, "wan0", "10.0.0.1", [static(name="wan0", ip="10.0.0.6")])
    with pytest.raises(PlanRefused, match="default route"):
        guard_plan(steps, "wan0", force=False)


def test_guard_allows_with_force():
    live = [make_live("wan0", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    steps = plan_changes(live, "wan0", "10.0.0.1", [static(name="wan0", ip="10.0.0.6")])
    guard_plan(steps, "wan0", force=True)  # must not raise


def test_guard_ignores_untouched_interfaces():
    live = [make_live("wan0", [LiveAddress(address="10.0.0.5", prefixlen=24)]), make_live("lan0", [])]
    steps = plan_changes(live, "wan0", "10.0.0.1", [static(name="lan0", ip="192.168.1.1", gw=None)])
    guard_plan(steps, "wan0", force=False)  # lan0 changes are safe


# ---------------------------------------------------------------------------
# Netplan persistence
# ---------------------------------------------------------------------------


def test_render_netplan_static_with_gateway():
    yaml_text = render_netplan([static()])
    assert "network:" in yaml_text
    assert "    ens18:" in yaml_text
    assert 'addresses: ["10.0.0.5/24"]' in yaml_text
    assert "- to: default" in yaml_text
    assert "via: 10.0.0.1" in yaml_text


def test_render_netplan_dhcp_and_disabled():
    cfgs = [
        InterfaceConfig(name="ens19", config_type="dhcp"),
        static(name="ens20", ip="10.9.9.9", gw=None, enabled=False),
    ]
    yaml_text = render_netplan(cfgs)
    assert "    ens19:" in yaml_text
    assert "dhcp4: true" in yaml_text
    assert "    ens20:" in yaml_text
    assert "optional: true" in yaml_text


def test_write_netplan_atomic_and_restricted(tmp_path):
    target = tmp_path / "60-viswall.yaml"
    assert write_netplan(str(target), "network:\n") is True
    assert target.read_text() == "network:\n"
    assert (target.stat().st_mode & 0o777) == 0o600


def test_write_netplan_missing_directory_returns_false(tmp_path):
    assert write_netplan(str(tmp_path / "nope" / "60-viswall.yaml"), "x") is False


def test_write_netplan_disabled_when_path_none():
    assert write_netplan(None, "x") is False


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_load_config_defaults(monkeypatch):
    for var in (
        "INSTANCE_API_KEY",
        "GATEWAY_URL",
        "INSTANCE_ID",
        "NETPLAN_DIR",
        "AGENT_PORT",
    ):
        monkeypatch.delenv(var, raising=False)

    cfg = load_config()

    assert cfg.api_port == 8085
    assert cfg.netplan_path == "/etc/netplan/60-viswall.yaml"
    assert cfg.heartbeat_enabled is False


def test_heartbeat_enabled_with_full_env(monkeypatch):
    monkeypatch.setenv("GATEWAY_URL", "http://127.0.0.1:8010")
    monkeypatch.setenv("INSTANCE_ID", "1")
    monkeypatch.setenv("INSTANCE_API_KEY", "vis_" + uuid.uuid4().hex)

    cfg = load_config()

    assert cfg.heartbeat_enabled is True


# ---------------------------------------------------------------------------
# Payload validation: ipv6 / dns / routes
# ---------------------------------------------------------------------------


def test_interface_config_ipv6_fields_validation():
    with pytest.raises(ValidationError, match="prefix"):
        InterfaceConfig(name="ens18", ipv6_address="2a01:4f8:140:22ef::2")
    with pytest.raises(ValidationError, match="ipv6 address"):
        InterfaceConfig(name="ens18", ipv6_address="10.0.0.5/24")
    with pytest.raises(ValidationError, match="ipv6 gateway"):
        InterfaceConfig(name="ens18", ipv6_gateway="10.0.0.1")
    with pytest.raises(ValidationError, match="DNS server"):
        InterfaceConfig(name="ens18", dns_servers=["not-an-ip"])
    with pytest.raises(ValidationError, match="route destination"):
        RouteConfig(to="not-a-route")
    with pytest.raises(ValidationError):
        RouteConfig(to="10.80.0.0/16", via="nope")


def test_route_config_accepts_default_and_cidr():
    assert RouteConfig(to="default").to == "default"
    assert RouteConfig(to="::/0").to == "::/0"
    assert RouteConfig(to="10.80.0.0/16", via="46.4.63.193", on_link=True).on_link is True


# ---------------------------------------------------------------------------
# Netplan render: ipv6 / dns / routes
# ---------------------------------------------------------------------------


def test_render_netplan_ipv6_dns_and_extra_routes():
    cfg = InterfaceConfig(
        name="enp0s31f6",
        config_type="static",
        ip_address="46.4.63.216",
        netmask="255.255.255.255",
        gateway="46.4.63.193",
        ipv6_address="2a01:4f8:140:22ef::2/64",
        ipv6_gateway="fe80::1",
        dns_servers=["185.12.64.1", "2a01:4ff:ff00::add:2"],
        routes=[
            RouteConfig(to="10.80.0.0/16", via="46.4.63.193"),
            RouteConfig(to="192.168.0.0/24", on_link=True),
        ],
    )
    yaml_text = render_netplan([cfg])

    assert 'addresses: ["46.4.63.216/32", "2a01:4f8:140:22ef::2/64"]' in yaml_text
    assert "- to: default" in yaml_text
    assert "via: 46.4.63.193" in yaml_text
    assert '- to: "::/0"' in yaml_text
    assert "via: fe80::1" in yaml_text
    assert "- to: 10.80.0.0/16" in yaml_text
    assert "via: 46.4.63.193" in yaml_text
    assert "- to: 192.168.0.0/24" in yaml_text
    assert "on-link: true" in yaml_text
    assert 'nameservers: {addresses: ["185.12.64.1", "2a01:4ff:ff00::add:2"]}' in yaml_text


def test_render_netplan_empty_ipv6_dns_routes_is_valid_yaml():
    yaml_text = render_netplan([static()])
    parsed = yaml.safe_load(yaml_text)

    ethernets = parsed["network"]["ethernets"]
    assert ethernets["ens18"]["addresses"] == ["10.0.0.5/24"]
    assert ethernets["ens18"]["routes"] == [{"to": "default", "via": "10.0.0.1"}]
    assert "nameservers" not in ethernets["ens18"]
    assert "dhcp4" in ethernets["ens18"]


def test_render_netplan_ipv6_only_static_is_valid_yaml():
    cfg = InterfaceConfig(
        name="ens19",
        config_type="static",
        ipv6_address="fd00:42::2/64",
        ipv6_gateway="fe80::1",
        dns_servers=["2a01:4ff:ff00::add:2"],
    )
    parsed = yaml.safe_load(render_netplan([cfg]))

    ethernets = parsed["network"]["ethernets"]["ens19"]
    assert ethernets["addresses"] == ["fd00:42::2/64"]
    assert ethernets["routes"] == [{"to": "::/0", "via": "fe80::1"}]
    assert ethernets["nameservers"] == {"addresses": ["2a01:4ff:ff00::add:2"]}


# ---------------------------------------------------------------------------
# Hard WAN guardrails (live state)
# ---------------------------------------------------------------------------


def make_guardrail_ctx(steps, desired, link_rows=None, netplan_dir="",
                       old_content=None, new_render=""):
    return GuardrailContext(
        steps=steps,
        desired=desired,
        link_rows=link_rows or [],
        netplan_dir=netplan_dir,
        old_content=old_content,
        new_render=new_render,
        wan_ip="46.4.63.216/32",
    )


def wan_static(ip="46.4.63.216", gw="46.4.63.193"):
    return InterfaceConfig(
        name="wan0",
        config_type="static",
        ip_address=ip,
        netmask="255.255.255.255",
        gateway=gw,
    )


def test_guardrail_refuses_wan_address_removal():
    live = [make_live("wan0", [LiveAddress(address="46.4.63.216", prefixlen=32)])]
    desired = [wan_static(ip="10.9.9.9", gw=None)]
    steps = plan_changes(live, "wan0", "46.4.63.193", desired)

    with pytest.raises(WanGuardrailRefused, match="46.4.63.216"):
        check_wan_guardrails(make_guardrail_ctx(steps, desired))


def test_guardrail_refuses_default_route_removal():
    live = [make_live("wan0", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    desired = [
        InterfaceConfig(
            name="wan0", config_type="static", ip_address="10.0.0.5",
            netmask="255.255.255.0", gateway=None,
        )
    ]
    steps = plan_changes(live, "wan0", "10.0.0.1", desired)

    with pytest.raises(WanGuardrailRefused, match="default route"):
        check_wan_guardrails(make_guardrail_ctx(steps, desired))


def test_guardrail_refuses_docker_bridge_member():
    live = [make_live("eth0", [], mtu=1500)]
    desired = [InterfaceConfig(name="eth0", config_type="dhcp", mtu=9000)]
    steps = plan_changes(live, None, None, desired)

    for master in ("docker0", "br-abc123def456"):
        ctx = make_guardrail_ctx(steps, desired, link_rows=[{"ifname": "eth0", "master": master}])
        with pytest.raises(WanGuardrailRefused, match="bridge"):
            check_wan_guardrails(ctx)


def test_guardrail_refuses_interface_absent_from_netplan(tmp_path):
    netplan_dir = tmp_path / "netplan"
    netplan_dir.mkdir()
    (netplan_dir / "01-netcfg.yaml").write_text(
        "network:\n  version: 2\n  ethernets:\n    enp0s31f6:\n      dhcp4: true\n"
    )

    missing = [InterfaceConfig(name="ens18", config_type="dhcp")]
    ctx = make_guardrail_ctx([], missing, netplan_dir=str(netplan_dir))
    with pytest.raises(WanGuardrailRefused, match="absent from the host netplan"):
        check_wan_guardrails(ctx)

    present = [InterfaceConfig(name="enp0s31f6", config_type="dhcp")]
    check_wan_guardrails(make_guardrail_ctx([], present, netplan_dir=str(netplan_dir)))


def test_guardrail_refuses_persisted_wan_and_default_route_drop():
    old_with_wan = (
        "network:\n  version: 2\n  ethernets:\n"
        '    enp0s31f6:\n      addresses: ["46.4.63.216/32"]\n'
        "      routes:\n        - to: default\n          via: 46.4.63.193\n"
    )
    empty_render = "network:\n  version: 2\n  ethernets: {}\n"

    ctx = make_guardrail_ctx([], [], old_content=old_with_wan, new_render=empty_render)
    with pytest.raises(WanGuardrailRefused, match="WAN address"):
        check_wan_guardrails(ctx)

    old_route_only = (
        "network:\n  version: 2\n  ethernets:\n"
        "    enp0s31f6:\n      routes:\n        - to: default\n          via: 46.4.63.193\n"
    )
    ctx = make_guardrail_ctx([], [], old_content=old_route_only, new_render=empty_render)
    with pytest.raises(WanGuardrailRefused, match="default route"):
        check_wan_guardrails(ctx)


def test_guardrail_allows_safe_plan():
    live = [make_live("ens18", [LiveAddress(address="10.0.0.5", prefixlen=24)])]
    desired = [static()]
    steps = plan_changes(live, "ens18", "10.0.0.1", desired)
    ctx = make_guardrail_ctx(
        steps, desired,
        link_rows=[{"ifname": "ens18"}],
        netplan_dir="",
    )
    check_wan_guardrails(ctx)  # must not raise


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


def test_snapshot_netplan_captures_and_prunes_to_ten(tmp_path, monkeypatch):
    import viswall_node_agent.netcfg as netcfg_module

    netplan_dir = tmp_path / "netplan"
    netplan_dir.mkdir()
    (netplan_dir / "01-netcfg.yaml").write_text("network:\n  version: 2\n")

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cfg = make_config(state_dir=str(state_dir), netplan_dir=str(netplan_dir))

    stamps = iter(f"20260101-000000-{i:06d}" for i in range(12))
    monkeypatch.setattr(netcfg_module, "_utc_stamp", lambda: next(stamps))

    for _ in range(12):
        assert snapshot_netplan(cfg) is not None

    snaps = state_dir / "snapshots"
    remaining = sorted(p.name for p in snaps.iterdir() if p.is_dir())
    assert len(remaining) == 10
    assert remaining[0] == "20260101-000000-000002"
    latest = snaps / remaining[-1] / "netplan" / "01-netcfg.yaml"
    assert latest.read_text() == "network:\n  version: 2\n"


def test_snapshot_netplan_skips_when_disabled(tmp_path):
    cfg = make_config(netplan_dir="", state_dir=str(tmp_path / "state"))
    assert snapshot_netplan(cfg) is None


# ---------------------------------------------------------------------------
# Try-mode apply (mocked subprocesses)
# ---------------------------------------------------------------------------


def make_config(**overrides) -> AgentConfig:
    defaults = {
        "instance_api_key": None,
        "gateway_url": None,
        "instance_id": None,
        "heartbeat_interval": 30.0,
        "api_host": "0.0.0.0",
        "api_port": 8085,
        "host_root": "/host",
        "netplan_dir": "",
        "netplan_file": "60-viswall.yaml",
        "ip_binary": "ip",
        "state_dir": "/tmp/viswall-node-test",
        "nsenter_binary": "nsenter",
        "netplan_binary": "netplan",
        "dbus_system_bus_address": "/run/dbus/system_bus_socket",
        "netplan_try_timeout": 120,
        "try_settle_seconds": 0.0,
        "probe_ssh_port": 22,
        "probe_gateway_url": "http://127.0.0.1:8010/health",
        "probe_ping_target": "46.4.63.193",
        "curl_binary": "curl",
        "ping_binary": "ping",
        "ss_binary": "ss",
        "wan_ip": "46.4.63.216/32",
    }
    defaults.update(overrides)
    return AgentConfig(**defaults)


class FakeStdin:
    def __init__(self, events):
        self.writes: list[bytes] = []
        self.closed = False
        self._events = events

    def write(self, data):
        self.writes.append(data)
        self._events.append("stdin-write")

    async def drain(self):
        return None

    def close(self):
        self.closed = True
        self._events.append("stdin-close")


class FakeProc:
    def __init__(self, events):
        self.stdin = FakeStdin(events)
        self.returncode = 0

    async def communicate(self):
        return b"", b""

    def kill(self):
        pass

    async def wait(self):
        return None


def _write_ens18_netplan_dir(tmp_path):
    netplan_dir = tmp_path / "netplan"
    netplan_dir.mkdir()
    (netplan_dir / "01-netcfg.yaml").write_text(
        "network:\n  version: 2\n  ethernets:\n    ens18:\n      dhcp4: true\n"
    )
    (netplan_dir / "60-viswall.yaml").write_text("network:\n  version: 2\n  ethernets: {}\n")
    return netplan_dir


def _patch_try_env(monkeypatch, events, probes_ok=True):
    """Patch run_ip/run_command/create_subprocess_exec; return (fake_proc, captured)."""
    import viswall_node_agent.netcfg as netcfg_module

    fake_proc = FakeProc(events)
    captured = {}

    async def fake_create_subprocess_exec(*argv, **kwargs):
        captured["argv"] = list(argv)
        captured["kwargs"] = kwargs
        return fake_proc

    monkeypatch.setattr(
        netcfg_module.asyncio, "create_subprocess_exec", fake_create_subprocess_exec
    )

    async def fake_run_ip(config, *args):
        if "addr" in args:
            return 0, json.dumps([{
                "ifname": "ens18",
                "flags": ["BROADCAST", "MULTICAST", "UP"],
                "mtu": 1500,
                "operstate": "UP",
                "address": "aa:bb:cc:dd:ee:ff",
                "addr_info": [
                    {"family": "inet", "local": "192.168.1.10", "prefixlen": 24},
                    {"family": "inet6", "local": "fe80::1", "prefixlen": 64},
                ],
            }]), ""
        if "route" in args:
            return 0, json.dumps(
                [{"dst": "default", "gateway": "192.168.1.1", "dev": "ens18"}]
            ), ""
        if "link" in args:
            return 0, json.dumps([{"ifname": "ens18"}]), ""
        raise AssertionError(f"unexpected ip args: {args}")

    monkeypatch.setattr(netcfg_module, "run_ip", fake_run_ip)

    async def fake_run_command(binary, *args, timeout=None):
        events.append(binary)
        if binary == "ss":
            return 0, "LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n", ""
        if binary == "curl":
            return (0, "", "") if probes_ok else (7, "", "Failed to connect to host")
        if binary == "ping":
            return 0, "", ""
        raise AssertionError(f"unexpected binary: {binary}")

    monkeypatch.setattr(netcfg_module, "run_command", fake_run_command)

    return fake_proc, captured


def _try_request():
    return ApplyRequest(
        interfaces=[
            InterfaceConfig(
                name="ens18",
                config_type="static",
                ip_address="192.168.1.10",
                netmask="255.255.255.0",
                gateway="192.168.1.1",
            )
        ],
        try_mode=True,
    )


def test_try_mode_writes_newline_only_after_all_probes_pass(tmp_path, monkeypatch):
    import viswall_node_agent.netcfg as netcfg_module

    netplan_dir = _write_ens18_netplan_dir(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cfg = make_config(netplan_dir=str(netplan_dir), state_dir=str(state_dir))

    events: list[str] = []
    fake_proc, captured = _patch_try_env(monkeypatch, events, probes_ok=True)

    result = asyncio.run(netcfg_module.apply_interfaces(cfg, _try_request()))

    assert result.try_mode is True
    assert result.netplan_outcome == "accepted"
    assert result.success is True
    assert [p.ok for p in result.probes] == [True, True, True]
    assert result.snapshot_dir is not None
    assert (state_dir / "snapshots").exists()
    assert events == ["ss", "curl", "ping", "stdin-write", "stdin-close"]
    assert fake_proc.stdin.writes == [b"\n"]

    argv = captured["argv"]
    assert argv[:7] == ["nsenter", "-t", "1", "-m", "-u", "-i", "-n"]
    assert argv[7:9] == ["--", "env"]
    assert argv[9].startswith("DBUS_SYSTEM_BUS_ADDRESS=")
    assert argv[10:14] == ["netplan", "try", "--timeout", "120"]

    backups = [p for p in (state_dir / "backups").iterdir()] if (state_dir / "backups").exists() else []
    assert len(backups) == 1
    assert (backups[0] / "60-viswall.yaml").read_text().startswith("network:")
    # F2 MAJOR #8: nothing backup-shaped may land inside the netplan dir.
    assert [p for p in netplan_dir.iterdir() if p.name.startswith("backup-")] == []
    assert (netplan_dir / "60-viswall.yaml").read_text() == render_netplan(
        _try_request().interfaces
    )


def test_try_mode_closes_stdin_without_newline_when_probe_fails(tmp_path, monkeypatch):
    import viswall_node_agent.netcfg as netcfg_module

    netplan_dir = _write_ens18_netplan_dir(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cfg = make_config(netplan_dir=str(netplan_dir), state_dir=str(state_dir))

    events: list[str] = []
    fake_proc, _captured = _patch_try_env(monkeypatch, events, probes_ok=False)

    result = asyncio.run(netcfg_module.apply_interfaces(cfg, _try_request()))

    assert result.try_mode is True
    assert result.netplan_outcome == "reverted"
    assert result.success is False
    assert [p.ok for p in result.probes] == [True, False, True]
    assert events == ["ss", "curl", "ping", "stdin-close"]
    assert fake_proc.stdin.writes == []
    assert fake_proc.stdin.closed is True
    assert "Failed to connect to host" in result.message


def test_hard_guardrail_not_bypassed_by_force(tmp_path, monkeypatch):
    import viswall_node_agent.netcfg as netcfg_module

    netplan_dir = _write_ens18_netplan_dir(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cfg = make_config(netplan_dir=str(netplan_dir), state_dir=str(state_dir))

    events: list[str] = []
    _fake_proc, _captured = _patch_try_env(monkeypatch, events, probes_ok=True)

    async def fake_run_ip(config, *args):
        if "addr" in args:
            return 0, json.dumps([{
                "ifname": "ens18",
                "flags": ["BROADCAST", "MULTICAST", "UP"],
                "mtu": 1500,
                "operstate": "UP",
                "addr_info": [
                    {"family": "inet", "local": "46.4.63.216", "prefixlen": 32},
                    {"family": "inet", "local": "10.0.0.99", "prefixlen": 24},
                ],
            }]), ""
        if "route" in args:
            return 0, json.dumps(
                [{"dst": "default", "gateway": "46.4.63.193", "dev": "ens18"}]
            ), ""
        if "link" in args:
            return 0, json.dumps([{"ifname": "ens18"}]), ""
        raise AssertionError(f"unexpected ip args: {args}")

    monkeypatch.setattr(netcfg_module, "run_ip", fake_run_ip)

    request = ApplyRequest(
        interfaces=[
            InterfaceConfig(
                name="ens18",
                config_type="static",
                ip_address="10.9.9.9",
                netmask="255.255.255.0",
                gateway=None,
            )
        ],
        force=True,  # bypasses the soft guard only
        try_mode=True,
    )

    with pytest.raises(WanGuardrailRefused, match="46.4.63.216"):
        asyncio.run(netcfg_module.apply_interfaces(cfg, request))

    request_live = request.model_copy(update={"try_mode": False})
    with pytest.raises(WanGuardrailRefused, match="46.4.63.216"):
        asyncio.run(netcfg_module.apply_interfaces(cfg, request_live))


# ---------------------------------------------------------------------------
# API-level error mapping
# ---------------------------------------------------------------------------


def test_api_apply_maps_guardrail_to_400_and_soft_guard_to_409(monkeypatch):
    from fastapi.testclient import TestClient

    import viswall_node_agent.api as api_module

    cfg = make_config(instance_api_key="test-key", netplan_dir="")
    monkeypatch.setattr(api_module, "config", cfg)

    async def fake_apply(config, request):
        raise WanGuardrailRefused("plan removes WAN address 46.4.63.216/32")

    monkeypatch.setattr(api_module, "apply_interfaces", fake_apply)

    client = TestClient(api_module.app)
    response = client.post(
        "/interfaces/apply",
        json={"interfaces": [], "try_mode": True},
        headers={"X-Instance-Key": "test-key"},
    )
    assert response.status_code == 400
    assert "46.4.63.216" in response.json()["detail"]

    async def fake_soft_guard(config, request):
        raise PlanRefused("default route touched")

    monkeypatch.setattr(api_module, "apply_interfaces", fake_soft_guard)
    response = client.post(
        "/interfaces/apply",
        json={"interfaces": []},
        headers={"X-Instance-Key": "test-key"},
    )
    assert response.status_code == 409
