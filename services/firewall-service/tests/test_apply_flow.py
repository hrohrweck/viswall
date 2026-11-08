"""Apply-flow tests (todo 8 QA + todo 14 gate f): validate-before-apply.

The critical safety contract: a ruleset that fails ``nft -c`` must leave the
live table untouched — ``apply_ruleset`` must never reach ``nft delete table
inet viswall`` or ``nft -f`` when validation fails. Proven at two levels:
the ``NFTablesManager.apply_ruleset`` unit and the ``POST /firewall/apply``
HTTP surface (which must turn it into a 500 carrying the exact error).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from viswall_firewall_agent import api as api_module
from viswall_firewall_agent import nft as nft_module
from viswall_firewall_agent.nft import NFTablesManager


@pytest.fixture(autouse=True)
def _pin_unshare(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make apply_ruleset's namespace probe deterministic across hosts/CI."""
    monkeypatch.setattr(
        nft_module.shutil,
        "which",
        lambda name: "/usr/bin/unshare" if name == "unshare" else None,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(api_module.app)


@pytest.fixture
def auth_headers() -> dict:
    # Same value conftest pinned into the env (api.py captured it at import).
    return {"X-Instance-Key": os.environ["INSTANCE_API_KEY"]}


def _ruleset() -> str:
    return NFTablesManager().generate_ruleset(
        interfaces=[{"name": "enp0s31f6", "type": "wan"}],
        firewall_rules=[],
        nat_rules=[],
    )


def _conf_path(fake_etc: Path) -> str:
    return os.path.realpath(str(fake_etc / "nftables.conf"))


class TestApplyRulesetUnit:
    def test_failed_validation_never_deletes_or_applies(
        self, subprocess_fake, fake_etc: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        subprocess_fake.on(
            lambda c: "-c" in c, rc=1, err=b"line 5: syntax error"
        )

        ok = asyncio.run(NFTablesManager().apply_ruleset(_ruleset()))

        assert ok is False
        assert subprocess_fake.commands == [
            ["/usr/bin/unshare", "-n", "true"],
            ["/usr/bin/unshare", "-n", "nft", "-c", "-f", _conf_path(fake_etc)],
        ]

    def test_success_swaps_table_in_order(
        self, subprocess_fake, fake_etc: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        subprocess_fake.on(lambda c: "-c" in c, rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)
        ruleset = _ruleset()

        ok = asyncio.run(NFTablesManager().apply_ruleset(ruleset))

        assert ok is True
        conf = _conf_path(fake_etc)
        assert subprocess_fake.commands == [
            ["/usr/bin/unshare", "-n", "true"],
            ["/usr/bin/unshare", "-n", "nft", "-c", "-f", conf],
            ["nft", "delete", "table", "inet", "viswall"],
            ["nft", "-f", conf],
        ]
        assert (fake_etc / "nftables.conf").read_text() == ruleset

    def test_last_good_saved_before_overwrite(
        self, subprocess_fake, fake_etc: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """F2 MAJOR #7: the previous conf is snapshotted to last-good before
        the new ruleset overwrites /etc/nftables.conf."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        monkeypatch.setenv("STATE_DIR", str(tmp_path))
        (fake_etc / "nftables.conf").write_text("OLD RULESET\n")
        subprocess_fake.on(lambda c: "-c" in c, rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)
        ruleset = _ruleset()

        ok = asyncio.run(NFTablesManager().apply_ruleset(ruleset))

        assert ok is True
        assert (tmp_path / "nftables.conf.last-good").read_text() == "OLD RULESET\n"
        assert (fake_etc / "nftables.conf").read_text() == ruleset

    def test_apply_failure_restores_last_good_and_reapplies(
        self, subprocess_fake, fake_etc: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """F2 MAJOR #7: when ``nft -f`` fails after the delete, the last-good
        conf is written back and re-applied — the host never stays without a
        firewall."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        monkeypatch.setenv("STATE_DIR", str(tmp_path))
        (fake_etc / "nftables.conf").write_text("OLD RULESET\n")
        subprocess_fake.on(lambda c: "-c" in c, rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
        state = {"loads": 0}

        def first_load_fails(command):
            if command[0] == "nft" and command[1] == "-f":
                state["loads"] += 1
                return state["loads"] == 1
            return False

        subprocess_fake.on(first_load_fails, rc=1, err=b"Error: load failed")
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)

        ok = asyncio.run(NFTablesManager().apply_ruleset(_ruleset()))

        assert ok is False
        # The failed load restored last-good and the re-apply ran.
        assert (fake_etc / "nftables.conf").read_text() == "OLD RULESET\n"
        assert [c for c in subprocess_fake.commands if c[1] == "-f"] == [
            ["nft", "-f", _conf_path(fake_etc)],
            ["nft", "-f", _conf_path(fake_etc)],
        ]


class TestApplyFlowHttp:
    def _mock_snapshot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            api_module,
            "snapshot_state",
            lambda state_dir: str(Path(state_dir) / "snapshots" / "fake"),
        )

    def test_apply_500_when_nft_validation_fails_leaves_old_table(
        self,
        client: TestClient,
        auth_headers: dict,
        api_state_dir: Path,
        subprocess_fake,
        fake_etc: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._mock_snapshot(monkeypatch)
        subprocess_fake.on(
            lambda c: "-c" in c, rc=1, err=b"line 5: syntax error"
        )

        response = client.post(
            "/firewall/apply",
            json={"interfaces": [], "rules": [], "nat_rules": [], "routing_rules": []},
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "nftables validation failed: line 5: syntax error"
        # Validate-before-apply proof: only the namespace probe + one `-c` check ran.
        # apply_ruleset validates in the netns (redirected /etc); the API
        # re-checks the class-level CONFIG_PATH for the error detail — both go
        # through the isolated form.
        assert [c for c in subprocess_fake.commands if "-c" in c] == [
            ["/usr/bin/unshare", "-n", "nft", "-c", "-f", _conf_path(fake_etc)],
            ["/usr/bin/unshare", "-n", "nft", "-c", "-f", "/etc/nftables.conf"],
        ]
        assert not any("delete" in c or (c[0] == "nft" and c[1] == "-f") for c in subprocess_fake.commands)
        assert not (api_state_dir / "last_applied_at").exists()

    def test_apply_500_when_payload_conversion_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        api_state_dir: Path,
        subprocess_fake,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._mock_snapshot(monkeypatch)

        response = client.post(
            "/firewall/apply",
            json={"rules": [{"id": 1, "no_name_field": True}]},
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "invalid rule at index 0" in response.json()["detail"]
        assert subprocess_fake.calls("nft") == []

    def test_apply_500_when_snapshot_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        api_state_dir: Path,
        subprocess_fake,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(api_module, "snapshot_state", _raising_snapshot)

        response = client.post(
            "/firewall/apply",
            json={"interfaces": [], "rules": [], "nat_rules": [], "routing_rules": []},
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "snapshot failed" in response.json()["detail"]
        assert subprocess_fake.calls("nft") == []


def _raising_snapshot(state_dir: str) -> str:
    raise OSError("iptables-save: command not found")
