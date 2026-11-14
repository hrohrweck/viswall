"""Unit tests for the node agent's /stats per-interface byte counters."""

from fastapi.testclient import TestClient

import viswall_node_agent.api as api_module
from viswall_node_agent.config import AgentConfig
from viswall_node_agent.payloads import InterfaceCounters
from viswall_node_agent.stats import parse_proc_net_dev

SAMPLE = "\n".join(
    [
        "Inter-|   Receive                                                |  Transmit",
        " face |bytes    packets errs drop fifo frame compressed multicast|"
        "bytes    packets errs drop fifo colls carrier compressed",
        "  lo: 123456789    1000    0    0    0     0          0         0"
        "  987654321    1000    0    0    0     0       0          0",
        "enp0s31f6: 555000111 444000 100 200 0 300 0 400"
        " 666000222 333000 0 0 0 0 0 0",
        "vethabc123: 1000 10 0 0 0 0 0 0 2000 20 0 0 0 0 0 0",
        "",
    ]
)


def make_config(**overrides) -> AgentConfig:
    defaults = {
        "instance_api_key": None,
        "gateway_url": None,
        "instance_id": None,
        "heartbeat_interval": 30.0,
        "api_host": "0.0.0.0",
        "api_port": 8085,
        "host_root": "/host",
        "netplan_dir": "",
        "netplan_file": "60-viswall.yaml",
        "ip_binary": "ip",
        "state_dir": "/tmp/viswall-node-test",
        "nsenter_binary": "nsenter",
        "netplan_binary": "netplan",
        "dbus_system_bus_address": "/run/dbus/system_bus_socket",
        "netplan_try_timeout": 120,
        "try_settle_seconds": 0.0,
        "probe_ssh_port": 22,
        "probe_gateway_url": "http://127.0.0.1:8010/health",
        "probe_ping_target": "46.4.63.193",
        "curl_binary": "curl",
        "ping_binary": "ping",
        "ss_binary": "ss",
        "wan_ip": "46.4.63.216/32",
    }
    defaults.update(overrides)
    return AgentConfig(**defaults)


class TestStatsParser:
    def test_stats_parser_returns_all_interfaces_when_sample_rows_valid(self):
        counters = parse_proc_net_dev(SAMPLE)

        assert [c.name for c in counters] == ["lo", "enp0s31f6", "vethabc123"]
        assert counters[0].rx_bytes == 123456789
        assert counters[0].tx_bytes == 987654321
        assert counters[1].rx_bytes == 555000111
        assert counters[1].tx_bytes == 666000222
        assert counters[2].rx_bytes == 1000
        assert counters[2].tx_bytes == 2000

    def test_stats_parser_skips_malformed_lines_when_separator_or_numbers_bad(self):
        malformed = "\n".join(
            [
                "Inter-|   Receive                                                |"
                "  Transmit",
                " face |bytes    packets errs drop fifo frame compressed multicast|"
                "bytes    packets errs drop fifo colls carrier compressed",
                "garbage line without separator",
                "broken: not numbers here at all xyz",
                "  lo: 1 2 3 4 5 6 7 8 9",
            ]
        )

        counters = parse_proc_net_dev(malformed)

        assert [c.name for c in counters] == ["lo"]
        assert counters[0].rx_bytes == 1
        assert counters[0].tx_bytes == 9

    def test_stats_parser_skips_short_rows_when_fewer_than_nine_fields(self):
        short = "\n".join(
            [
                "Inter-|   Receive                                                |"
                "  Transmit",
                " face |bytes    packets errs drop fifo frame compressed multicast|"
                "bytes    packets errs drop fifo colls carrier compressed",
                "tiny: 5 10 0 0",
                "  lo: 1 2 3 4 5 6 7 8 9",
            ]
        )

        counters = parse_proc_net_dev(short)

        assert [c.name for c in counters] == ["lo"]


class TestStatsEndpoint:
    def test_stats_endpoint_returns_401_when_key_wrong_or_missing(self, monkeypatch):
        cfg = make_config(instance_api_key="secret-key")
        monkeypatch.setattr(api_module, "config", cfg)

        client = TestClient(api_module.app)
        wrong = client.get(
            "/stats", headers={"X-Instance-Key": "not-the-key"}
        )
        missing = client.get("/stats")

        assert wrong.status_code == 401
        assert wrong.json() == {"detail": "invalid instance key"}
        assert missing.status_code == 401
        assert missing.json() == {"detail": "invalid instance key"}

    def test_stats_endpoint_returns_503_when_key_unconfigured(self, monkeypatch):
        cfg = make_config(instance_api_key=None)
        monkeypatch.setattr(api_module, "config", cfg)

        client = TestClient(api_module.app)
        response = client.get("/stats", headers={"X-Instance-Key": "anything"})

        assert response.status_code == 503
        assert "INSTANCE_API_KEY not configured" in response.json()["detail"]

    def test_stats_endpoint_returns_counters_when_key_correct(self, monkeypatch):
        cfg = make_config(instance_api_key="secret-key")
        monkeypatch.setattr(api_module, "config", cfg)
        expected = [
            InterfaceCounters(name="lo", rx_bytes=1, tx_bytes=2),
            InterfaceCounters(name="enp0s31f6", rx_bytes=3, tx_bytes=4),
        ]

        def fake_read():
            return expected

        monkeypatch.setattr(api_module, "read_interface_counters", fake_read)

        client = TestClient(api_module.app)
        response = client.get(
            "/stats", headers={"X-Instance-Key": "secret-key"}
        )

        assert response.status_code == 200
        assert response.json() == {
            "interfaces": [
                {"name": "lo", "rx_bytes": 1, "tx_bytes": 2},
                {"name": "enp0s31f6", "rx_bytes": 3, "tx_bytes": 4},
            ]
        }

    def test_stats_endpoint_returns_500_when_reader_raises_oserror(self, monkeypatch):
        cfg = make_config(instance_api_key="secret-key")
        monkeypatch.setattr(api_module, "config", cfg)

        def failing_read():
            raise OSError("[Errno 2] No such file or directory: '/proc/net/dev'")

        monkeypatch.setattr(api_module, "read_interface_counters", failing_read)

        client = TestClient(api_module.app)
        response = client.get(
            "/stats", headers={"X-Instance-Key": "secret-key"}
        )

        assert response.status_code == 500
        assert "/proc/net/dev" in response.json()["detail"]

    def test_health_endpoint_stays_unauthenticated_when_no_key_sent(self, monkeypatch):
        cfg = make_config(instance_api_key="secret-key")
        monkeypatch.setattr(api_module, "config", cfg)

        client = TestClient(api_module.app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
