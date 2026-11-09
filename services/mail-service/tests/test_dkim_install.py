"""Tests for the mail agent /dkim/install endpoint (multi-domain DKIM)."""
import os
import stat

import pytest
from fastapi.testclient import TestClient

import mail_agent

INSTANCE_KEY = "test-instance-key"
VALID_PAYLOAD = {
    "domain": "example.test",
    "selector": "viswall",
    "private_key_pem": "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----\n",
}


@pytest.fixture()
def env(monkeypatch, tmp_path):
    """Agent with the instance key set and both key dirs pointed at tmp_path."""
    staging = tmp_path / "dkim-staging"
    exim = tmp_path / "exim-dkim"
    monkeypatch.setattr(mail_agent, "INSTANCE_API_KEY", INSTANCE_KEY)
    monkeypatch.setattr(mail_agent, "DKIM_STAGING_DIR", str(staging))
    monkeypatch.setattr(mail_agent, "EXIM_DKIM_DIR", str(exim))
    return staging, exim


class TestDkimInstallAuth:
    def test_instance_key_unset_returns_503(self, monkeypatch):
        monkeypatch.setattr(mail_agent, "INSTANCE_API_KEY", None)
        client = TestClient(mail_agent.app)
        response = client.post("/dkim/install", json=VALID_PAYLOAD)
        assert response.status_code == 503

    def test_wrong_instance_key_returns_401(self, env):
        client = TestClient(mail_agent.app)
        response = client.post(
            "/dkim/install", json=VALID_PAYLOAD, headers={"X-Instance-Key": "wrong"}
        )
        assert response.status_code == 401
        staging, exim = env
        assert not staging.exists()
        assert not exim.exists()


class TestDkimInstall:
    def test_valid_install_writes_per_domain_key_and_hups_exim(self, env, monkeypatch):
        staging, exim = env
        calls = []
        monkeypatch.setattr(mail_agent, "_run", lambda cmd, timeout=30: calls.append(cmd) or (0, ""))

        client = TestClient(mail_agent.app)
        response = client.post(
            "/dkim/install", json=VALID_PAYLOAD, headers={"X-Instance-Key": INSTANCE_KEY}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["reloaded"] is True

        staging_key = staging / "example.test.private"
        exim_key = exim / "example.test.private"
        assert body["path"] == str(staging_key)
        assert body["exim_path"] == str(exim_key)

        for key in (staging_key, exim_key):
            assert key.read_text() == VALID_PAYLOAD["private_key_pem"]
            assert stat.S_IMODE(os.stat(key).st_mode) == 0o400

        assert ["pkill", "-HUP", "-x", "exim4"] in calls
        assert ["chown", "Debian-exim:Debian-exim", str(staging_key)] in calls
        assert ["chown", "Debian-exim:Debian-exim", str(exim_key)] in calls

    def test_second_domain_gets_its_own_key_file(self, env, monkeypatch):
        staging, exim = env
        monkeypatch.setattr(mail_agent, "_run", lambda cmd, timeout=30: (0, ""))
        client = TestClient(mail_agent.app)
        headers = {"X-Instance-Key": INSTANCE_KEY}

        first = dict(VALID_PAYLOAD)
        second = dict(VALID_PAYLOAD, domain="other.test")
        assert client.post("/dkim/install", json=first, headers=headers).status_code == 200
        assert client.post("/dkim/install", json=second, headers=headers).status_code == 200

        assert (staging / "example.test.private").exists()
        assert (staging / "other.test.private").exists()
        assert (exim / "example.test.private").exists()
        assert (exim / "other.test.private").exists()

    def test_hostile_selector_rejected(self, env, monkeypatch):
        staging, exim = env
        wrote = []
        monkeypatch.setattr(mail_agent, "_run", lambda cmd, timeout=30: wrote.append(cmd) or (0, ""))
        client = TestClient(mail_agent.app)
        headers = {"X-Instance-Key": INSTANCE_KEY}

        for selector in ("../../evil", "/etc/evil", ".."):
            payload = dict(VALID_PAYLOAD, selector=selector)
            response = client.post("/dkim/install", json=payload, headers=headers)
            assert response.status_code in (400, 422), selector

        assert not staging.exists()
        assert not exim.exists()
        assert not wrote

    def test_hostile_domain_rejected(self, env, monkeypatch):
        staging, exim = env
        wrote = []
        monkeypatch.setattr(mail_agent, "_run", lambda cmd, timeout=30: wrote.append(cmd) or (0, ""))
        client = TestClient(mail_agent.app)
        headers = {"X-Instance-Key": INSTANCE_KEY}

        for domain in ("../../etc/cron.d/evil", "a..b", "..", ".hidden.test"):
            payload = dict(VALID_PAYLOAD, domain=domain)
            response = client.post("/dkim/install", json=payload, headers=headers)
            assert response.status_code in (400, 422), domain

        assert not staging.exists()
        assert not exim.exists()
        assert not wrote
