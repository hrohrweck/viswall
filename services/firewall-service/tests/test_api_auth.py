"""API-surface tests: X-Instance-Key auth matrix + todo-8 endpoint behavior.

Every endpoint except ``/health`` must answer 401 without (or with a wrong)
instance key and 200 with the right one. The 200 paths run against mocked
subprocesses only — the conftest guard turns any accidental real ``nft`` /
``ip`` / ``tc`` invocation into a loud test failure.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from viswall_firewall_agent import api as api_module

#: The same value conftest pinned into the env (api.py captured it at import).
TEST_INSTANCE_KEY = os.environ["INSTANCE_API_KEY"]

TC_STATS_FIXTURE = (
    "qdisc htb 1: root refcnt 2 r2q 10 default 12 direct_packets_stat 0 direct_qlen 1000\n"
    " Sent 1583412 bytes 12007 pkt (dropped 3, overlimits 0 requeues 0)\n"
    " backlog 0b 0p requeues 0\n"
    "qdisc fq_codel 8002: parent 1:10 limit 10240p flows 1024 quantum 1514 target 5ms interval 100ms memory_limit 32Mb ecn drop_batch 64\n"
    " Sent 981234 bytes 8100 pkt (dropped 1, overlimits 0 requeues 0)\n"
    " backlog 0b 0p requeues 0\n"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(api_module.app)


@pytest.fixture
def auth_headers() -> dict:
    return {"X-Instance-Key": TEST_INSTANCE_KEY}


# ---------------------------------------------------------------------------
# Auth matrix
# ---------------------------------------------------------------------------

_ENDPOINTS = [
    ("GET", "/firewall/status", None),
    ("POST", "/firewall/apply", {}),
    ("POST", "/firewall/rollback", None),
    ("POST", "/block", {"ip": "1.2.3.4"}),
    ("POST", "/unblock", {"ip": "1.2.3.4"}),
    (
        "POST",
        "/qos/apply",
        {"interface": "eth0", "algorithm": "cake", "download_kbps": 1000, "upload_kbps": 1000, "classes": []},
    ),
    ("POST", "/qos/clear", {"interface": "eth0"}),
    ("GET", "/qos/stats/eth0", None),
    ("GET", "/stats", None),
]


def test_health_when_unauthenticated(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.parametrize("method,path,body", _ENDPOINTS)
def test_endpoint_401_when_key_missing(
    client: TestClient, method: str, path: str, body: dict | None
) -> None:
    response = client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid instance key"


@pytest.mark.parametrize("method,path,body", _ENDPOINTS)
def test_endpoint_401_when_key_wrong(
    client: TestClient, method: str, path: str, body: dict | None
) -> None:
    response = client.request(method, path, json=body, headers={"X-Instance-Key": "wrong-key"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# todo-8 endpoints with the right key (subprocess mocked)
# ---------------------------------------------------------------------------


def _apply_payload() -> dict:
    return {
        "interfaces": [{"name": "enp0s31f6", "type": "wan"}],
        "rules": [
            {
                "id": 1,
                "name": "ssh limit",
                "source_type": None,
                "source_value": None,
                "dest_type": None,
                "dest_value": None,
                "service_protocol": "tcp",
                "service_ports": "22",
                "action": "drop",
                "limit": "8/minute",
                "order_index": 0,
            }
        ],
        "nat_rules": [],
        "routing_rules": [],
        "qos": None,
    }


def test_firewall_apply_200(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    fake_etc: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_module, "snapshot_state", lambda state_dir: str(Path(state_dir) / "snapshots" / "fake")
    )
    subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-c", rc=0)
    subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
    subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)
    subprocess_fake.on(lambda c: c[0] == "ip", rc=0, out=b"[]")

    response = client.post("/firewall/apply", json=_apply_payload(), headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"applied": True, "validation_mode": False, "errors": []}
    assert ["nft", "delete", "table", "inet", "viswall"] in subprocess_fake.commands
    assert (api_state_dir / "last_applied_at").is_file()


def test_firewall_status_200_with_table(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    subprocess_fake.on(
        lambda c: c[0] == "nft", rc=0, out=b'{"nftables": [{"metainfo": {"version": "1.0.9"}}]}'
    )
    response = client.get("/firewall/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["validation_mode"] is False
    assert body["table_present"] is True
    assert body["nft_dump"]["nftables"][0]["metainfo"]["version"] == "1.0.9"


def test_firewall_status_reports_validation_mode(
    client: TestClient, auth_headers: dict, subprocess_fake, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VALIDATION_MODE", "1")
    subprocess_fake.on(lambda c: c[0] == "nft", rc=1, err=b"no such file")
    response = client.get("/firewall/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["validation_mode"] is True
    assert response.json()["table_present"] is False


def test_firewall_rollback_200_direct_mechanism(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = api_state_dir / "snapshots" / "20261023-000000-000001"
    snapshot.mkdir(parents=True)
    (snapshot / "rules.v4").write_text("*filter\n")
    (snapshot / "rules.v6").write_text("*filter\n")
    monkeypatch.setattr(api_module.shutil, "which", lambda _name: None)
    subprocess_fake.on(lambda c: c[0] == "nft", rc=0)
    subprocess_fake.on(lambda c: c[0].startswith("iptables-restore"), rc=0)
    subprocess_fake.on(lambda c: c[0].startswith("ip6tables-restore"), rc=0)

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["restored"] is True
    assert body["mechanism"] == "direct (snapshot files)"
    assert set(body["restored_artifacts"]) == {
        "rules.v4",
        "rules.v6",
        "nft: table inet viswall removed",
    }


def test_firewall_rollback_500_without_snapshot(
    client: TestClient, auth_headers: dict, api_state_dir: Path
) -> None:
    response = client.post("/firewall/rollback", headers=auth_headers)
    assert response.status_code == 500
    assert "no snapshot available" in response.json()["detail"]


def test_firewall_rollback_409_when_cutover_committed(
    client: TestClient, auth_headers: dict, api_state_dir: Path
) -> None:
    """Post-cutover the newest snapshots carry the STRIPPED iptables; restoring
    one would leave the host unfiltered. COMMIT must disable the console path."""
    api_state_dir.mkdir(parents=True, exist_ok=True)
    (api_state_dir / "COMMIT").write_text("committed\n")

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "cutover is committed" in detail
    assert "cutover-baseline" in detail


def test_firewall_rollback_validates_before_deleting_table(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F2 MAJOR #7: a corrupt capture must fail the --test BEFORE the viswall
    table is deleted — otherwise the delete leaves the host with no firewall."""
    snapshot = api_state_dir / "snapshots" / "20261023-000000-000001"
    snapshot.mkdir(parents=True)
    (snapshot / "rules.v4").write_text("*filter\n")
    (snapshot / "rules.v6").write_text("*filter\nCORRUPT\n")
    monkeypatch.setattr(api_module.shutil, "which", lambda _name: None)
    subprocess_fake.on(
        lambda c: c[0] == "iptables-restore" and "--test" in c, rc=0
    )
    subprocess_fake.on(
        lambda c: c[0] == "ip6tables-restore" and "--test" in c, rc=1, err=b"syntax error"
    )

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 500
    assert "ip6tables-restore --test failed" in response.json()["detail"]
    assert not any("delete" in c for c in subprocess_fake.commands)


