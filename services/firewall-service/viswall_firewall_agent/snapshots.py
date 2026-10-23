"""State snapshot helper for the Viswall firewall agent.

Captures the complete host firewall/network state into
``$STATE_DIR/snapshots/<utc-timestamp>/`` (called before every
``/firewall/apply`` and ``/interfaces/apply``), then prunes the snapshots
directory to the newest 10.

The signature is part of the agent contract (``api.py`` imports it):

    def snapshot_state(state_dir: str) -> str   # returns the snapshot dir path

Every artifact is captured independently. A missing or failing tool (e.g.
``wg`` absent on a host without WireGuard) fails only that artifact: the
failure is recorded in the snapshot's ``failures.txt`` and via the ``logging``
logger, and the snapshot itself never raises for a missing tool — one dead
probe must not abort the whole pre-apply safety snapshot.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

KEEP_SNAPSHOTS = 10
NETPLAN_DIR = Path("/etc/netplan")
_COMMAND_TIMEOUT_SEC = 30


def _utc_stamp() -> str:
    """UTC timestamp that sorts lexicographically (``%Y%m%d-%H%M%S-%f``)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


# (output file name, argv) — run read-only against the live host state.
_ARTIFACTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("rules.v4", ("iptables-save",)),
    ("rules.v6", ("ip6tables-save",)),
    ("nft-ruleset.txt", ("nft", "list", "ruleset")),
    ("ip-addr.json", ("ip", "-j", "addr")),
    ("ip-route.json", ("ip", "-j", "route")),
    ("ip-rule.json", ("ip", "-j", "rule")),
    ("tc-qdisc.txt", ("tc", "qdisc", "show")),
    ("wg-show.txt", ("wg", "show")),
)


def _capture_command(snapshot_dir: Path, name: str, argv: tuple[str, ...]) -> None:
    """Run one read-only capture command, stdout to ``snapshot_dir/name``."""
    out_path = snapshot_dir / name
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            check=True,
            timeout=_COMMAND_TIMEOUT_SEC,
        )
    except OSError as exc:
        raise RuntimeError(f"cannot run {argv[0]}: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"{argv[0]} exited {exc.returncode}: {exc.stderr.decode(errors='replace')[:200]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{argv[0]} timed out after {_COMMAND_TIMEOUT_SEC}s") from exc
    out_path.write_bytes(result.stdout)


def _capture_netplan(snapshot_dir: Path) -> None:
    """Copy /etc/netplan into the snapshot."""
    shutil.copytree(NETPLAN_DIR, snapshot_dir / "netplan")


def _prune_old_snapshots(snapshots_root: Path, keep: int) -> None:
    """Remove the oldest snapshot dirs beyond ``keep`` (name-sorted)."""
    entries = sorted(
        (p for p in snapshots_root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    for stale in entries[:-keep] if keep > 0 else entries:
        shutil.rmtree(stale)
        logger.info("pruned old snapshot %s", stale)


def snapshot_state(state_dir: str) -> str:
    """Snapshot live firewall/network state; return the snapshot dir path.

    Captures ``iptables-save``, ``ip6tables-save``, ``nft list ruleset``,
    ``ip -j addr``, ``ip -j route``, ``ip -j rule``, ``tc qdisc show``,
    ``wg show`` and a copy of ``/etc/netplan`` into
    ``<state_dir>/snapshots/<ts>/``. Missing/failing tools are recorded in the
    snapshot's ``failures.txt`` (and the log) instead of raising. Keeps the
    newest ``KEEP_SNAPSHOTS`` snapshots.
    """
    root = Path(state_dir)
    snapshots_root = root / "snapshots"
    snapshot_dir = snapshots_root / _utc_stamp()
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    failures: list[str] = []
    for name, argv in _ARTIFACTS:
        try:
            _capture_command(snapshot_dir, name, argv)
        except RuntimeError as exc:
            failures.append(f"{name}: {exc}")
            logger.warning("snapshot artifact %s failed: %s", name, exc)
    try:
        _capture_netplan(snapshot_dir)
    except (OSError, shutil.Error) as exc:
        failures.append(f"netplan/: {exc}")
        logger.warning("snapshot artifact netplan/ failed: %s", exc)

    if failures:
        (snapshot_dir / "failures.txt").write_text(
            "\n".join(failures) + "\n", encoding="utf-8"
        )
        logger.warning(
            "snapshot %s captured with %d failed artifact(s) — see failures.txt",
            snapshot_dir,
            len(failures),
        )
    else:
        logger.info("snapshot captured: %s", snapshot_dir)

    _prune_old_snapshots(snapshots_root, KEEP_SNAPSHOTS)
    return str(snapshot_dir)
