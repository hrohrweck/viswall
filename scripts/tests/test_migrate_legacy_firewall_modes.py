"""Run-mode tests for scripts/migrate_legacy_firewall.py (plan todo 37).

Covers the executable paths of the importer: --dry-run safety (no socket, no
writes), the adversarial unmapped-input failure, and --rollback semantics
against a mocked HTTP layer. Plan/accounting tests live in
test_migrate_legacy_firewall.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

import migrate_legacy_firewall as fw


def test_dry_run_opens_no_socket_and_writes_nothing(
    run_fw_main, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--dry-run parses and prints the plan without touching the network or
    the filesystem. socket.socket is patched to raise by the conftest guard,
    so any attempt to reach the API would fail this test loudly."""
    manifest = tmp_path / "firewall_import_manifest.json"
    stale4 = tmp_path / "no-stale4"
    stale6 = tmp_path / "no-stale6"

    rc = run_fw_main(
        (
            "--dry-run",
            "--import-manifest", str(manifest),
            "--stale4-file", str(stale4),
            "--stale6-file", str(stale6),
        )
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert "mode: DRY-RUN — no API calls, no writes." in out
    assert "rows planned: 107" in out
    assert "no stale file" in out            # divergence report guards exercised
    assert not manifest.exists()             # dry-run writes nothing
    assert not stale4.exists() and not stale6.exists()


def test_unmapped_rule_fails_the_run(
    run_fw_main, tmp_path: Path, capsys: pytest.CaptureFixture[str], rules_v4: Path
) -> None:
    """Adversarial: one unmapped -A line must fail the run loudly (rc 1),
    never be silently dropped."""
    bad = tmp_path / "rules.bad.live"
    bad.write_text(rules_v4.read_text() + "\n-A FORWARD -p tcp --dport 8443 -j ACCEPT\n")

    rc = run_fw_main(
        ("--rules-file", str(bad),
         "--stale4-file", str(tmp_path / "x"),
         "--stale6-file", str(tmp_path / "y"))
    )
    out = capsys.readouterr().out

    assert rc == 1
    assert "FATAL" in out and "could not be mapped" in out
    assert "-A FORWARD -p tcp --dport 8443 -j ACCEPT" in out


def test_rollback_deletes_only_manifest_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = tmp_path / "firewall_import_manifest.json"
    manifest.write_text(json.dumps({
        "created": [
            {"name": "allow tcp/22", "id": 11},
            {"name": "drop tcp/5432", "id": 12},
        ],
        "instance_id": 1,
        "applied_at": 1761200000,
    }))
    calls: list[tuple[str, str]] = []

    def fake_http(method: str, url: str, token: str, body: dict | None = None) -> dict:
        calls.append((method, url))
        return {}

    monkeypatch.setattr(fw, "_http", fake_http)  # HTTP layer mock — no network
    monkeypatch.setenv("VISWALL_TOKEN", "test-jwt-not-real")
    args = argparse.Namespace(
        api_url="https://example.invalid/api/v1",
        import_manifest=str(manifest),
        instance_id=1,
    )

    rc = fw.rollback_rows(args)
    out = capsys.readouterr().out

    assert rc == 0
    deleted = [url.rsplit("/", 1)[-1] for method, url in calls if method == "DELETE"]
    assert sorted(deleted) == ["11", "12"]
    assert "deleted 2 rows" in out
    # a row NOT recorded in the manifest is never requested
    assert all("13" not in url for _, url in calls)
    # manifest is kept and annotated, entries preserved
    saved = json.loads(manifest.read_text())
    assert "rolled_back_at" in saved
    assert [entry["id"] for entry in saved["created"]] == [11, 12]


def test_rollback_tolerates_already_deleted_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = tmp_path / "firewall_import_manifest.json"
    manifest.write_text(json.dumps({
        "created": [
            {"name": "already gone", "id": 7},
            {"name": "still there", "id": 8},
        ]
    }))

    def fake_http(method: str, url: str, token: str, body: dict | None = None) -> dict:
        if url.endswith("/7"):
            raise fw.ApiError(404, "not found")
        return {}

    monkeypatch.setattr(fw, "_http", fake_http)
    monkeypatch.setenv("VISWALL_TOKEN", "test-jwt-not-real")
    args = argparse.Namespace(
        api_url="https://example.invalid/api/v1",
        import_manifest=str(manifest),
        instance_id=1,
    )

    rc = fw.rollback_rows(args)
    out = capsys.readouterr().out

    assert rc == 0
    assert "deleted 1 rows, already gone 1" in out
    assert "already gone id=7" in out


def test_rollback_missing_manifest_returns_4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("VISWALL_TOKEN", "test-jwt-not-real")
    args = argparse.Namespace(
        api_url="https://example.invalid/api/v1",
        import_manifest=str(tmp_path / "missing.json"),
        instance_id=1,
    )

    rc = fw.rollback_rows(args)
    out = capsys.readouterr().out

    assert rc == 4
    assert "not found" in out
