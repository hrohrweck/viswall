"""Snapshot helper tests (todo 10): the pre-apply undo point.

``snapshot_state`` must capture every artifact, tolerate a missing/failing
tool (recorded in ``failures.txt``, never raised), and prune to the newest
``KEEP_SNAPSHOTS`` directories. The conftest guard blocks the real
``subprocess`` seam; these tests install a recorder over it.
"""

from __future__ import annotations

import subprocess as real_subprocess
from pathlib import Path

import pytest

import viswall_firewall_agent.snapshots as snapshots

_ARTIFACT_NAMES = (
    "rules.v4",
    "rules.v6",
    "nft-ruleset.txt",
    "ip-addr.json",
    "ip-route.json",
    "ip-rule.json",
    "tc-qdisc.txt",
    "wg-show.txt",
)


class _RecordingSubprocess:
    """Replaces the snapshots module's subprocess reference (sync runner)."""

    CalledProcessError = real_subprocess.CalledProcessError
    TimeoutExpired = real_subprocess.TimeoutExpired

    def __init__(self, failing: tuple[str, ...] = ()) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.failing = set(failing)

    def run(self, argv, **kwargs):
        self.calls.append(tuple(argv))
        if argv[0] in self.failing:
            raise self.CalledProcessError(
                returncode=127, cmd=argv, stderr=b"command not found"
            )
        return type("Completed", (), {"stdout": b"captured-data\n"})()


@pytest.fixture
def fake_subprocess(monkeypatch: pytest.MonkeyPatch):
    recorder = _RecordingSubprocess()
    monkeypatch.setattr(snapshots, "subprocess", recorder)
    return recorder


@pytest.fixture
def fake_netplan_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    netplan = tmp_path / "netplan-src"
    netplan.mkdir()
    (netplan / "01-netcfg.yaml").write_text("network:\n  version: 2\n")
    monkeypatch.setattr(snapshots, "NETPLAN_DIR", netplan)
    return netplan


@pytest.fixture
def deterministic_stamp(monkeypatch: pytest.MonkeyPatch):
    counter = iter(range(1, 100))

    def _stamp() -> str:
        return f"20261023-000000-{next(counter):06d}"

    monkeypatch.setattr(snapshots, "_utc_stamp", _stamp)


def test_snapshot_captures_every_artifact(
    tmp_path: Path, fake_subprocess, fake_netplan_dir: Path, deterministic_stamp
) -> None:
    state_dir = str(tmp_path / "state")

    snapshot_path = snapshots.snapshot_state(state_dir)

    snapshot = Path(snapshot_path)
    assert snapshot.parent == Path(state_dir) / "snapshots"
    for name in _ARTIFACT_NAMES:
        assert (snapshot / name).is_file()
        assert (snapshot / name).read_bytes() == b"captured-data\n"
    assert (snapshot / "netplan" / "01-netcfg.yaml").is_file()
    assert not (snapshot / "failures.txt").exists()
    assert len(fake_subprocess.calls) == len(_ARTIFACT_NAMES)


def test_snapshot_tolerates_missing_tools(
    tmp_path: Path, fake_subprocess, fake_netplan_dir: Path, deterministic_stamp
) -> None:
    fake_subprocess.failing = {"wg", "tc"}

    snapshot_path = snapshots.snapshot_state(str(tmp_path / "state"))

    snapshot = Path(snapshot_path)
    failures = (snapshot / "failures.txt").read_text()
    assert "wg-show.txt:" in failures
    assert "tc-qdisc.txt:" in failures
    assert (snapshot / "rules.v4").is_file()


def test_prune_keeps_newest_ten(tmp_path: Path) -> None:
    root = tmp_path / "snapshots"
    root.mkdir()
    for index in range(12):
        (root / f"20261023-000000-{index:06d}").mkdir()

    snapshots._prune_old_snapshots(root, keep=10)

    remaining = sorted(p.name for p in root.iterdir())
    assert remaining == [f"20261023-000000-{i:06d}" for i in range(2, 12)]
