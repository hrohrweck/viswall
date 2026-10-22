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
from viswall_firewall_agent.nft import NFTablesManager


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
            lambda c: c[0] == "nft" and c[1] == "-c", rc=1, err=b"line 5: syntax error"
        )

        ok = asyncio.run(NFTablesManager().apply_ruleset(_ruleset()))

        assert ok is False
        assert subprocess_fake.commands == [["nft", "-c", "-f", _conf_path(fake_etc)]]

    def test_success_swaps_table_in_order(
        self, subprocess_fake, fake_etc: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-c", rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
        subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)
        ruleset = _ruleset()

        ok = asyncio.run(NFTablesManager().apply_ruleset(ruleset))

        assert ok is True
        conf = _conf_path(fake_etc)
        assert subprocess_fake.commands == [
            ["nft", "-c", "-f", conf],
            ["nft", "delete", "table", "inet", "viswall"],
            ["nft", "-f", conf],
        ]
        assert (fake_etc / "nftables.conf").read_text() == ruleset


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
            lambda c: c[0] == "nft" and c[1] == "-c", rc=1, err=b"line 5: syntax error"
        )

        response = client.post(
            "/firewall/apply",
            json={"interfaces": [], "rules": [], "nat_rules": [], "routing_rules": []},
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "nftables validation failed: line 5: syntax error"
        # Validate-before-apply proof: only the two `-c` checks ran.
        assert all(c[1] == "-c" for c in subprocess_fake.calls("nft"))
        assert not any("delete" in c or c[1] == "-f" for c in subprocess_fake.commands)
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
