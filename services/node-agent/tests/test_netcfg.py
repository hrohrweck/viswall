"""Unit tests for the node agent's interface planning and persistence."""

import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from viswall_node_agent.config import AgentConfig, load_config
from viswall_node_agent.netcfg import (
    PlanRefused,
    guard_plan,
    parse_addr_json,
    parse_default_route,
    plan_changes,
    render_netplan,
    write_netplan,
)
from viswall_node_agent.payloads import (
    ApplyRequest,
    InterfaceConfig,
    LiveAddress,
    LiveInterface,
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


def test_parse_addr_json_extracts_ipv4_and_up_flag():
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
            ],
        },
    ]

    interfaces = parse_addr_json(rows)

    by_name = {iface.name: iface for iface in interfaces}
    assert by_name["lo"].up is True
    assert by_name["ens18"].addresses == [LiveAddress(address="10.0.0.5", prefixlen=24)]
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
