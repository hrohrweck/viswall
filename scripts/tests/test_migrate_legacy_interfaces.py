"""Importer tests for scripts/migrate_legacy_interfaces.py (plan todo 37).

Fixtures under scripts/tests/fixtures/: the real netplan yaml (trimmed copy of
/etc/netplan/01-netcfg.yaml from the todo-3 backup), a trimmed `ip -j addr`
capture, and a client.conf whose key material is REGENERATED FAKE (zero-entropy
placeholders in the wg base64 shape — never the production key).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import migrate_legacy_interfaces as ifaces


# --- netplan render roundtrip ---------------------------------------------------


def test_netplan_enp0s31f6_renders_as_wan_static(netplan_file: Path) -> None:
    rows = ifaces.parse_netplan(netplan_file)
    assert [row.name for row in rows] == ["enp0s31f6"]
    wan = rows[0]
    assert wan.type == "wan"                       # default route present -> wan
    assert wan.config_type == "static"
    assert wan.ip_address == "46.4.63.216"
    assert wan.netmask == "255.255.255.255"
    assert wan.cidr() == "46.4.63.216/32"
    assert wan.gateway == "46.4.63.193"
    assert wan.ipv6_address == "2a01:4f8:140:22ef::2/64"
    assert wan.ipv6_gateway == "fe80::1"
    assert wan.dns_servers == [
        "185.12.64.1",
        "185.12.64.2",
        "2a01:4ff:ff00::add:2",
        "2a01:4ff:ff00::add:1",
    ]  # v4 first, then v6 — matches the documented order
    assert wan.routes == [
        {"to": "0.0.0.0/0", "via": "46.4.63.193", "on_link": True},
    ]  # on-link default kept as a route; ::/0 is the ipv6_gateway
    assert wan.enabled is True


# --- wireguard client parse ------------------------------------------------------


def test_wireguard_client_parse(wg_conf: Path, fake_wg_keys: tuple[str, str]) -> None:
    private, public = fake_wg_keys
    vpn = ifaces.parse_wireguard(wg_conf)
    assert vpn.name == "site-to-site-base0"
    assert vpn.tunnel_type == "site-to-site"
    assert vpn.protocol == "wireguard"
    assert vpn.endpoint == "base0.webmasters.co.at:51820"
    assert vpn.allowed_ips == "10.80.0.0/16"
    assert vpn.persistent_keepalive == 25
    assert vpn.local_address == "10.80.210.2/24"
    assert vpn.private_key == private          # fixture carries regenerated fakes
    assert vpn.peer_public_key == public
    assert vpn.enabled is True
    assert "site-to-site" in vpn.description


def test_wireguard_fixture_uses_regenerated_fake_keys(
    wg_conf: Path, fake_wg_keys: tuple[str, str]
) -> None:
    """The committed fixture must contain exactly the fake key material —
    zero-entropy placeholders, structurally a valid wg key shape, provably
    not a real secret (and immune to secret scanners)."""
    private, public = fake_wg_keys
    text = wg_conf.read_text()
    assert f"PrivateKey = {private}" in text
    assert f"PublicKey = {public}" in text
    for key in (private, public):
        assert len(key) == 44 and key.endswith("=")
        assert len(set(key[:-1])) == 1       # single repeated char => zero entropy


# --- dry-run safety + redaction ---------------------------------------------------


def test_dry_run_redacts_key_material(
    run_ifaces_main, capsys: pytest.CaptureFixture[str], fake_wg_keys: tuple[str, str]
) -> None:
    private, public = fake_wg_keys
    rc = run_ifaces_main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "private_key=REDACTED" in out
    assert "peer_public_key=REDACTED" in out
    assert private not in out and public not in out
    assert "PrivateKey =" not in out          # no key/value echo anywhere


def test_dry_run_reports_wan_and_wireguard_fields(
    run_ifaces_main, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = run_ifaces_main()
    out = capsys.readouterr().out
    assert rc == 0
    assert (
        "enp0s31f6: type=wan config_type=static ip=46.4.63.216/32 "
        "gateway=46.4.63.193" in out
    )
    assert "ipv6=2a01:4f8:140:22ef::2/64 ipv6_gateway=fe80::1" in out
    assert (
        "dns_servers=['185.12.64.1', '185.12.64.2', "
        "'2a01:4ff:ff00::add:2', '2a01:4ff:ff00::add:1']" in out
    )
    assert "routes=[{'to': '0.0.0.0/0', 'via': '46.4.63.193', 'on_link': True}]" in out
    assert "mtu=1500" in out                   # merged from the live ip -j addr fixture
    assert "endpoint=base0.webmasters.co.at:51820" in out
    assert "allowed_ips=10.80.0.0/16" in out
    assert "persistent_keepalive=25" in out
    assert "local_address=10.80.210.2/24" in out
    assert "status=stopped" in out
    assert "mode: DRY-RUN — no API calls were made." in out


def test_dry_run_writes_nothing_and_opens_no_socket(
    run_ifaces_main, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--dry-run must not construct an API client, write the manifest, or
    open a socket. socket.socket and subprocess.run are patched to raise by
    the conftest guards, so any violation fails this test loudly."""
    manifest = tmp_path / "interfaces_import_manifest.json"
    rc = run_ifaces_main(("--import-manifest", str(manifest)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "mode: DRY-RUN — no API calls were made." in out
    assert not manifest.exists()
    assert list(tmp_path.iterdir()) == []      # literally nothing written


# --- live discovery ---------------------------------------------------------------


def test_live_discovery_trimmed_fixture(
    ip_addr_json: Path, netplan_file: Path
) -> None:
    netplan_names = {row.name for row in ifaces.parse_netplan(netplan_file)}
    rows, mtu_by_name = ifaces.discover_live(ip_addr_json, netplan_names)

    names = [row.name for row in rows]
    assert "lo" not in names                   # loopback never a row
    assert "enp0s31f6" not in names            # netplan-defined names excluded
    assert names == sorted(names)              # deterministic order

    by_name = {row.name: row for row in rows}
    client = by_name["client"]
    assert client.description == "wireguard site-to-site"
    assert client.ip_address == "10.80.210.2" and client.netmask == "255.255.255.0"
    assert client.mtu == 1420
    assert client.type == "other" and client.config_type == "dhcp"

    assert by_name["docker0"].ip_address == "172.17.0.1"
    assert by_name["docker0"].ipv6_address == "2001:db8:1::1/64"
    assert by_name["br-dcbbead2b63e"].ipv6_address == "fd00:42::1/64"
    assert by_name["vetheff5fbb"].ip_address is None  # empty addr_info tolerated

    assert mtu_by_name["enp0s31f6"] == 1500    # mtu map feeds the netplan merge


# --- adversarial inputs ------------------------------------------------------------


def test_missing_wireguard_conf_raises(tmp_path: Path) -> None:
    with pytest.raises(ifaces.MigrationError, match="not found"):
        ifaces.parse_wireguard(tmp_path / "absent.conf")


def test_missing_private_key_raises(
    tmp_path: Path, fake_wg_keys: tuple[str, str]
) -> None:
    _, public = fake_wg_keys
    bad = tmp_path / "nokey.conf"
    bad.write_text(
        "[Interface]\n"
        "Address = 10.80.210.2/24\n"
        "\n"
        "[Peer]\n"
        f"PublicKey = {public}\n"
        "Endpoint = base0.webmasters.co.at:51820\n"
        "AllowedIPs = 10.80.0.0/16\n"
        "PersistentKeepalive = 25\n"
    )
    with pytest.raises(ifaces.MigrationError, match="PrivateKey"):
        ifaces.parse_wireguard(bad)


def test_malformed_netplan_missing_ethernets_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad-netcfg.yaml"
    bad.write_text("network:\n  version: 2\n")
    with pytest.raises(ifaces.MigrationError, match="ethernets"):
        ifaces.parse_netplan(bad)


def test_missing_netplan_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ifaces.MigrationError, match="not found"):
        ifaces.parse_netplan(tmp_path / "absent.yaml")
