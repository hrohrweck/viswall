"""WireGuard client manager tests: renderer semantics, atomic write with
backup + 0600, apply rollback ordering, unit steering, takeover gate, and
the ``wg show`` / ``ip -j`` status parser fixtures."""

from __future__ import annotations

import base64
import json
import secrets
from pathlib import Path

import pytest

from viswall_vpn_agent.wg_client import (
    WgApplyError,
    WgClientConfig,
    WgClientManager,
    WgConfigValidationError,
    WgUnitError,
    _parse_handshake_sec,
    _parse_size,
    _parse_wg_show,
    render_config,
)


def _b64_key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


def _model(**overrides: object) -> WgClientConfig:
    base: dict[str, object] = dict(
        address="10.80.0.2/32",
        endpoint="46.4.63.216:51820",
        peer_public_key=_b64_key(),
        allowed_ips="10.80.0.0/16",
        private_key=_b64_key(),
        dns="1.1.1.1",
        persistent_keepalive=25,
    )
    return WgClientConfig(**{**base, **overrides})


def _key_values(text: str) -> dict[str, str]:
    """Parse active (non-comment) ``Key = Value`` lines, stripping comments."""
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("#") or " = " not in line:
            continue
        key, _, value = line.partition(" = ")
        parsed[key.strip()] = value.split("  #")[0].strip()
    return parsed


# -- renderer ---------------------------------------------------------------


def test_render_config_when_full_model_matches_live_semantics() -> None:
    """Every model field lands as `Key = Value`; [Interface] precedes [Peer]."""
    model = _model()
    rendered = render_config(model)
    assert _key_values(rendered) == {
        "PrivateKey": model.private_key,
        "Address": model.address,
        "DNS": model.dns,
        "PublicKey": model.peer_public_key,
        "Endpoint": model.endpoint,
        "AllowedIPs": model.allowed_ips,
        "PersistentKeepalive": str(model.persistent_keepalive),
    }
    assert rendered.index("[Interface]") < rendered.index("[Peer]")
    assert rendered.endswith("\n")


def test_render_config_when_private_key_missing() -> None:
    """A partial model renders a parseable file instead of crashing."""
    rendered = render_config(_model(private_key=None))
    assert "#PrivateKey = (not provided - supply on next apply)" in rendered
    assert "PrivateKey" not in _key_values(rendered)


def test_render_config_when_dns_missing() -> None:
    rendered = render_config(_model(dns=None))
    assert "DNS" not in rendered
    assert "DNS" not in _key_values(rendered)


def test_render_config_when_both_optional_fields_missing() -> None:
    rendered = render_config(_model(private_key=None, dns=None))
    kvs = _key_values(rendered)
    assert "PrivateKey" not in kvs
    assert "DNS" not in kvs
    assert kvs["Address"] == "10.80.0.2/32"
    assert kvs["AllowedIPs"] == "10.80.0.0/16"


# -- atomic write + backup + perms -------------------------------------------


def test_write_config_when_previous_exists_backs_up_and_chmods_600(
    manager: WgClientManager, tmp_path: Path
) -> None:
    manager.config_path.write_text("OLD CONTENT\n")
    model = _model()
    written = manager.write_config(model)
    assert written == manager.config_path
    assert manager.config_path.read_text() == render_config(model)
    # mutation check target: drop the chmod-600 line and this fails
    assert manager.config_path.stat().st_mode & 0o777 == 0o600
    assert manager.backup_path.read_text() == "OLD CONTENT\n"
    # atomic write leaves no tmp litter behind
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "client.conf",
        "client.conf.viswall-backup",
    ]


def test_write_config_when_no_previous_file_takes_no_backup(
    manager: WgClientManager,
) -> None:
    manager.write_config(_model())
    assert not manager.backup_path.exists()
    assert manager.config_path.stat().st_mode & 0o777 == 0o600


def test_write_config_when_second_write_backs_up_previous_render(
    manager: WgClientManager,
) -> None:
    first = _model(endpoint="e1.example:51820")
    second = _model(endpoint="e2.example:51820")
    manager.write_config(first)
    manager.write_config(second)
    assert manager.backup_path.read_text() == render_config(first)
    assert manager.config_path.read_text() == render_config(second)
    assert manager.config_path.stat().st_mode & 0o777 == 0o600


def test_restore_backup_when_backup_exists(manager: WgClientManager) -> None:
    manager.config_path.write_text("BROKEN\n")
    manager.backup_path.write_text("GOOD\n")
    assert manager.restore_backup() is True
    assert manager.config_path.read_text() == "GOOD\n"
    assert manager.config_path.stat().st_mode & 0o777 == 0o600


