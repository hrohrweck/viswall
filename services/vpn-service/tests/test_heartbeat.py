"""Heartbeat contract tests: URL shape and the body
``{"api_key": ..., "status": "ok"}`` against a synchronous fake gateway."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from viswall_vpn_agent import heartbeat as hb
from viswall_vpn_agent.main import AgentConfig


class _RecordingHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        self.server.requests.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "body": json.loads(self.rfile.read(length) or b"{}"),
            }
        )
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: object) -> None:  # silence stderr
        return


@pytest.fixture
def fake_gateway():
    """A synchronous ThreadingHTTPServer that records every POST."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RecordingHandler)
    server.requests: list[dict] = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _config(base_url: str) -> AgentConfig:
    return AgentConfig(
        instance_api_key="hb-test-key",
        gateway_url=base_url,
        instance_id=7,
        port=8083,
        state_dir=Path("/tmp/unused"),
        wg_service="wg-quick@client",
    )


def test_heartbeat_url() -> None:
    config = _config("http://127.0.0.1:18086/")  # trailing slash must not double
    assert (
        hb.heartbeat_url(config)
        == "http://127.0.0.1:18086/api/v1/instances/7/heartbeat"
    )


def test_post_heartbeat_when_gateway_up(fake_gateway) -> None:
    url = f"http://127.0.0.1:{fake_gateway.server_address[1]}"
    status = hb._post_heartbeat(hb.heartbeat_url(_config(url)), "hb-test-key")
    assert status == 200
    assert len(fake_gateway.requests) == 1
    request = fake_gateway.requests[0]
    assert request["path"] == "/api/v1/instances/7/heartbeat"
    assert request["content_type"] == "application/json"
    assert request["body"] == {"api_key": "hb-test-key", "status": "ok"}


def test_heartbeat_loop_posts_repeatedly(
    monkeypatch: pytest.MonkeyPatch, fake_gateway
) -> None:
    """Two successful posts, then a non-network error ends the loop — proving
    the loop really posts to the gateway with the env-derived key."""
    url = f"http://127.0.0.1:{fake_gateway.server_address[1]}"
    config = _config(url)
    posts: list[tuple[str, str]] = []

    def fake_post(target_url: str, api_key: str) -> int:
        posts.append((target_url, api_key))
        if len(posts) >= 2:
            raise RuntimeError("terminate loop")
        return 200

    monkeypatch.setattr(hb, "_post_heartbeat", fake_post)
    monkeypatch.setattr(hb, "HEARTBEAT_INTERVAL", 0.0)

    with pytest.raises(RuntimeError, match="terminate loop"):
        asyncio.run(hb.heartbeat_loop(config))

    assert posts == [(hb.heartbeat_url(config), "hb-test-key")] * 2