def test_firewall_rollback_restore_failure_reapplies_last_good(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F2 MAJOR #7: when iptables-restore fails mid-rollback, the last-good
    nft conf is re-applied so neither firewall stays absent."""
    snapshot = api_state_dir / "snapshots" / "20261023-000000-000001"
    snapshot.mkdir(parents=True)
    (snapshot / "rules.v4").write_text("*filter\n")
    (snapshot / "rules.v6").write_text("*filter\n")
    (api_state_dir / "nftables.conf.last-good").write_text("table inet viswall {}\n")
    monkeypatch.setattr(api_module.shutil, "which", lambda _name: None)
    subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "delete", rc=0)
    subprocess_fake.on(
        lambda c: c[0] == "iptables-restore" and "--test" in c, rc=0
    )
    subprocess_fake.on(
        lambda c: c[0] == "iptables-restore" and "--test" not in c, rc=1, err=b"restore failed"
    )
    subprocess_fake.on(
        lambda c: c[0] == "ip6tables-restore" and "--test" in c, rc=0
    )
    subprocess_fake.on(lambda c: c[0] == "nft" and c[1] == "-f", rc=0)

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 500
    assert "iptables-restore failed" in response.json()["detail"]
    assert any(len(c) > 1 and c[1] == "-f" for c in subprocess_fake.commands)


def test_block_unblock_200(client: TestClient, auth_headers: dict, subprocess_fake) -> None:
    subprocess_fake.on(lambda c: c[0] == "nft", rc=0)
    block = client.post("/block", json={"ip": "1.2.3.4"}, headers=auth_headers)
    assert block.status_code == 200
    assert block.json() == {"success": True, "ip": "1.2.3.4"}

    unblock = client.post("/unblock", json={"ip": "1.2.3.4"}, headers=auth_headers)
    assert unblock.status_code == 200
    assert unblock.json() == {"success": True, "ip": "1.2.3.4"}
    assert ["nft", "add", "element", "inet", "viswall", "blacklist_v4"] in [
        c[:6] for c in subprocess_fake.commands
    ]


def test_block_rejects_invalid_ip_with_422(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    """F2 MAJOR #5: the ip is rendered into an nft element statement."""
    response = client.post(
        "/block", json={"ip": "1.2.3.4; flush ruleset"}, headers=auth_headers
    )
    assert response.status_code == 422
    assert subprocess_fake.commands == []


def test_block_rejects_invalid_timeout_with_422(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    """F2 MAJOR #5: the timeout is rendered into an nft element statement."""
    response = client.post(
        "/block", json={"ip": "1.2.3.4", "timeout": "1h; flush chain input"}, headers=auth_headers
    )
    assert response.status_code == 422
    assert subprocess_fake.commands == []


def test_unblock_rejects_invalid_ip_with_422(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    response = client.post(
        "/unblock", json={"ip": "not-an-ip"}, headers=auth_headers
    )
    assert response.status_code == 422
    assert subprocess_fake.commands == []


def test_block_with_ipv6_uses_blacklist_v6(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    subprocess_fake.on(lambda c: c[0] == "nft", rc=0)
    response = client.post(
        "/block", json={"ip": "2001:db8::1", "timeout": "30m"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert ["nft", "add", "element", "inet", "viswall", "blacklist_v6"] in [
        c[:6] for c in subprocess_fake.commands
    ]
    assert "timeout" in subprocess_fake.commands[0]
    assert "30m" in subprocess_fake.commands[0]


def test_qos_apply_200(client: TestClient, auth_headers: dict, subprocess_fake) -> None:
    subprocess_fake.on(lambda c: c[0] == "tc", rc=0)
    response = client.post(
        "/qos/apply",
        json={
            "interface": "eth0",
            "algorithm": "cake",
            "download_kbps": 1000,
            "upload_kbps": 1000,
            "classes": [],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_qos_apply_422_never_touches_qdisc(client: TestClient, auth_headers: dict) -> None:
    """Malformed classes → 422 and zero tc invocations (conftest guard proves it)."""
    response = client.post(
        "/qos/apply",
        json={
            "interface": "eth0",
            "algorithm": "htb",
            "download_kbps": 1000,
            "upload_kbps": 1000,
            "classes": [{"name": "missing-min-rate"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "min_rate_kbps is required" in response.json()["detail"]


def test_qos_stats_200_contract_shape(
    client: TestClient, auth_headers: dict, subprocess_fake
) -> None:
    subprocess_fake.on(lambda c: c[0] == "tc", rc=0, out=TC_STATS_FIXTURE.encode())
    response = client.get("/qos/stats/eth0", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["interface"] == "eth0"
    assert [q["name"] for q in body["stats"]["queues"]] == ["1:", "8002:"]
    assert body["stats"]["queues"][0]["bytes"] == 1583412
    assert body["stats"]["queues"][0]["packets"] == 12007
    assert body["stats"]["queues"][0]["dropped"] == 3
    assert body["stats"]["raw"].startswith("qdisc htb 1: root")


def test_system_stats_200(client: TestClient, auth_headers: dict, subprocess_fake) -> None:
    subprocess_fake.on(lambda c: c[0] == "nft", rc=0, out=b"{}")
    subprocess_fake.on(lambda c: c[0] == "conntrack", rc=0, out=b"123")
    response = client.get("/stats", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["nftables"] == {}
    assert body["connections"]["tracked"] == 123


def test_firewall_rollback_200_via_script_mechanism(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = api_state_dir / "snapshots" / "20261023-000000-000001"
    snapshot.mkdir(parents=True)
    (snapshot / "rules.v4").write_text("*filter\n")
    (snapshot / "rules.v6").write_text("*filter\n")
    monkeypatch.setattr(api_module.shutil, "which", lambda _name: "/usr/local/sbin/restore_firewall.sh")
    subprocess_fake.on(lambda c: c[0] == api_module.RESTORE_SCRIPT, rc=0)

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["mechanism"] == "restore_firewall.sh"
    assert [api_module.RESTORE_SCRIPT, "--no-restart-docker", str(snapshot)] in subprocess_fake.commands


def test_firewall_rollback_500_when_script_fails(
    client: TestClient,
    auth_headers: dict,
    api_state_dir: Path,
    subprocess_fake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = api_state_dir / "snapshots" / "20261023-000000-000001"
    snapshot.mkdir(parents=True)
    (snapshot / "rules.v4").write_text("*filter\n")
    (snapshot / "rules.v6").write_text("*filter\n")
    monkeypatch.setattr(api_module.shutil, "which", lambda _name: "/usr/local/sbin/restore_firewall.sh")
    subprocess_fake.on(
        lambda c: c[0] == api_module.RESTORE_SCRIPT, rc=1, err=b"restore failed"
    )

    response = client.post("/firewall/rollback", headers=auth_headers)

    assert response.status_code == 500
    assert "rollback failed" in response.json()["detail"]


class TestPayloadConversion:
    def test_parse_service_ports_forms(self) -> None:
        assert api_module._parse_service_ports(None) == []
        assert api_module._parse_service_ports("22") == [22]
        assert api_module._parse_service_ports("8000-8002") == [8000, 8001, 8002]
        assert api_module._parse_service_ports("22,443") == [22, 443]

    def test_parse_service_ports_rejects_garbage_and_overflow(self) -> None:
        assert api_module._parse_service_ports("not-a-port") == []
        assert api_module._parse_service_ports("0") == []
        assert api_module._parse_service_ports("70000") == []
        # range wider than the expansion cap yields [] (protocol-only rule)
        assert api_module._parse_service_ports("8000-9000") == []

    def test_rule_chain_tagging_for_forward_concepts(self) -> None:
        assert api_module._rule_chain("anti-spoof container") == "forward"
        assert api_module._rule_chain("internal-port 11434") == "forward"
        assert api_module._rule_chain("ssh limit") == "input"

    def test_rules_from_payload_expands_service_ports(self) -> None:
        entry = {
            "id": 1,
            "name": "range rule",
            "source_type": None,
            "source_value": None,
            "dest_type": None,
            "dest_value": None,
            "service_protocol": "tcp",
            "service_ports": "8000-8002",
            "action": "accept",
            "order_index": 5,
        }
        rules = api_module._rules_from_payload(entry, 0)
        assert [r.destination_port for r in rules] == [8000, 8001, 8002]
        assert all(r.chain == "input" for r in rules)
        assert all(r.order == 5 for r in rules)

    def test_nat_from_payload_derives_chain_from_type(self) -> None:
        dnat = api_module._nat_from_payload(
            {"id": 1, "name": "mail", "type": "dnat", "to_destination": "172.20.0.10:25"}, 0
        )
        assert dnat.chain == "prerouting"
        snat = api_module._nat_from_payload(
            {"id": 2, "name": "vpn", "type": "snat", "to_source": "46.4.63.216"}, 1
        )
        assert snat.chain == "postrouting"

    def test_nat_from_payload_rejects_newline_injection(self) -> None:
        """F2 MAJOR #4: an injected nft statement fails the apply loudly."""
        from viswall_firewall_agent.api import FirewallApplyError

        with pytest.raises(FirewallApplyError, match="to_destination"):
            api_module._nat_from_payload(
                {
                    "id": 1,
                    "name": "evil",
                    "type": "dnat",
                    "to_destination": "172.20.0.10:25\n        flush chain input",
                },
                0,
            )

    def test_nat_from_payload_rejects_invalid_to_source(self) -> None:
        from viswall_firewall_agent.api import FirewallApplyError

        with pytest.raises(FirewallApplyError, match="to_source"):
            api_module._nat_from_payload(
                {"id": 1, "name": "evil", "type": "snat", "to_source": "not-an-ip"}, 0
            )