def test_restore_backup_when_no_backup_returns_false(manager: WgClientManager) -> None:
    manager.config_path.write_text("CURRENT\n")
    assert manager.restore_backup() is False
    assert manager.config_path.read_text() == "CURRENT\n"


# -- unit steering (enable/disable + start/stop) ------------------------------


def test_start_enables_then_starts(managed) -> None:
    manager, fake = managed
    manager.start()
    assert fake.calls == [
        ("enable", "wg-quick@client"),
        ("start", "wg-quick@client"),
    ]


def test_start_when_unit_fails_raises_with_action(
    managed,
) -> None:
    manager, fake = managed
    fake.arm_failure("start", returncode=3, stderr="Unit not found.")
    with pytest.raises(WgUnitError) as excinfo:
        manager.start()
    assert excinfo.value.action == "start"
    assert "exited 3" in str(excinfo.value)
    assert "Unit not found." in str(excinfo.value)
    # enable still happened before the failing start
    assert fake.calls == [
        ("enable", "wg-quick@client"),
        ("start", "wg-quick@client"),
    ]


def test_stop_disables_then_stops(managed) -> None:
    manager, fake = managed
    manager.stop()
    assert fake.calls == [
        ("disable", "wg-quick@client"),
        ("stop", "wg-quick@client"),
    ]


def test_stop_when_unit_fails_raises_with_action(
    managed,
) -> None:
    manager, fake = managed
    fake.arm_failure("stop", returncode=1, stderr="No such unit.")
    with pytest.raises(WgUnitError) as excinfo:
        manager.stop()
    assert excinfo.value.action == "stop"


def test_systemctl_runs_via_nsenter_on_host_pid_1(
    shadow_bin: Path, manager: WgClientManager
) -> None:
    """The REAL `_systemctl` chain: `nsenter -t 1 -m -u -i -n -- systemctl ...`."""
    manager.start()
    calls = shadow_bin.read_text().splitlines()
    assert any(
        "-t 1 -m -u -i -n -- systemctl enable wg-quick@client" in line
        for line in calls
    )
    assert any(
        "-t 1 -m -u -i -n -- systemctl start wg-quick@client" in line
        for line in calls
    )
    assert any(
        "systemctl enable wg-quick@client" in line for line in calls
    )


# -- apply + rollback ---------------------------------------------------------


def test_apply_restarts_unit_with_new_config(
    managed,
) -> None:
    manager, fake = managed
    manager.config_path.write_text("OLD\n")
    model = _model()
    manager.apply(model)
    assert fake.calls == [("restart", "wg-quick@client")]
    assert manager.config_path.read_text() == render_config(model)
    assert manager.backup_path.read_text() == "OLD\n"


def test_apply_when_restart_fails_restores_backup_and_restarts(
    managed,
) -> None:
    """Rollback contract: old file restored AND the unit restarted with it."""
    manager, fake = managed
    baseline = render_config(_model(endpoint="e1.example:51820"))
    manager.config_path.write_text(baseline)
    fake.arm_failure("restart", returncode=1, stderr="simulated restart failure")

    with pytest.raises(WgApplyError) as excinfo:
        manager.apply(_model(endpoint="e2.example:51820"))

    assert "exited 1" in str(excinfo.value)
    assert "simulated restart failure" in str(excinfo.value)
    # exactly two restarts: the failing one, then the rollback restart
    assert fake.calls == [
        ("restart", "wg-quick@client"),
        ("restart", "wg-quick@client"),
    ]
    assert manager.config_path.read_text() == baseline
    assert manager.config_path.stat().st_mode & 0o777 == 0o600


# -- takeover gate -------------------------------------------------------------


def test_takeover_gate_when_marker_absent(manager: WgClientManager) -> None:
    """No reconcile without $STATE_DIR/takeover — host still owns the tunnel."""
    assert manager.takeover_enabled() is False


def test_takeover_gate_when_marker_present(manager: WgClientManager) -> None:
    manager.state_dir.mkdir(parents=True, exist_ok=True)
    (manager.state_dir / "takeover").write_text("")
    assert manager.takeover_enabled() is True


# -- status parser fixtures -----------------------------------------------------

WG_SHOW_UP = """\
interface: client
  public key: peerpub
  private key: (hidden)
  listening port: 51820

peer: peerpub
  endpoint: 46.4.63.216:51820
  allowed ips: 10.80.0.0/16
  latest handshake: 1 minute, 15 seconds ago
  transfer: 15.21 GiB received, 3.02 MiB sent
"""

