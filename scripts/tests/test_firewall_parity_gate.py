"""Regression tests for ``scripts/firewall_parity_gate.py`` (plan todo 44 step 5).

The parity gate is the cutover's HARD GATE: it renders the desired
``table inet viswall`` from the COMMITTED live-capture fixtures and asserts
that every legacy accept/drop/meter/guard still exists. These tests prove the
gate is green on the fixtures AND that each sabotage class actually turns into
a literal ``DIFF`` line (a gate that cannot fail is not a gate).

Isolation: the fixtures under ``scripts/tests/fixtures/`` are used directly —
never ``/data/docker/persistent/backup/...`` — so the suite runs in CI
containers. ``render_desired`` imports the agent renderer in-process; it opens
no sockets and spawns no binaries, so the conftest guards stay satisfied.
"""

from __future__ import annotations

import pytest

import firewall_parity_gate as gate


def _diff_lines(rendered: str, rules_v4, rules_v6) -> list[str]:
    expected = gate.Expected()
    expected.add_iptables(rules_v4.read_text(), "v4")
    expected.add_iptables(rules_v6.read_text(), "v6")

    actual = gate.Actual()
    actual.add_nft_text(rendered)

    return [line for line in gate.compare(expected, actual) if line.startswith("DIFF")]


@pytest.fixture
def rendered(monkeypatch: pytest.MonkeyPatch, rules_v4, rules_v6) -> str:
    """The desired real-mode ruleset rendered from the committed fixtures.

    ``render_desired`` sets ``VALIDATION_MODE=0`` process-wide; registering the
    key with monkeypatch first restores the previous environment on teardown so
    later tests are not silently forced into real mode.
    """
    monkeypatch.setenv("VALIDATION_MODE", "0")
    return gate.render_desired(rules_v4, rules_v6)


def test_gate_all_pass_on_committed_fixtures(
    monkeypatch: pytest.MonkeyPatch, rules_v4, rules_v6, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("VALIDATION_MODE", "0")

    rc = gate.main(
        [
            "--rules-v4", str(rules_v4),
            "--rules-v6", str(rules_v6),
            "--render",
        ]
    )
    output = capsys.readouterr().out

    assert rc == 0
    assert "verdict: ALL PASS" in output
    assert [line for line in output.splitlines() if line.startswith("DIFF")] == []


def test_rendered_ruleset_surfaces_every_pass_class(
    rendered: str, rules_v4, rules_v6
) -> None:
    lines = gate.compare(
        _expected(rules_v4, rules_v6), _actual(rendered)
    )

    assert [line for line in lines if line.startswith("DIFF")] == []
    for passed in (
        "PASS accepts:",
        "PASS drops:",
        "PASS meters:",
        "PASS docker-internal-port-protection:",
        "PASS anti-spoof:",
    ):
        assert any(line.startswith(passed) for line in lines), passed


def test_missing_accept_is_diff(rendered: str, rules_v4, rules_v6) -> None:
    # Legacy tcp/25 is accepted both by the IPv4 bundle and by the bare mirror
    # rule, so a realistic regression removes BOTH before the gate sees it.
    mutated: list[str] = []
    for line in rendered.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == "ip protocol tcp tcp dport 25 accept":
            continue
        if "meta nfproto ipv4 tcp dport {" in line and stripped.endswith("accept"):
            line = line.replace(" 25,", "")
        mutated.append(line)

    assert _diff_lines("".join(mutated), rules_v4, rules_v6) == [
        "DIFF accept missing: v4 tcp/25"
    ]


def test_missing_5432_drop_is_diff(rendered: str, rules_v4, rules_v6) -> None:
    mutated = "\n".join(
        line
        for line in rendered.splitlines()
        if not (
            "5432" in line
            and line.strip().endswith("drop")
            and "limit rate" not in line
            and "daddr 127" not in line
        )
    )

    assert _diff_lines(mutated, rules_v4, rules_v6) == [
        "DIFF drop missing: v4 tcp/5432"
    ]


def test_meter_rate_change_is_diff(rendered: str, rules_v4, rules_v6) -> None:
    mutated = rendered.replace("limit rate over 10/minute", "limit rate over 99/minute")

    diffs = _diff_lines(mutated, rules_v4, rules_v6)

    assert (
        "DIFF meter rate: ssh_limit expected 10/minute, rendered 99/minute" in diffs
    )


def test_unexpected_open_port_is_diff(rendered: str, rules_v4, rules_v6) -> None:
    mutated = rendered.replace(
        "    chain input {",
        "    chain input {\n        ip protocol tcp tcp dport 9999 accept",
        1,
    )

    assert _diff_lines(mutated, rules_v4, rules_v6) == [
        "DIFF accept unexpected (port opened): v4 tcp/9999"
    ]


def _expected(rules_v4, rules_v6) -> gate.Expected:
    expected = gate.Expected()
    expected.add_iptables(rules_v4.read_text(), "v4")
    expected.add_iptables(rules_v6.read_text(), "v6")
    return expected


def _actual(rendered: str) -> gate.Actual:
    actual = gate.Actual()
    actual.add_nft_text(rendered)
    return actual
