"""Rendering tests for viswall_dns_agent.render."""

from __future__ import annotations

from viswall_dns_agent.payloads import (
    DNSRecordPayload,
    DNSZonePayload,
    DNSServerConfigPayload,
    TSIGKeyPayload,
)
from viswall_dns_agent.render import (
    record_line,
    render_local_text,
    render_options_text,
    render_zone_block,
    render_zone_text,
)


def _zone(**overrides) -> DNSZonePayload:
    base = dict(
        id=1,
        name="example.com",
        zone_type="master",
        serial=2026090512,
        refresh=3600,
        retry=600,
        expire=86400,
        minimum_ttl=3600,
    )
    return DNSZonePayload(**{**base, **overrides})


def _server(**overrides) -> DNSServerConfigPayload:
    base = dict(
        server_id=7,
        name="node0-dns",
        listening_addresses=["46.4.63.216", "2a01:4f8:140:22ef::2"],
        is_recursive=False,
        allow_query=["0.0.0.0/0", "::/0"],
        allow_transfer=["93.111.66.28"],
        also_notify=["93.111.66.28"],
    )
    return DNSServerConfigPayload(**{**base, **overrides})


def test_record_line_when_mx() -> None:
    given = DNSRecordPayload(
        name="@", record_type="MX", content="mx1.example.com.", ttl=38400, priority=10
    )
    assert record_line(given) == "@ 38400 IN MX 10 mx1.example.com."


def test_record_line_when_srv() -> None:
    given = DNSRecordPayload(
        name="_sip._tcp",
        record_type="SRV",
        content="sip.example.com.",
        ttl=600,
        priority=1,
        weight=2,
        port=3,
    )
    assert record_line(given) == "_sip._tcp 600 IN SRV 1 2 3 sip.example.com."


def test_record_line_when_plain() -> None:
    given = DNSRecordPayload(name="www", record_type="A", content="192.0.2.1", ttl=60)
    assert record_line(given) == "www 60 IN A 192.0.2.1"


def test_render_zone_text_when_soa_present() -> None:
    zone = _zone(
        records=[
            DNSRecordPayload(
                name="@",
                record_type="SOA",
                content="dns1.example.com. admin.example.com. 2026090512 3600 600 86400 3600",
            )
        ]
    )
    text = render_zone_text(zone, include_dnssec=False)
    assert "$TTL 3600" in text
    assert "dns1.example.com. admin.example.com. 2026090512" in text
    assert "@ IN SOA ns1." not in text


def test_render_zone_text_when_soa_missing_generates_default() -> None:
    zone = _zone(
        records=[DNSRecordPayload(name="www", record_type="A", content="192.0.2.1")]
    )
    text = render_zone_text(zone, include_dnssec=False)
    assert "ns1.example.com. admin.example.com." in text
    assert "2026090512 ; serial" in text


def test_render_options_text_when_wildcard_listens_become_any() -> None:
    text = render_options_text(_server(listening_addresses=["0.0.0.0"]))
    assert "listen-on { any; };" in text
    assert "listen-on-v6" not in text
    text6 = render_options_text(_server(listening_addresses=["::", "0.0.0.0"]))
    assert "listen-on { any; };" in text6
    assert "listen-on-v6 { any; };" in text6


def test_render_options_text_splits_listen_addresses_by_family() -> None:
    text = render_options_text(_server())
    assert 'listen-on { 46.4.63.216; };' in text
    assert "listen-on-v6 { 2a01:4f8:140:22ef::2; };" in text
    assert "recursion no;" in text
    assert "allow-transfer { 93.111.66.28; };" in text
    assert "also-notify { 93.111.66.28; };" in text
    assert "forwarders" not in text
    assert 'directory "/var/cache/bind";' in text
    assert 'include "/etc/bind/rndc.key";' in text


def test_render_options_text_contains_no_zone_statements() -> None:
    """The options file must never carry zone/key blocks (double-include bug)."""
    text = render_options_text(_server())
    assert 'zone "' not in text
    assert text.count("options {") == 1


def test_render_options_text_when_forwarders_set() -> None:
    text = render_options_text(_server(forwarders=["185.12.64.1", "185.12.64.2"]))
    assert "forwarders { 185.12.64.1; 185.12.64.2; };" in text


def test_render_zone_block_when_master_with_tsig() -> None:
    block = render_zone_block(_zone(), "/var/lib/bind/viswall-zones/zone-1-example.com.db", "axfr-key")
    assert 'zone "example.com" {' in block
    assert "type master;" in block
    assert 'allow-transfer { key "axfr-key"; };' in block
    assert 'also-notify { key "axfr-key"; };' in block


def test_render_zone_block_when_slave_without_master_address() -> None:
    try:
        render_zone_block(_zone(zone_type="slave"), "/tmp/z.db", None)
    except ValueError as exc:
        assert "missing master_server_address" in str(exc)
    else:
        raise AssertionError("slave zone without master must raise")


def test_render_zone_block_when_slave_with_tsig() -> None:
    block = render_zone_block(
        _zone(zone_type="slave", master_server_address="192.0.2.10"),
        "/tmp/z.db",
        "axfr-key",
    )
    assert "type slave;" in block
    assert "masters { 192.0.2.10 key axfr-key; };" in block


def test_render_local_text_contains_tsig_and_zones_only() -> None:
    payload = _server(
        tsig_keys=[TSIGKeyPayload(id=1, name="axfr-key", secret="c2VjcmV0")]
    )
    text = render_local_text(payload, [render_zone_block(_zone(), "/tmp/z.db", None)])
    assert 'key "axfr-key" {' in text
    assert "algorithm hmac-sha256;" in text
    assert 'secret "c2VjcmV0";' in text
    assert 'zone "example.com" {' in text
    # the local file must never carry an options block (double-include bug)
    assert "options {" not in text
    assert "server_id=7" in text