IP_UP = json.dumps(
    [
        {
            "ifindex": 42,
            "ifname": "client",
            "operstate": "UNKNOWN",
            "addr_info": [
                {"family": "inet6", "local": "fe80::1", "prefixlen": 64},
                {"family": "inet", "local": "10.80.0.2", "prefixlen": 32},
            ],
        }
    ]
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("latest handshake: 58 seconds ago", 58),
        ("latest handshake: 1 minute, 15 seconds ago", 75),
        ("latest handshake: 2 hours, 3 minutes ago", 7380),
        ("latest handshake: 1 minute ago", 60),
        ("latest handshake: N/A", None),
        ("interface: client\n  listening port: 51820", None),
    ],
)
def test_parse_handshake_sec(text: str, expected: int | None) -> None:
    assert _parse_handshake_sec(text) == expected


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        ("15.21", "GiB", 16331613143),
        ("3.02", "MiB", 3166699),
        ("5", "B", 5),
        ("1", "KiB", 1024),
        ("not-a-number", "GiB", None),
        ("1", "bogus", None),
    ],
)
def test_parse_size(value: str, unit: str, expected: int | None) -> None:
    assert _parse_size(value, unit) == expected


def test_parse_wg_show_when_fully_populated() -> None:
    assert _parse_wg_show(WG_SHOW_UP) == (
        75,
        16331613143,
        3166699,
        "46.4.63.216:51820",
        "10.80.0.0/16",
    )


def test_parse_wg_show_when_no_handshake() -> None:
    out = WG_SHOW_UP.replace(
        "latest handshake: 1 minute, 15 seconds ago", "latest handshake: N/A"
    )
    handshake, rx, tx, endpoint, allowed = _parse_wg_show(out)
    assert handshake is None
    assert (rx, tx) == (16331613143, 3166699)
    assert endpoint == "46.4.63.216:51820"
    assert allowed == "10.80.0.0/16"


def test_status_when_interface_up(manager: WgClientManager, fake_ip_wg) -> None:
    fake_ip_wg(ip_stdout=IP_UP, wg_stdout=WG_SHOW_UP)
    status = manager.status()
    assert status.up is True
    assert status.interface == "client"
    assert status.address == "10.80.0.2/32"  # inet picked over inet6
    assert status.endpoint == "46.4.63.216:51820"
    assert status.latest_handshake_sec == 75
    assert status.transfer_rx == 16331613143
    assert status.transfer_tx == 3166699
    assert status.allowed_ips == "10.80.0.0/16"


def test_status_when_ip_fails_reports_down_without_calling_wg(
    manager: WgClientManager, fake_ip_wg
) -> None:
    fake = fake_ip_wg(ip_returncode=1)
    status = manager.status()
    assert status.up is False
    assert fake.wg_calls == 0


def test_status_when_ip_stdout_empty_reports_down(
    manager: WgClientManager, fake_ip_wg
) -> None:
    fake_ip_wg(ip_stdout="")
    status = manager.status()
    assert status.up is False


def test_status_when_ip_output_malformed_json_tolerated(
    manager: WgClientManager, fake_ip_wg
) -> None:
    fake_ip_wg(ip_stdout="not-json", wg_stdout=WG_SHOW_UP)
    status = manager.status()
    assert status.up is True
    assert status.address is None
    assert status.latest_handshake_sec == 75


def test_status_when_wg_fails_still_reports_up_with_unknown_fields(
    manager: WgClientManager, fake_ip_wg
) -> None:
    fake_ip_wg(ip_stdout=IP_UP, wg_returncode=1)
    status = manager.status()
    assert status.up is True
    assert status.address == "10.80.0.2/32"
    assert status.latest_handshake_sec is None
    assert status.endpoint is None


# -- config-value validation (F2 BLOCKER #3) --------------------------------


def test_render_config_rejects_allowed_ips_newline_injection() -> None:
    """A newline smuggles a PostUp line into a root-run wg-quick config."""
    malicious = "10.80.0.0/16\nPostUp = /tmp/pwned"
    with pytest.raises(WgConfigValidationError):
        render_config(_model(allowed_ips=malicious))


def test_render_config_rejects_allowed_ips_equals_injection() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(allowed_ips="10.80.0.0/16 = evil"))


def test_render_config_rejects_allowed_ips_bad_cidr() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(allowed_ips="10.80.0.0/16,not-a-cidr"))


def test_render_config_rejects_bad_local_address() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(address="10.80.0.2/33"))  # prefix > 32


def test_render_config_rejects_non_ip_local_address() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(address="not-an-address/24"))


def test_render_config_rejects_bad_endpoint() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(endpoint="evil host:51820"))


def test_render_config_rejects_malformed_private_key() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(private_key="not-a-key\nPostUp = evil"))


def test_render_config_rejects_malformed_peer_public_key() -> None:
    with pytest.raises(WgConfigValidationError):
        render_config(_model(peer_public_key="not-a-key"))
