"""Shared fixtures for the viswall firewall agent test suite.

Isolation contract (todo 14): no test may touch the host firewall/network.
This is enforced by an autouse guard that replaces every subprocess seam used
by the agent (``asyncio.create_subprocess_exec`` in nft/api/qos/routing and the
sync ``subprocess`` reference inside snapshots) with a function that raises.
Tests that legitimately need a subprocess install the ``subprocess_fake``
fixture (or inject a runner, as routing does) to replace the guard within that
single test.

The ``STATE_DIR`` and ``INSTANCE_API_KEY`` environment variables are pinned
BEFORE ``viswall_firewall_agent.api`` is imported, because that module reads
both at import time. The state dir is a throwaway tmpdir removed at session
end, so no test can write ``/var/lib/viswall-firewall``.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional

import pytest

#: Agent API key every test talks with. Never a real credential.
TEST_INSTANCE_KEY = "vw-test-instance-key"

# api.py reads these at import time; conftest is imported before any test
# module, so pinning here wins over the environment and the defaults.
_STATE_DIR = tempfile.mkdtemp(prefix="vw-fw-test-state-")
os.environ["STATE_DIR"] = _STATE_DIR
os.environ["INSTANCE_API_KEY"] = TEST_INSTANCE_KEY


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    shutil.rmtree(_STATE_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# Subprocess seam fakes
# ---------------------------------------------------------------------------


class ProcResult:
    """Minimal stand-in for an asyncio subprocess Process."""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    async def communicate(self, input: Optional[bytes] = None) -> Any:
        return self.stdout, self.stderr


Predicate = Callable[[List[str]], bool]


class SubprocessFake:
    """Records every spawned command and answers per predicate.

    Unexpected invocations raise AssertionError, so a test can never
    accidentally talk to the real host binaries (and a missed expectation
    fails loudly instead of silently returning a fake success).
    """

    def __init__(self) -> None:
        self.commands: List[List[str]] = []
        self._rules: List[tuple[Predicate, ProcResult]] = []

    def on(
        self,
        predicate: Predicate,
        *,
        rc: int = 0,
        out: bytes = b"",
        err: bytes = b"",
    ) -> None:
        self._rules.append((predicate, ProcResult(rc, out, err)))

    async def __call__(self, binary: str, *args: Any, **kwargs: Any) -> ProcResult:
        command = [str(binary), *[str(arg) for arg in args]]
        self.commands.append(command)
        for predicate, result in self._rules:
            if predicate(command):
                return result
        raise AssertionError(f"unexpected subprocess invocation: {command}")

    def calls(self, binary: str) -> List[List[str]]:
        return [c for c in self.commands if c[0] == binary]


class _BlockedSubprocess:
    """Sync-subprocess stand-in for snapshots: every call raises."""

    CalledProcessError = subprocess.CalledProcessError
    TimeoutExpired = subprocess.TimeoutExpired

    @staticmethod
    def run(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError(
            f"conftest guard: test attempted to spawn a real subprocess: {args!r}"
        )


@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block every real subprocess seam in the agent modules."""

    def _blocked(binary: str, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError(
            f"conftest guard: test attempted to spawn a real subprocess: "
            f"{binary!r} {args!r}"
        )

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", _blocked)

    import viswall_firewall_agent.snapshots as snapshots

    # Replace only the snapshots module's reference, not subprocess globally.
    monkeypatch.setattr(snapshots, "subprocess", _BlockedSubprocess)


@pytest.fixture
def subprocess_fake(monkeypatch: pytest.MonkeyPatch) -> SubprocessFake:
    """Install a scriptable subprocess recorder (replaces the guard)."""
    fake = SubprocessFake()
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake)
    return fake


# ---------------------------------------------------------------------------
# /etc isolation for nft.apply_ruleset (its config path is deliberately fixed)
# ---------------------------------------------------------------------------


@pytest.fixture
def api_state_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point api.py's STATE_DIR at a per-test tmpdir.

    ``STATE_DIR`` is a module global read at call time, so monkeypatching the
    attribute isolates every apply/rollback marker write from other tests.
    """
    from viswall_firewall_agent import api as api_module

    state_dir = tmp_path / "state"
    monkeypatch.setattr(api_module, "STATE_DIR", str(state_dir))
    return state_dir


@pytest.fixture
def fake_etc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect every ``Path("/etc/...")`` inside nft.py into a tmp dir.

    ``apply_ruleset`` hardcodes ``/etc/nftables.conf`` (deliberately inlined so
    no caller can influence the path). Tests must not write the real /etc, so
    the module's ``Path`` symbol is swapped for a subclass that maps the
    ``/etc`` prefix onto ``tmp_path/etc``.
    """
    import pathlib

    import viswall_firewall_agent.nft as nft_module

    etc = tmp_path / "etc"
    etc.mkdir()

    class _RedirectedPath:
        """``Path`` stand-in: maps the /etc prefix onto tmp_path/etc.

        Returns a plain ``pathlib.Path`` for the mapped value — subclassing
        PosixPath with a custom ``__new__`` is unsafe on Python 3.12 (the
        path parser runs in ``__init__`` with the original args).
        """

        _redirect = {"/etc": str(etc)}

        def __new__(cls, *args: Any, **kwargs: Any) -> Path:
            mapped = list(args)
            if mapped:
                first = str(mapped[0])
                for prefix, target in cls._redirect.items():
                    if first == prefix or first.startswith(prefix + "/"):
                        mapped[0] = target + first[len(prefix) :]
                        break
            return pathlib.Path(*mapped, **kwargs)

    monkeypatch.setattr(nft_module, "Path", _RedirectedPath)
    return etc
