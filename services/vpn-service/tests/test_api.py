"""API-surface tests: X-Instance-Key auth on every endpoint except /health,
apply wiring incl. rollback surfacing as 500, the start/stop Pydantic-body
contract (the body-vs-query regression), and keygen output shape."""

from __future__ import annotations

import base64
import importlib
import os
import secrets
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from viswall_vpn_agent import api as api_module
from viswall_vpn_agent.wg_client import WgClientConfig, WgClientManager, render_config


def _b64_key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


APPLY_BODY = {
    "protocol": "wireguard",
    "name": "site-to-site-base0",
    "address": "10.80.0.2/32",
    "private_key": _b64_key(),
    "endpoint": "46.4.63.216:51820",
    "peer_public_key": _b64_key(),
    "allowed_ips": "10.80.0.0/16",
    "persistent_keepalive": 25,
}

AUTH_PROTECTED = [
    ("POST", "/vpn/apply", APPLY_BODY),
    ("POST", "/vpn/start", {"protocol": "wireguard"}),
    ("POST", "/vpn/stop", {"protocol": "wireguard"}),
    ("GET", "/vpn/status", None),
    ("POST", "/vpn/generate-keys", None),
]


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_systemctl) -> TestClient:
    """TestClient over the real app with a per-test manager bound to tmp_path."""
    mgr = WgClientManager(
        interface="client",
        wg_service="wg-quick@client",
        config_path=tmp_path / "client.conf",
        state_dir=tmp_path / "state",
    )
    monkeypatch.setattr(mgr, "_systemctl", fake_systemctl)
    monkeypatch.setattr(api_module, "manager", mgr)
    return TestClient(api_module.app)


# -- auth matrix ---------------------------------------------------------------


@pytest.mark.parametrize("method,path,body", AUTH_PROTECTED)
def test_endpoint_when_key_missing(client: TestClient, method, path, body) -> None:
    response = client.request(method, path, json=body)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path,body", AUTH_PROTECTED)
