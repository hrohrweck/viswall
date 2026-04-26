"""Tests for Viswall CLI."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from viswall_cli.main import app
from viswall_cli.config import Config

runner = CliRunner()


class TestLogin:
    def test_login_success(self, httpx_mock, tmp_path):
        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/auth/login",
            json={"access_token": "test-token", "token_type": "bearer"},
        )

        config_file = tmp_path / "config.yaml"
        result = runner.invoke(
            app,
            [
                "login",
                "--url", "https://viswall.example.com",
                "--username", "admin",
                "--password", "secret",
                "--config", str(config_file),
            ],
        )
        assert result.exit_code == 0
        assert "Logged in" in result.output

    def test_login_failure(self, httpx_mock):
        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/auth/login",
            status_code=401,
            json={"detail": "Invalid credentials"},
        )

        result = runner.invoke(
            app,
            [
                "login",
                "--url", "https://viswall.example.com",
                "--username", "admin",
                "--password", "wrong",
            ],
        )
        assert result.exit_code == 1
        assert "Authentication failed" in result.output


class TestConfig:
    def test_config_show_empty(self, tmp_path):
        config_file = tmp_path / "nonexistent.yaml"
        result = runner.invoke(app, ["config-show", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "No configuration found" in result.output

    def test_config_show_with_env(self, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "my-secret-token")

        result = runner.invoke(app, ["config-show"])
        assert result.exit_code == 0
        assert "https://viswall.example.com" in result.output
        assert "my-secre...oken" in result.output


class TestInstances:
    def test_list_instances(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/instances",
            json=[
                {"id": 1, "name": "edge-01", "hostname": "10.0.0.10", "status": "active"},
            ],
        )

        result = runner.invoke(app, ["instances", "list"])
        assert result.exit_code == 0
        assert "edge-01" in result.output

    def test_create_instance(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/instances",
            method="POST",
            json={"id": 1, "name": "edge-01", "hostname": "10.0.0.10"},
        )

        result = runner.invoke(
            app,
            ["instances", "create", "edge-01", "10.0.0.10"],
        )
        assert result.exit_code == 0
        assert "edge-01" in result.output

    def test_delete_instance_confirm(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/instances/1",
            method="DELETE",
            status_code=204,
        )

        result = runner.invoke(
            app,
            ["instances", "delete", "1", "--yes"],
        )
        assert result.exit_code == 0
        assert "deleted" in result.output


class TestFirewall:
    def test_list_rules(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/firewall/rules/1",
            json=[
                {"id": 1, "name": "allow-ssh", "action": "accept", "chain": "input", "protocol": "tcp", "dst_port": 22},
            ],
        )

        result = runner.invoke(app, ["firewall", "list", "--instance-id", "1"])
        assert result.exit_code == 0
        assert "allow-ssh" in result.output

    def test_create_rule(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/firewall/rules/1",
            method="POST",
            json={"id": 1, "name": "allow-https", "action": "accept"},
        )

        result = runner.invoke(
            app,
            [
                "firewall", "create",
                "--instance-id", "1",
                "--name", "allow-https",
                "--action", "accept",
                "--dst-port", "443",
            ],
        )
        assert result.exit_code == 0
        assert "allow-https" in result.output

    def test_apply_firewall(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/firewall/apply/1",
            method="POST",
            json={"status": "applied"},
        )

        result = runner.invoke(app, ["firewall", "apply", "1"])
        assert result.exit_code == 0
        assert "applied" in result.output


class TestUsers:
    def test_list_users(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/users",
            json=[
                {"id": 1, "username": "admin", "email": "admin@example.com", "role": "admin"},
            ],
        )

        result = runner.invoke(app, ["users", "list"])
        assert result.exit_code == 0
        assert "admin" in result.output


class TestMetrics:
    def test_metrics_latest(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/metrics/latest/1",
            json={"cpu_percent": 45.2, "memory_percent": 62.1},
        )

        result = runner.invoke(app, ["metrics", "latest", "1"])
        assert result.exit_code == 0
        assert "cpu_percent" in result.output

    def test_metrics_overview(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/metrics/overview",
            json={"total_instances": 5, "active_instances": 4},
        )

        result = runner.invoke(app, ["metrics", "overview"])
        assert result.exit_code == 0
        assert "total_instances" in result.output


class TestDHCP:
    def test_list_dhcp_servers(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/dhcp/servers/1",
            json=[{"id": 1, "name": "kea-main", "status": "running", "subnets_count": 2}],
        )

        result = runner.invoke(app, ["dhcp", "servers", "--instance-id", "1"])
        assert result.exit_code == 0
        assert "kea-main" in result.output

    def test_create_dhcp_subnet(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/dhcp/servers/2/subnets",
            method="POST",
            json={"id": 10, "name": "lan-v4", "subnet": "192.168.10.0/24", "type": "v4"},
        )

        result = runner.invoke(
            app,
            [
                "dhcp",
                "subnet-create",
                "--server-id",
                "2",
                "--name",
                "lan-v4",
                "--subnet",
                "192.168.10.0/24",
                "--type",
                "v4",
            ],
        )
        assert result.exit_code == 0
        assert "lan-v4" in result.output

    def test_release_dhcp_lease(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("VISWALL_URL", "https://viswall.example.com")
        monkeypatch.setenv("VISWALL_TOKEN", "token")

        httpx_mock.add_response(
            url="https://viswall.example.com/api/v1/dhcp/leases/55",
            method="DELETE",
            json={"id": 55, "state": "released"},
        )

        result = runner.invoke(app, ["dhcp", "lease-release", "55", "--yes"])
        assert result.exit_code == 0
        assert "released" in result.output
