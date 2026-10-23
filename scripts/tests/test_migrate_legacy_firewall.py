"""Importer tests for scripts/migrate_legacy_firewall.py (plan todo 37).

Fixtures are trimmed copies of the REAL live captures (todo-3 backup) under
scripts/tests/fixtures/rules.v{4,6}.live. Expected counts are pinned to the
todo-34 divergence report (.omo/evidence/task-34-firewall-migration.md); the
MASQUERADE duplicate count is additionally derived from the fixture content
itself, so the accounting can never pass against a hardcoded number.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

import migrate_legacy_firewall as fw

# --- Expected values pinned to the todo-34 divergence report -----------------
# .omo/evidence/task-34-firewall-migration.md (live-capture run, 2026-10-23).
EVIDENCE_ROWS = 107
EVIDENCE_ACCEPT_V4 = 18
EVIDENCE_ACCEPT_V6 = 4
EVIDENCE_METERS_V4 = 4
EVIDENCE_METERS_V6 = 4
EVIDENCE_DROPS = 1              # INPUT tcp/5432 explicit drop (policy is never a row)
EVIDENCE_LOOPBACK_GUARDS = 12
EVIDENCE_ANTISPOOF_V4 = 48
EVIDENCE_ANTISPOOF_V6 = 15
EVIDENCE_INTERNAL_LINES = 34    # 17 v4 + 17 v6 DOCKER-USER ctorigdstport lines
EVIDENCE_NAT_LINES = 130        # v4 108 + v6 22
EVIDENCE_MASQUERADE_TOTAL = 67  # v4 65 + v6 2, all docker-owned, NOT imported
EVIDENCE_MASQUERADE_DUPES = 47  # max identical-line count (the loud report line)

# Live ports from the capture's raw loopback guards (todo-34 report).
LOOPBACK_GUARD_PORTS = {
    5432, 6379, 3000, 3001, 8010, 8065, 8082, 8088, 8095, 9091, 9121, 20000,
}
# Live DOCKER-USER ctorigdstport set (todo-34 report; sorted for the row).
DOCKER_USER_PORTS = (
    5000, 5055, 5678, 8000, 8001, 8080, 8089, 8090, 8091,
    8096, 8100, 8201, 8502, 8888, 9090, 10000, 11434,
)


def _kind_count(plan: fw.Plan, kind: str, family: str | None = None) -> int:
    """Number of planned rows of ``kind`` (optionally for one family)."""
    return sum(
        count
        for (fam, row_kind), count in plan.row_kinds.items()
        if row_kind == kind and (family is None or fam == family)
    )


# --- The accounting test ------------------------------------------------------


def test_every_a_line_maps_to_a_row_or_a_documented_skip(
    fw_plan: fw.Plan, rules_v4: Path, rules_v6: Path
) -> None:
    """Every -A line of the real capture maps to a row, a skip, or the
    DOCKER-USER aggregation — nothing is silently dropped."""
    assert fw_plan.unmapped == [], f"unmapped lines: {fw_plan.unmapped}"

    total_lines = 0
    for path in (rules_v4, rules_v6):
        total_lines += sum(
            1 for line in path.read_text().splitlines()
            if line.strip().startswith("-A")
        )

    line_rows = len(fw_plan.rows) - 1  # the DOCKER-USER row is aggregated, not a line
    skipped = sum(len(texts) for texts in fw_plan.skips.values())
    accounted = line_rows + skipped + fw_plan.internal_lines

    assert accounted == total_lines, (
        f"accounting mismatch: {line_rows} rows + {skipped} skips + "
        f"{fw_plan.internal_lines} internal != {total_lines} -A lines"
    )
    assert len(fw_plan.rows) == EVIDENCE_ROWS


def test_row_kind_counts_match_divergence_report(fw_plan: fw.Plan) -> None:
    assert _kind_count(fw_plan, "accept", "v4") == EVIDENCE_ACCEPT_V4
    assert _kind_count(fw_plan, "accept", "v6") == EVIDENCE_ACCEPT_V6
    assert _kind_count(fw_plan, "meter", "v4") == EVIDENCE_METERS_V4
    assert _kind_count(fw_plan, "meter", "v6") == EVIDENCE_METERS_V6
    assert _kind_count(fw_plan, "drop") == EVIDENCE_DROPS
    assert _kind_count(fw_plan, "loopback-guard") == EVIDENCE_LOOPBACK_GUARDS
    assert _kind_count(fw_plan, "anti-spoof", "v4") == EVIDENCE_ANTISPOOF_V4
    assert _kind_count(fw_plan, "anti-spoof", "v6") == EVIDENCE_ANTISPOOF_V6
    assert _kind_count(fw_plan, "internal-port-protection") == 1


# --- hashlimit -> limit string -------------------------------------------------


def test_hashlimit_lines_become_meter_rows_with_limit_strings(
    fw_plan: fw.Plan,
) -> None:
    meters = {row["name"]: row for kind, row in fw_plan.row_meta if kind == "meter"}
    assert len(meters) == EVIDENCE_METERS_V4 + EVIDENCE_METERS_V6

    expected = {
        "ssh_limit": ("10/minute burst 5 packets", "22", "tcp"),
        "http_limit": ("100/minute burst 5 packets", "80", "tcp"),
        "https_limit": ("100/minute burst 5 packets", "443", "tcp"),
        "wireguard_limit": ("20/minute burst 5 packets", "51820", "udp"),
    }
    for base, (limit, ports, proto) in expected.items():
        for suffix in ("", "_v6"):  # v6 file carries the same meters with _v6 names
            row = meters[base + suffix]
            assert row["limit"] == limit
            assert row["service_ports"] == ports
            assert row["service_protocol"] == proto
            assert row["action"] == "drop"
            assert row["name"] == base + suffix


# --- multiport parse -----------------------------------------------------------


def test_ports_helper_parses_lists_and_ranges() -> None:
    assert fw._ports("80,443,8080", 1) == (80, 443, 8080)
    assert fw._ports("21114:21119", 1) == (21114, 21115, 21116, 21117, 21118, 21119)
    with pytest.raises(fw.ParseError):
        fw._ports("80,http", 1)


def test_multiport_accept_line_expands_to_one_row_per_port() -> None:
    text = (
        "*filter\n"
        ":INPUT DROP [0:0]\n"
        "-A INPUT -p tcp -m multiport --dports 80,443,8080 -j ACCEPT\n"
        "COMMIT\n"
    )
    (rule,) = fw.parse_iptables_save(text)
    kind, data = fw.classify(rule)
    assert (kind, data["kind"]) == ("row", "accept")
    rows = fw.build_rows(rule, data, "v4")
    assert [row["service_ports"] for _, row in rows] == ["80", "443", "8080"]
    assert all(row["action"] == "accept" for _, row in rows)


def test_multiport_range_drop_line_expands_per_port() -> None:
    text = (
        "*filter\n"
        ":INPUT DROP [0:0]\n"
        "-A INPUT -p tcp -m multiport --dports 1000:1003 -j DROP\n"
        "COMMIT\n"
    )
    (rule,) = fw.parse_iptables_save(text)
    kind, data = fw.classify(rule)
    assert (kind, data["kind"]) == ("row", "drop")
    rows = fw.build_rows(rule, data, "v4")
    assert [row["service_ports"] for _, row in rows] == ["1000", "1001", "1002", "1003"]
    assert all(row["action"] == "drop" for _, row in rows)


# --- DOCKER-USER aggregation ----------------------------------------------------


def test_docker_user_aggregates_into_one_row_with_the_17_ports(
    fw_plan: fw.Plan,
) -> None:
    agg = [row for kind, row in fw_plan.row_meta if kind == "internal-port-protection"]
    assert len(agg) == 1
    row = agg[0]
    assert row["name"] == "docker-internal-port-protection"
    assert row["service_protocol"] == "tcp"
    assert row["action"] == "drop"
    assert tuple(int(p) for p in row["service_ports"].split(",")) == DOCKER_USER_PORTS
    assert fw_plan.internal_lines == EVIDENCE_INTERNAL_LINES
    assert "34 lines" in row["description"]       # live count, both families
    assert "enp0s31f6" in row["description"]      # iif recorded in the audit note


# --- MASQUERADE duplicate detection (NOT hardcoded) ----------------------------


def test_masquerade_duplicate_count_matches_divergence_report(
    fw_plan: fw.Plan, rules_v4: Path, rules_v6: Path
) -> None:
    # Pinned to the value recorded in todo 34's divergence report for THIS
    # fixture (the live capture, not the stale file's 48).
    assert fw_plan.masquerade.total() == EVIDENCE_MASQUERADE_TOTAL
    assert max(fw_plan.masquerade.values()) == EVIDENCE_MASQUERADE_DUPES
    assert (
        fw_plan.masquerade[
            "-A POSTROUTING -s 172.17.0.0/16 -o enp0s31f6 -j MASQUERADE"
        ]
        == EVIDENCE_MASQUERADE_DUPES
    )

    # NOT hardcoded: the importer's Counter must equal the fixture's own line
    # frequencies, so the assertion holds only if the detection mirrors the
    # capture content exactly.
    lines = rules_v4.read_text().splitlines() + rules_v6.read_text().splitlines()
    fixture_counter = Counter(
        line.strip()
        for line in lines
        if "MASQUERADE" in line and line.strip().startswith("-A")
    )
    assert fw_plan.masquerade == fixture_counter


# --- NAT table skipped with a report -------------------------------------------


def test_nat_table_is_skipped_with_a_report(fw_plan: fw.Plan) -> None:
    assert fw_plan.nat_lines == EVIDENCE_NAT_LINES
    nat_skips = fw_plan.skips["docker-owned NAT (not imported)"]
    assert len(nat_skips) == EVIDENCE_NAT_LINES
    assert all(text.startswith(("v4:", "v6:")) for text in nat_skips)
    # no planned row is derived from NAT lines
    for _, row in fw_plan.row_meta:
        assert "MASQUERADE" not in row["description"]
        assert "DNAT" not in row["description"]


# --- raw PREROUTING guards ------------------------------------------------------


def test_loopback_guards_are_host_dest_input_drops(fw_plan: fw.Plan) -> None:
    guards = [row for kind, row in fw_plan.row_meta if kind == "loopback-guard"]
    assert len(guards) == EVIDENCE_LOOPBACK_GUARDS
    assert {int(row["service_ports"]) for row in guards} == LOOPBACK_GUARD_PORTS
    assert all(
        row["dest_type"] == "host" and row["dest_value"] == "127.0.0.1"
        for row in guards
    )
    assert all(
        row["action"] == "drop" and row["service_protocol"] == "tcp"
        for row in guards
    )
    assert all(row["name"].startswith("loopback-guard tcp/") for row in guards)


def test_anti_spoof_rows_carry_network_dest_and_bridge_names(
    fw_plan: fw.Plan,
) -> None:
    rows = [row for kind, row in fw_plan.row_meta if kind == "anti-spoof"]
    assert len(rows) == EVIDENCE_ANTISPOOF_V4 + EVIDENCE_ANTISPOOF_V6
    assert all(
        row["dest_type"] == "network" and row["action"] == "drop" for row in rows
    )
    # name carries the container IP + bridge (the renderer tag contract)
    assert all(
        row["name"].startswith("anti-spoof ") and " via " in row["name"]
        for row in rows
    )
    v6 = [row for row in rows if ":" in row["dest_value"]]
    assert len(v6) == EVIDENCE_ANTISPOOF_V6
    assert any(row["dest_value"].startswith("fd00:42::") for row in v6)
    assert all(row["dest_value"].endswith("/128") for row in v6)


# --- INPUT accept/drop rows -----------------------------------------------------


def test_accept_rows_cover_the_inventory_and_v6_gets_suffix(
    fw_plan: fw.Plan,
) -> None:
    rows = [row for kind, row in fw_plan.row_meta if kind == "accept"]
    assert len(rows) == EVIDENCE_ACCEPT_V4 + EVIDENCE_ACCEPT_V6
    v6 = [row for row in rows if row["name"].endswith(" (ipv6)")]
    assert len(v6) == EVIDENCE_ACCEPT_V6
    got = {(row["service_protocol"], int(row["service_ports"])) for row in rows}
    assert set(fw.EXPECTED_V4) <= got  # 18/18 open ports from the inventory
    assert all(row["action"] == "accept" for row in rows)


def test_explicit_input_drop_row(fw_plan: fw.Plan) -> None:
    drops = [row for kind, row in fw_plan.row_meta if kind == "drop"]
    assert len(drops) == EVIDENCE_DROPS
    assert drops[0]["name"] == "drop tcp/5432"
    assert drops[0]["service_ports"] == "5432"
    assert drops[0]["action"] == "drop"


# Run-mode tests (--dry-run safety, adversarial unmapped input, --rollback with
# a mocked HTTP layer) live in test_migrate_legacy_firewall_modes.py.
