"""Tests for the Viswall Python SDK."""

import pytest
import httpx
from viswall import ViswallClient, ViswallAPIError, AuthenticationError, NotFoundError


class TestViswallClient:
    """Test the main ViswallClient."""

    def test_client_initialization(self):
        """Test client can be initialized."""
        client = ViswallClient(base_url="https://test.example.com", token="test-token")
        assert client.base_url == "https://test.example.com"
        assert client.token == "test-token"
        client.close()

    def test_client_context_manager(self):
        """Test client works as context manager."""
        with ViswallClient(base_url="https://test.example.com") as client:
            assert client.base_url == "https://test.example.com"

    def test_auth_header_set(self):
        """Test auth header is set when token provided."""
        client = ViswallClient(base_url="https://test.example.com", token="jwt123")
        assert client._client.headers["Authorization"] == "Bearer jwt123"
        client.close()


class TestErrorHandling:
    """Test error handling."""

    def test_handle_401(self):
        """Test 401 raises AuthenticationError."""
        client = ViswallClient(base_url="https://test.example.com")
        response = httpx.Response(401, json={"detail": "Unauthorized"})
        with pytest.raises(AuthenticationError):
            client._handle_error(response)
        client.close()

    def test_handle_404(self):
        """Test 404 raises NotFoundError."""
        client = ViswallClient(base_url="https://test.example.com")
        response = httpx.Response(404, json={"detail": "Not found"})
        with pytest.raises(NotFoundError):
            client._handle_error(response)
        client.close()

    def test_handle_500(self):
        """Test 500 raises ViswallAPIError."""
        client = ViswallClient(base_url="https://test.example.com")
        response = httpx.Response(500, json={"detail": "Server error"})
        with pytest.raises(ViswallAPIError) as exc_info:
            client._handle_error(response)
        assert exc_info.value.status_code == 500
        client.close()


class TestAuthResource:
    """Test AuthResource."""

    def test_login(self, httpx_mock):
        """Test login endpoint."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/auth/login",
            method="POST",
            json={"access_token": "token123", "token_type": "bearer"},
        )
        
        client = ViswallClient(base_url="https://test.example.com")
        result = client.auth.login("admin", "password")
        assert result["access_token"] == "token123"
        client.close()

    def test_me(self, httpx_mock):
        """Test me endpoint."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/auth/me",
            method="GET",
            json={"id": 1, "username": "admin"},
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.auth.me()
        assert result["username"] == "admin"
        client.close()


class TestInstancesResource:
    """Test InstancesResource."""

    def test_list_instances(self, httpx_mock):
        """Test list instances."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/instances",
            method="GET",
            json=[{"id": 1, "name": "edge-01"}],
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.instances.list()
        assert len(result) == 1
        assert result[0]["name"] == "edge-01"
        client.close()

    def test_create_instance(self, httpx_mock):
        """Test create instance."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/instances",
            method="POST",
            status_code=201,
            json={"id": 1, "name": "edge-01", "hostname": "10.0.0.10"},
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.instances.create(name="edge-01", hostname="10.0.0.10")
        assert result["id"] == 1
        client.close()


class TestFirewallResource:
    """Test FirewallResource."""

    def test_list_rules(self, httpx_mock):
        """Test list firewall rules."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/firewall/rules/1",
            method="GET",
            json=[{"id": 1, "name": "Allow HTTPS"}],
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.firewall.list_rules(instance_id=1)
        assert len(result) == 1
        client.close()

    def test_create_rule(self, httpx_mock):
        """Test create firewall rule."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/firewall/rules/1",
            method="POST",
            status_code=201,
            json={"id": 1, "name": "Allow SSH", "action": "accept"},
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.firewall.create_rule(
            instance_id=1,
            name="Allow SSH",
            action="accept",
            protocol="tcp",
            dst_port=22,
        )
        assert result["action"] == "accept"
        client.close()


class TestMailResource:
    """Test MailResource."""

    def test_create_domain(self, httpx_mock):
        """Test create mail domain."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/mail/domains/1",
            method="POST",
            status_code=201,
            json={"id": 5, "domain": "example.com"},
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.mail.create_domain(instance_id=1, domain="example.com")
        assert result["domain"] == "example.com"
        client.close()

    def test_list_users(self, httpx_mock):
        """Test list mail users."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/mail/users/5",
            method="GET",
            json=[{"id": 1, "username": "john"}],
        )
        
        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.mail.list_users(domain_id=5)
        assert len(result) == 1
        client.close()


class TestDHCPResource:
    """Test DHCPResource."""

    def test_list_servers(self, httpx_mock):
        """Test list DHCP servers."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/dhcp/servers/1",
            method="GET",
            json=[{"id": 1, "name": "kea-main"}],
        )

        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.dhcp.list_servers(instance_id=1)
        assert len(result) == 1
        assert result[0]["name"] == "kea-main"
        client.close()

    def test_create_subnet(self, httpx_mock):
        """Test create DHCP subnet."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/dhcp/servers/1/subnets",
            method="POST",
            status_code=201,
            json={"id": 11, "name": "lan-v4", "subnet": "192.168.10.0/24", "type": "v4"},
        )

        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.dhcp.create_subnet(
            server_id=1,
            name="lan-v4",
            subnet="192.168.10.0/24",
            type="v4",
            lease_time_min=300,
            lease_time_default=3600,
            lease_time_max=7200,
        )
        assert result["id"] == 11
        client.close()

    def test_release_lease(self, httpx_mock):
        """Test release DHCP lease."""
        httpx_mock.add_response(
            url="https://test.example.com/api/v1/dhcp/leases/99",
            method="DELETE",
            json={"id": 99, "state": "released", "released_at": "2026-01-01T00:00:00Z"},
        )

        client = ViswallClient(base_url="https://test.example.com", token="jwt")
        result = client.dhcp.release_lease(lease_id=99)
        assert result["state"] == "released"
        client.close()
