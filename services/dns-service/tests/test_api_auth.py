"""API-surface tests: X-Instance-Key auth and apply wiring."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from viswall_dns_agent import api as api_module
from viswall_dns_agent.agent import DNSAgent
from viswall_dns_agent.config import AgentConfig


def _config(tmp_path, api_key: str | None, allow_commands: bool = False) -> AgentConfig:
    return AgentConfig(
        named_conf_path=str(tmp_path / "named.conf.local"),
        named_options_path=str(tmp_path / "named.conf.options"),
        zones_dir=str(tmp_path / "zones"),
        keys_dir=str(tmp_path / "keys"),
        allow_commands=allow_commands,
        instance_api_key=api_key,
        gateway_url=None,
        instance_id=None,
        heartbeat_interval=30,
        api_host="127.0.0.1",
        api_port=8082,
    )


@pytest.fixture
def client(tmp_path, monkeypatch):
    cfg = _config(tmp_path, api_key="placeholder-key")
    monkeypatch.setattr(api_module, "config", cfg)
    monkeypatch.setattr(api_module, "agent", DNSAgent(cfg))
    return TestClient(api_module.app)


def _payload() -> dict:
    return {
        "server_id": 1,
        "name": "node0-dns",
        "is_recursive": False,
        "allow_transfer": ["93.111.66.28"],
        "also_notify": ["93.111.66.28"],
        "zones": [
            {
                "id": 1,
                "name": "example.com",
                "zone_type": "master",
                "serial": 2026090512,
                "refresh": 3600,
                "retry": 600,
                "expire": 86400,
                "minimum_ttl": 3600,
                "records": [
                    {
                        "name": "@",
                        "record_type": "SOA",
                        "content": "dns1.example.com. admin.example.com. 2026090512 3600 600 86400 3600",
                    }
                ],
            }
        ],
    }


def test_health_when_unauthenticated(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["auth_configured"] is True


def test_apply_when_key_missing(client) -> None:
    response = client.post("/dns/apply", json=_payload())
    assert response.status_code == 401


def test_apply_when_key_wrong(client) -> None:
    response = client.post(
        "/dns/apply", json=_payload(), headers={"X-Instance-Key": "wrong"}
    )
    assert response.status_code == 401


def test_apply_when_key_correct_writes_config(client) -> None:
    response = client.post(
        "/dns/apply", json=_payload(), headers={"X-Instance-Key": "placeholder-key"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    options = (api_module.agent.named_options_path).read_text()
    local = (api_module.agent.named_conf_path).read_text()
    assert "recursion no;" in options
    assert 'zone "example.com" {' in local


def test_reload_when_key_missing(client) -> None:
    response = client.post("/dns/reload")
    assert response.status_code == 401


def test_status_when_key_missing(client) -> None:
    response = client.get("/dns/status")
    assert response.status_code == 401


def test_mutations_when_api_key_not_configured(tmp_path, monkeypatch) -> None:
    cfg = _config(tmp_path, api_key=None)
    monkeypatch.setattr(api_module, "config", cfg)
    monkeypatch.setattr(api_module, "agent", DNSAgent(cfg))
    unconfigured = TestClient(api_module.app)
    response = unconfigured.post("/dns/apply", json=_payload())
    assert response.status_code == 503
    assert "INSTANCE_API_KEY" in response.json()["detail"]
