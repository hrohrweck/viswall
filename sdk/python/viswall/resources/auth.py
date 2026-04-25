"""Authentication resource."""

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class AuthResource:
    """Authentication and user profile operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate and obtain JWT token.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Login response with access_token
            
        Example:
            result = client.auth.login("admin", "secret")
            client.token = result["access_token"]
        """
        return self._client._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )

    def me(self) -> Dict[str, Any]:
        """Get current user profile.
        
        Returns:
            User profile data
        """
        return self._client._request("GET", "/auth/me")

    def get_ldap_config(self) -> Dict[str, Any]:
        """Get LDAP configuration (admin only)."""
        return self._client._request("GET", "/auth/ldap-config")

    def update_ldap_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update LDAP configuration (admin only)."""
        return self._client._request("POST", "/auth/ldap-config", json=config)

    def delete_ldap_config(self) -> Dict[str, Any]:
        """Delete LDAP configuration (admin only)."""
        return self._client._request("DELETE", "/auth/ldap-config")

    def test_ldap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test LDAP connection without saving."""
        return self._client._request("POST", "/auth/test-ldap", json=config)
