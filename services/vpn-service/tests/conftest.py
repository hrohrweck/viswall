"""Shared fixtures for the vpn-service agent tests.

Environment is pinned here BEFORE any test module imports
``viswall_vpn_agent``: ``api.py`` reads ``INSTANCE_API_KEY``, ``WG_CONF_DIR``
and ``STATE_DIR`` at import time, and conftest is loaded by pytest ahead of
every test module. The pinned values point at a session scratch dir — never
``/etc/wireguard``, never ``/var/lib/viswall-vpn`` — so no test can touch the
host's real WireGuard config.

All subprocess work (nsenter/systemctl/wg/ip) is faked in-process or via PATH
shadow scripts; nothing here mutates the host.
"""

from __future__ import annotations

import atexit
import os
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

_SCRATCH = Path(tempfile.mkdtemp(prefix="vw-vpn-tests-"))
atexit.register(shutil.rmtree, _SCRATCH, ignore_errors=True)

# Set BEFORE viswall_vpn_agent is imported (import-time env reads).
os.environ["INSTANCE_API_KEY"] = "vw-test-" + secrets.token_hex(16)
os.environ["WG_CONF_DIR"] = str(_SCRATCH / "wgconf")
os.environ["STATE_DIR"] = str(_SCRATCH / "state")

from viswall_vpn_agent.wg_client import WgClientManager  # noqa: E402


@pytest.fixture
def instance_key() -> str:
    """The key the auth middleware captured at import (== the env value)."""
    return os.environ["INSTANCE_API_KEY"]


class FakeSystemctl:
    """In-process replacement for ``WgClientManager._systemctl``.

    Records every argv and can be armed to fail a specific action (first
    argv token), so the rollback path can be exercised deterministically.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self._failures: dict[str, tuple[int, str]] = {}

    def arm_failure(
        self,
        action: str,
        returncode: int = 1,
        stderr: str = "fake systemctl: simulated failure",
    ) -> None:
        self._failures[action] = (returncode, stderr)

    def __call__(self, *args: str) -> subprocess.CompletedProcess[str]:
        self.calls.append(args)
        returncode, stderr = self._failures.get(args[0], (0, ""))
        return subprocess.CompletedProcess(
            list(args), returncode, stdout="", stderr=stderr
        )


@pytest.fixture
def fake_systemctl() -> FakeSystemctl:
    return FakeSystemctl()


@pytest.fixture
def manager(tmp_path: Path) -> WgClientManager:
    """Manager bound to a per-test scratch dir, never the host paths."""
    return WgClientManager(
        interface="client",
        wg_service="wg-quick@client",
        config_path=tmp_path / "client.conf",
        state_dir=tmp_path / "state",
    )


@pytest.fixture
def managed(
    manager: WgClientManager,
    fake_systemctl: FakeSystemctl,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[WgClientManager, FakeSystemctl]:
    """Manager whose ``_systemctl`` is the recorder, plus the recorder."""
    monkeypatch.setattr(manager, "_systemctl", fake_systemctl)
    return manager, fake_systemctl


def _completed(
    argv: list[str], returncode: int, stdout: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")


class FakeIpWg:
    """Dispatches ``subprocess.run`` for the ``ip``/``wg`` binaries only.

    Any other argv raises — a test that unexpectedly shells out to something
    else (e.g. a real systemctl) must fail loudly, not silently.
    """

    def __init__(
        self,
        ip_stdout: str = "",
        ip_returncode: int = 0,
        wg_stdout: str = "",
        wg_returncode: int = 0,
    ) -> None:
        self.ip_stdout = ip_stdout
        self.ip_returncode = ip_returncode
        self.wg_stdout = wg_stdout
        self.wg_returncode = wg_returncode
        self.wg_calls = 0

    def __call__(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[0] == "ip":
            return _completed(argv, self.ip_returncode, self.ip_stdout)
        if argv[0] == "wg":
            self.wg_calls += 1
            return _completed(argv, self.wg_returncode, self.wg_stdout)
        raise AssertionError(f"unexpected subprocess argv in test: {argv}")


@pytest.fixture
def fake_ip_wg(monkeypatch: pytest.MonkeyPatch):
    """Install a ``FakeIpWg`` for ``wg_client.subprocess.run``.

    Usage: ``fake = fake_ip_wg(ip_stdout=..., wg_stdout=...)`` — returns the
    fake so callers can assert on ``wg_calls``.
    """

    def install(
        ip_stdout: str = "",
        ip_returncode: int = 0,
        wg_stdout: str = "",
        wg_returncode: int = 0,
    ) -> FakeIpWg:
        fake = FakeIpWg(ip_stdout, ip_returncode, wg_stdout, wg_returncode)
        monkeypatch.setattr(
            "viswall_vpn_agent.wg_client.subprocess.run", fake
        )
        return fake

    return install


@pytest.fixture
def shadow_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """PATH with fake ``nsenter``/``systemctl`` executables.

    Exercises the REAL ``WgClientManager._systemctl`` subprocess chain
    (``nsenter -t 1 -m -u -i -n -- systemctl ...``) without touching the
    host. Each fake appends its argv to ``$VW_CALL_LOG``.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"

    (bin_dir / "nsenter").write_text(
        "#!/bin/sh\n"
        "echo \"$@\" >> \"$VW_CALL_LOG\"\n"
        "systemctl \"$@\"\n"
    )
    (bin_dir / "systemctl").write_text(
        "#!/bin/sh\n"
        "echo \"systemctl $@\" >> \"$VW_CALL_LOG\"\n"
        "exit 0\n"
    )
    for name in ("nsenter", "systemctl"):
        (bin_dir / name).chmod(0o755)

    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("VW_CALL_LOG", str(log))
    return log
