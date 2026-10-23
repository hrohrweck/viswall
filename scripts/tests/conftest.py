"""Shared fixtures for the legacy importer test suite (plan todo 37).

Isolation contract — the suite must never touch the live console or the host:

  * no test may open a socket: ``socket.socket`` / ``socket.create_connection``
    are replaced by raising guards via an autouse fixture, so any accidental
    live API call (urllib in the firewall importer, httpx in the interfaces
    importer) fails loudly instead of talking to production;
  * no test may spawn host binaries: ``subprocess.run`` / ``subprocess.Popen``
    are guarded on the interfaces importer's module reference (its live
    discovery shells out to ``ip -j addr`` unless ``--ip-addr-json`` is given);
    the firewall importer has no subprocess seam;
  * all fixtures are committed trimmed copies of the REAL todo-3 live captures
    under ``scripts/tests/fixtures/`` — the suite never reads
    ``/data/docker/persistent/backup/...`` so it runs in CI containers too.
    The WireGuard key material in the fixture is REGENERATED FAKE (zero-entropy
    placeholders in the 44-char base64 shape of a real wg key), never the
    production key.
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = FIXTURES.parent.parent

if str(SCRIPTS_DIR) not in sys.path:  # make `import migrate_legacy_*` work
    sys.path.insert(0, str(SCRIPTS_DIR))

import migrate_legacy_firewall as fw
import migrate_legacy_interfaces as ifaces

#: Regenerated fake WireGuard key material used by the client.conf fixture.
#: Zero-entropy placeholders in the 44-char base64 shape of a real wg key —
#: parseably valid, obviously not a secret, and immune to secret scanners.
FAKE_PRIVATE_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
FAKE_PUBLIC_KEY = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="


# ---------------------------------------------------------------------------
# Autouse isolation guards
# ---------------------------------------------------------------------------


def _network_blocked(*args: object, **kwargs: object) -> None:
    raise AssertionError("importer tests may not open sockets (live API guard)")


@pytest.fixture(autouse=True)
def no_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "socket", _network_blocked)
    monkeypatch.setattr(socket, "create_connection", _network_blocked)


def _subprocess_blocked(*args: object, **kwargs: object) -> None:
    raise AssertionError(f"importer tests may not spawn host binaries: {args!r}")


@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch through the interfaces importer's reference so the guard is scoped
    # to the importer seam (subprocess is shared, but only this suite uses it).
    monkeypatch.setattr(ifaces.subprocess, "run", _subprocess_blocked)
    monkeypatch.setattr(ifaces.subprocess, "Popen", _subprocess_blocked)


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def rules_v4() -> Path:
    """Trimmed copy of the REAL todo-3 live v4 capture (313 -A lines)."""
    return FIXTURES / "rules.v4.live"


@pytest.fixture(scope="session")
def rules_v6() -> Path:
    """Trimmed copy of the REAL todo-3 live v6 capture (99 -A lines)."""
    return FIXTURES / "rules.v6.live"


@pytest.fixture(scope="session")
def fw_plan(rules_v4: Path, rules_v6: Path) -> fw.Plan:
    """The parsed import plan for the real capture fixtures."""
    args = argparse.Namespace(rules_file=str(rules_v4), rules6_file=str(rules_v6))
    return fw.build_plan(args)


@pytest.fixture(scope="session")
def netplan_file() -> Path:
    """Real netplan yaml from the todo-3 backup (trimmed copy)."""
    return FIXTURES / "netplan" / "01-netcfg.yaml"


@pytest.fixture(scope="session")
def wg_conf() -> Path:
    """client.conf fixture with REGENERATED FAKE key material."""
    return FIXTURES / "wireguard" / "client.conf"


@pytest.fixture(scope="session")
def fake_wg_keys() -> tuple[str, str]:
    """The (private, public) fake keys the client.conf fixture must contain."""
    return FAKE_PRIVATE_KEY, FAKE_PUBLIC_KEY


@pytest.fixture(scope="session")
def ip_addr_json() -> Path:
    """Trimmed `ip -j addr` capture (lo/enp0s31f6/client/br-/docker0/veth)."""
    return FIXTURES / "ip-addr.json"


# ---------------------------------------------------------------------------
# In-process main() runners
# ---------------------------------------------------------------------------


@pytest.fixture
def run_fw_main(
    monkeypatch: pytest.MonkeyPatch, rules_v4: Path, rules_v6: Path
) -> Callable[..., int]:
    """Run migrate_legacy_firewall.main() in-process against the fixtures.

    Extra args (e.g. ``--dry-run``, ``--import-manifest``) are appended after
    the fixture capture paths; repeating ``--rules-file`` overrides the base.
    """

    def _run(argv: tuple[str, ...] = ()) -> int:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "migrate_legacy_firewall.py",
                "--rules-file",
                str(rules_v4),
                "--rules6-file",
                str(rules_v6),
                *argv,
            ],
        )
        return fw.main()

    return _run


@pytest.fixture
def run_ifaces_main(
    monkeypatch: pytest.MonkeyPatch,
    netplan_file: Path,
    wg_conf: Path,
    ip_addr_json: Path,
) -> Callable[..., int]:
    """Run migrate_legacy_interfaces.main() in-process against the fixtures.

    ``--ip-addr-json`` pins live discovery to the fixture so the ``ip`` binary
    is never invoked (the conftest subprocess guard would fail the test).
    """

    def _run(argv: tuple[str, ...] = ()) -> int:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "migrate_legacy_interfaces.py",
                "--netplan-file",
                str(netplan_file),
                "--wireguard-conf",
                str(wg_conf),
                "--ip-addr-json",
                str(ip_addr_json),
                *argv,
            ],
        )
        return ifaces.main()

    return _run
