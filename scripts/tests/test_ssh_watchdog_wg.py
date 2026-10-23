"""Regression tests for the ssh_watchdog WG probe (plan todo 40).

The probe runs `wg show client latest-handshakes`, whose machine output is
"<pubkey>\\t<epoch>" — it never prints the human-readable "latest handshake"
phrase. The original implementation grepped for that phrase, so the WG probe
always failed, the sliding window never re-armed, and the armed revert trap
fired spuriously after its window.

Isolation: every mutating/network binary is a logging shim on PATH; the drift
reference is absent (documented "not yet armed" path), so only the WG parsing
and the overall proof gate are exercised.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ssh_watchdog.sh"

_POPEN = subprocess.Popen


def _shims(bindir: Path, log: Path, wg_body: str) -> None:
    bindir.mkdir(parents=True, exist_ok=True)
    bodies = {
        "ssh": "exit 0\n",
        "curl": "exit 0\n",
        "wg": wg_body,
        "systemctl": f"echo systemctl >> '{log}'\nprintf '%s\\n' \"$@\" >> '{log}'\nexit 0\n",
        "systemd-run": f"echo systemd-run >> '{log}'\nprintf '%s\\n' \"$@\" >> '{log}'\nexit 0\n",
        "nft": "printf '%s\\n' '{\"nftables\":[{\"table\":{\"family\":\"inet\",\"name\":\"viswall\"}}]}'\n",
    }
    for name, body in bodies.items():
        p = bindir / name
        p.write_text("#!/bin/sh\n" + body)
        p.chmod(0o755)


def _run(bindir: Path, state: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{bindir}:{os.environ['PATH']}",
            "STATE_DIR": str(state),
            "REFERENCE_FILE": str(state / "absent.ref"),
            "SSH_KEY": str(state / "dummy_key"),
            "SSH_TARGET": "root@127.0.0.1",
            "MAX_CYCLES": "1",
            "INTERVAL": "0",
        }
    )
    if extra_env:
        env.update(extra_env)
    proc = _POPEN(
        ["bash", str(SCRIPT), "--dry-run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    out, err = proc.communicate(timeout=60)
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def test_machine_latest_handshakes_is_parsed(tmp_path: Path) -> None:
    bindir, state, log = tmp_path / "bin", tmp_path / "state", tmp_path / "calls.log"
    state.mkdir()
    _shims(bindir, log, 'printf \'PUBKEY\\t%s\\n\' "$(date +%s)"\n')

    result = _run(bindir, state)

    assert result.returncode == 0
    log_text = result.stderr
    assert "check wg: OK" in log_text, log_text
    assert "proof FAILED" not in log_text, log_text
    assert "[DRY-RUN] would run:" in log_text


def test_epoch_zero_counts_as_no_handshake(tmp_path: Path) -> None:
    bindir, state, log = tmp_path / "bin", tmp_path / "state", tmp_path / "calls.log"
    state.mkdir()
    _shims(bindir, log, "printf 'PUBKEY\\t0\\n'\n")

    result = _run(bindir, state)

    assert result.returncode == 0
    assert "check wg: FAIL (no handshake recorded — epoch 0)" in result.stderr
    assert "proof FAILED" in result.stderr


def test_stale_handshake_fails_the_window(tmp_path: Path) -> None:
    bindir, state, log = tmp_path / "bin", tmp_path / "state", tmp_path / "calls.log"
    state.mkdir()
    _shims(bindir, log, 'printf \'PUBKEY\\t%s\\n\' "$(( $(date +%s) - 600 ))"\n')

    result = _run(bindir, state)

    assert "check wg: FAIL (handshake age" in result.stderr
    assert "proof FAILED" in result.stderr
