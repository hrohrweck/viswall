"""Regression tests for scripts/restore_firewall.sh no-op guard ordering.

F2 review BLOCKER #2: the COMMIT + ALIVE no-op guard used to run AFTER
``systemctl disable --now viswall-firewall-persist`` and
``nft delete table inet viswall`` — a scheduled no-op mutated live firewall
state. The guard now runs FIRST; these tests prove a no-op trip exits 0 with
zero destructive invocations, and that without a marker the destructive path
still runs (so the shim harness is not vacuously green).

Isolation: every binary the script calls is replaced by a logging shim on
PATH — nothing touches the real systemctl/nft/iptables/netplan state, and
STATE_DIR/LOG are pointed at tmp dirs via env.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "restore_firewall.sh"

# The suite's autouse ``no_real_subprocess`` fixture blocks subprocess.run/Popen
# for the IMPORTER modules; this test deliberately runs restore_firewall.sh under
# shimmed binaries, so it uses module-import-time references to the real
# functions (the monkeypatch only rebinds the subprocess module attributes).
_POPEN = subprocess.Popen

#: Binaries that must never be invoked when the no-op guard trips.
DESTRUCTIVE = {
    "systemctl",
    "nft",
    "iptables-restore",
    "ip6tables-restore",
    "netplan",
    "cp",
    "chmod",
}

#: Read-only helpers left to the real system (never mutate anything).
PASSTHROUGH = {"date", "stat", "tee", "bash", "sh"}


def _write_shims(bindir: Path, logfile: Path) -> None:
    """Create log-only shims for every binary the script may call."""
    bindir.mkdir(parents=True, exist_ok=True)
    for name in sorted(DESTRUCTIVE):
        (bindir / name).write_text(
            f"#!/bin/sh\n"
            f"echo {name} >> '{logfile}'\n"
            f"printf '%s\\n' \"$@\" >> '{logfile}'\n"
            f"exit 0\n"
        )
        (bindir / name).chmod(0o755)


def _run_script(bindir: Path, state_dir: Path, snapshot: Path, log_file: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{os.environ['PATH']}"
    env["STATE_DIR"] = str(state_dir)
    env["LOG"] = str(log_file)
    proc = _POPEN(
        ["bash", str(SCRIPT), "--no-restart-docker", str(snapshot)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = proc.communicate(timeout=30)
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


@pytest.fixture
def harness(tmp_path: Path):
    bindir = tmp_path / "bin"
    state_dir = tmp_path / "state"
    snapshot = tmp_path / "snapshot"
    state_dir.mkdir()
    snapshot.mkdir()
    (snapshot / "rules.v4").write_text("*filter\nCOMMIT\n")
    (snapshot / "rules.v6").write_text("*filter\nCOMMIT\n")
    log_file = tmp_path / "restore.log"
    calls = tmp_path / "calls.log"
    _write_shims(bindir, calls)
    return bindir, state_dir, snapshot, log_file, calls


def _recorded(calls: Path) -> list[str]:
    if not calls.exists():
        return []
    return calls.read_text().splitlines()


class TestNoOpGuardRunsFirst:
    def test_commit_marker_exits_0_without_any_destructive_call(self, harness):
        bindir, state_dir, snapshot, log_file, calls = harness
        (state_dir / "COMMIT").write_text("cutover committed\n")

        result = _run_script(bindir, state_dir, snapshot, log_file)

        assert result.returncode == 0
        assert "no-op:" in log_file.read_text()
        assert _recorded(calls) == []

    def test_fresh_alive_marker_exits_0_without_any_destructive_call(self, harness):
        bindir, state_dir, snapshot, log_file, calls = harness
        alive = state_dir / "ALIVE"
        alive.write_text("proof of life\n")
        now = time.time()
        os.utime(alive, (now, now))

        result = _run_script(bindir, state_dir, snapshot, log_file)

        assert result.returncode == 0
        assert "no-op:" in log_file.read_text()
        assert _recorded(calls) == []

    def test_stale_alive_marker_proceeds_and_runs_destructive_steps(self, harness):
        bindir, state_dir, snapshot, log_file, calls = harness
        alive = state_dir / "ALIVE"
        alive.write_text("proof of life\n")
        old = time.time() - 3600
        os.utime(alive, (old, old))

        result = _run_script(bindir, state_dir, snapshot, log_file)

        assert result.returncode == 0
        recorded = _recorded(calls)
        assert "systemctl" in recorded
        assert "nft" in recorded
        assert "iptables-restore" in recorded
        assert "no-op:" not in log_file.read_text()

    def test_no_markers_runs_the_full_restore_sequence(self, harness):
        bindir, state_dir, snapshot, log_file, calls = harness

        result = _run_script(bindir, state_dir, snapshot, log_file)

        assert result.returncode == 0
        recorded = _recorded(calls)
        assert "systemctl" in recorded
        assert "nft" in recorded
        assert "iptables-restore" in recorded
        assert "ip6tables-restore" in recorded


class TestDefaultSnapshotSelection:
    """The dead-man trap invokes the script with no positional snapshot arg.

    restore_firewall.sh must then pick the newest directory under
    $STATE_DIR/snapshots (todo 40). Before this fix the trap would fire into a
    usage error (exit 2) and silently restore nothing.
    """

    @staticmethod
    def _run_no_arg(bindir: Path, state_dir: Path, log_file: Path) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PATH"] = f"{bindir}:{os.environ['PATH']}"
        env["STATE_DIR"] = str(state_dir)
        env["LOG"] = str(log_file)
        proc = _POPEN(
            ["bash", str(SCRIPT), "--no-restart-docker"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        stdout, stderr = proc.communicate(timeout=30)
        return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)

    def test_no_arg_uses_newest_snapshot_directory(self, harness):
        bindir, state_dir, _snapshot, log_file, calls = harness
        snaps = state_dir / "snapshots"
        for name in ("20260101-000000-000000", "20261023-120000-000000"):
            d = snaps / name
            d.mkdir(parents=True)
            (d / "rules.v4").write_text("*filter\nCOMMIT\n")
            (d / "rules.v6").write_text("*filter\nCOMMIT\n")

        result = self._run_no_arg(bindir, state_dir, log_file)

        assert result.returncode == 0, result.stderr
        log = log_file.read_text()
        assert "using newest snapshot" in log
        assert "20261023-120000-000000" in log
        assert "iptables-restore" in _recorded(calls)

    def test_no_arg_and_no_snapshots_fails_closed(self, harness):
        bindir, state_dir, _snapshot, log_file, calls = harness

        result = self._run_no_arg(bindir, state_dir, log_file)

        assert result.returncode == 2
        assert _recorded(calls) == []
        assert "no snapshots" in log_file.read_text()