def test_endpoint_when_key_wrong(client: TestClient, method, path, body) -> None:
    response = client.request(
        method, path, json=body, headers={"X-Instance-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_health_when_unauthenticated(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "vpn-agent"}


def test_endpoints_when_instance_api_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """INSTANCE_API_KEY unset at import -> 401 everywhere except /health."""
    key = os.environ["INSTANCE_API_KEY"]
    monkeypatch.delenv("INSTANCE_API_KEY", raising=False)
    importlib.reload(api_module)
    try:
        unconfigured = TestClient(api_module.app)
        assert unconfigured.get("/health").status_code == 200
        assert unconfigured.post(
            "/vpn/start", json={"protocol": "wireguard"}
        ).status_code == 401
        assert unconfigured.get("/vpn/status").status_code == 401
    finally:
        monkeypatch.setenv("INSTANCE_API_KEY", key)
        importlib.reload(api_module)


# -- /vpn/apply -----------------------------------------------------------------


def test_apply_when_key_correct_writes_config(
    client: TestClient, instance_key: str, tmp_path: Path
) -> None:
    response = client.post(
        "/vpn/apply", json=APPLY_BODY, headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["applied"] is True
    assert payload["name"] == "site-to-site-base0"
    assert payload["interface"] == "client"
    assert payload["service"] == "wg-quick@client"
    assert payload["config_path"] == str(tmp_path / "client.conf")

    written = Path(payload["config_path"])
    model = WgClientConfig(
        address=APPLY_BODY["address"],
        endpoint=APPLY_BODY["endpoint"],
        peer_public_key=APPLY_BODY["peer_public_key"],
        allowed_ips=APPLY_BODY["allowed_ips"],
        private_key=APPLY_BODY["private_key"],
        persistent_keepalive=APPLY_BODY["persistent_keepalive"],
    )
    assert written.read_text() == render_config(model)
    assert written.stat().st_mode & 0o777 == 0o600


def test_apply_rollback_when_restart_fails(
    client: TestClient, instance_key: str, fake_systemctl, tmp_path: Path
) -> None:
    """Failed apply -> 500, old file restored, unit restarted with it."""
    baseline = dict(APPLY_BODY, endpoint="e1.example:51820")
    ok = client.post(
        "/vpn/apply", json=baseline, headers={"X-Instance-Key": instance_key}
    )
    assert ok.status_code == 200
    good = (tmp_path / "client.conf").read_text()

    fake_systemctl.arm_failure(
        "restart", returncode=1, stderr="simulated restart failure"
    )
    broken = dict(APPLY_BODY, endpoint="e2.example:51820")
    failed = client.post(
        "/vpn/apply", json=broken, headers={"X-Instance-Key": instance_key}
    )
    assert failed.status_code == 500
    assert "restart wg-quick@client exited 1" in failed.json()["detail"]

    assert (tmp_path / "client.conf").read_text() == good
    assert (tmp_path / "client.conf").stat().st_mode & 0o777 == 0o600
    assert [call[0] for call in fake_systemctl.calls] == [
        "restart",
        "restart",
        "restart",
    ]


def test_apply_when_unsupported_protocol(client: TestClient, instance_key: str) -> None:
    response = client.post(
        "/vpn/apply",
        json=dict(APPLY_BODY, protocol="openvpn"),
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 400
    assert "unsupported protocol" in response.json()["detail"]


def test_apply_when_required_field_missing(client: TestClient, instance_key: str) -> None:
    body = {k: v for k, v in APPLY_BODY.items() if k != "endpoint"}
    response = client.post(
        "/vpn/apply", json=body, headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "endpoint"] for error in response.json()["detail"]
    )


# -- /vpn/start + /vpn/stop body contract ---------------------------------------


def test_start_when_body_accepted(
    client: TestClient, instance_key: str, fake_systemctl
) -> None:
    response = client.post(
        "/vpn/start",
        json={"protocol": "wireguard", "name": "client"},
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "action": "start",
        "service": "wg-quick@client",
        "name": "client",
    }
    assert [call[0] for call in fake_systemctl.calls] == ["enable", "start"]


def test_start_when_protocol_only_body_accepted(
    client: TestClient, instance_key: str
) -> None:
    """The gateway's current dispatch sends only {"protocol": ...}."""
    response = client.post(
        "/vpn/start",
        json={"protocol": "wireguard"},
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 200
    assert response.json()["name"] is None


def test_start_when_body_missing_rejected(client: TestClient, instance_key: str) -> None:
    response = client.post(
        "/vpn/start", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 422


def test_start_when_query_param_rejected(client: TestClient, instance_key: str) -> None:
    """Regression: the pre-package agent read `protocol` as a QUERY param and
    the gateway's JSON-body calls 422'd. A query-param-only call must keep
    failing with a missing-body error, never be silently accepted."""
    response = client.post(
        "/vpn/start?protocol=wireguard",
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]
    assert response.json()["detail"][0]["type"] == "missing"


def test_stop_when_body_accepted(
    client: TestClient, instance_key: str, fake_systemctl
) -> None:
    response = client.post(
        "/vpn/stop",
        json={"protocol": "wireguard", "name": "client"},
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 200
    assert response.json()["action"] == "stop"
    assert [call[0] for call in fake_systemctl.calls] == ["disable", "stop"]


def test_start_when_unsupported_protocol(client: TestClient, instance_key: str) -> None:
    response = client.post(
        "/vpn/start",
        json={"protocol": "openvpn"},
        headers={"X-Instance-Key": instance_key},
    )
    assert response.status_code == 400
    assert "unsupported protocol" in response.json()["detail"]


# -- /vpn/status -----------------------------------------------------------------

IP_UP = (
    '[{"ifindex": 42, "ifname": "client", "operstate": "UNKNOWN", '
    '"addr_info": [{"family": "inet6", "local": "fe80::1", "prefixlen": 64}, '
    '{"family": "inet", "local": "10.80.0.2", "prefixlen": 32}]}]'
)

WG_SHOW_UP = """\
interface: client
  listening port: 51820

peer: peerpub
  endpoint: 46.4.63.216:51820
  allowed ips: 10.80.0.0/16
  latest handshake: 1 minute, 15 seconds ago
  transfer: 15.21 GiB received, 3.02 MiB sent
"""


def test_status_when_key_correct(
    client: TestClient, instance_key: str, fake_ip_wg
) -> None:
    fake_ip_wg(ip_stdout=IP_UP, wg_stdout=WG_SHOW_UP)
    response = client.get(
        "/vpn/status", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 200
    assert response.json() == {
        "up": True,
        "interface": "client",
        "address": "10.80.0.2/32",
        "endpoint": "46.4.63.216:51820",
        "latest_handshake_sec": 75,
        "transfer_rx": 16331613143,
        "transfer_tx": 3166699,
        "allowed_ips": "10.80.0.0/16",
    }


def test_status_when_interface_down(
    client: TestClient, instance_key: str, fake_ip_wg
) -> None:
    fake_ip_wg(ip_returncode=1)
    response = client.get(
        "/vpn/status", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 200
    assert response.json()["up"] is False


# -- /vpn/generate-keys -----------------------------------------------------------

PRIVATE_KEY = _b64_key()
PUBLIC_KEY = _b64_key()


def _fake_wg_binary(argv, **kwargs):
    if argv == ["wg", "genkey"]:
        return subprocess.CompletedProcess(argv, 0, stdout=PRIVATE_KEY + "\n", stderr="")
    if argv == ["wg", "pubkey"]:
        return subprocess.CompletedProcess(argv, 0, stdout=PUBLIC_KEY + "\n", stderr="")
    raise AssertionError(f"unexpected argv in test: {argv}")


def test_generate_keys_when_valid_output(
    client: TestClient, instance_key: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api_module.subprocess, "run", _fake_wg_binary)
    response = client.post(
        "/vpn/generate-keys", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["private_key"] == PRIVATE_KEY
    assert body["public_key"] == PUBLIC_KEY
    for key in (body["private_key"], body["public_key"]):
        assert len(key) == 44
        assert api_module._WG_KEY_RE.fullmatch(key)


def test_generate_keys_when_malformed_output(
    client: TestClient, instance_key: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def bad(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout="short\n", stderr="")

    monkeypatch.setattr(api_module.subprocess, "run", bad)
    response = client.post(
        "/vpn/generate-keys", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 500
    assert "malformed key material" in response.json()["detail"]


def test_generate_keys_when_binary_missing(
    client: TestClient, instance_key: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(argv, **kwargs):
        raise FileNotFoundError("no such file: wg")

    monkeypatch.setattr(api_module.subprocess, "run", missing)
    response = client.post(
        "/vpn/generate-keys", headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 500
    assert "cannot execute wg" in response.json()["detail"]


# -- config-value injection guard (F2 BLOCKER #3) ---------------------------


def test_apply_rejects_allowed_ips_newline_injection_with_422(
    client: TestClient, instance_key: str
) -> None:
    """A malicious allowed_ips (newline + PostUp) is rejected before writing."""
    malicious = dict(APPLY_BODY, allowed_ips="10.80.0.0/16\nPostUp = /tmp/pwned")
    response = client.post(
        "/vpn/apply", json=malicious, headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "allowed_ips"] for error in response.json()["detail"]
    )


def test_apply_rejects_malformed_peer_key_with_422(
    client: TestClient, instance_key: str
) -> None:
    body = dict(APPLY_BODY, peer_public_key="not-a-key")
    response = client.post(
        "/vpn/apply", json=body, headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "peer_public_key"]
        for error in response.json()["detail"]
    )


def test_apply_rejects_bad_local_address_with_422(
    client: TestClient, instance_key: str
) -> None:
    body = dict(APPLY_BODY, address="10.80.0.2/33")
    response = client.post(
        "/vpn/apply", json=body, headers={"X-Instance-Key": instance_key}
    )
    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "address"] for error in response.json()["detail"]
    )
