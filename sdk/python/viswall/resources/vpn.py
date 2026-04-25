"""VPN resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class VPNResource:
    """VPN server and client operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def get_protocol_recommendations(self) -> List[Dict[str, Any]]:
        """Get VPN protocol recommendations."""
        return self._client._request("GET", "/vpn/protocols/recommendations")

    def list_servers(self, instance_id: int) -> List[Dict[str, Any]]:
        """List VPN servers for an instance."""
        return self._client._request("GET", f"/vpn/servers/{instance_id}")

    def create_server(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a VPN server."""
        return self._client._request("POST", f"/vpn/servers/{instance_id}", json=kwargs)

    def get_server(self, server_id: int) -> Dict[str, Any]:
        """Get VPN server by ID."""
        return self._client._request("GET", f"/vpn/servers/detail/{server_id}")

    def update_server(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update VPN server."""
        return self._client._request("PATCH", f"/vpn/servers/{server_id}", json=kwargs)

    def delete_server(self, server_id: int) -> None:
        """Delete VPN server."""
        self._client._request("DELETE", f"/vpn/servers/{server_id}")

    def start_server(self, server_id: int) -> Dict[str, Any]:
        """Start VPN server."""
        return self._client._request("POST", f"/vpn/servers/{server_id}/start")

    def stop_server(self, server_id: int) -> Dict[str, Any]:
        """Stop VPN server."""
        return self._client._request("POST", f"/vpn/servers/{server_id}/stop")

    def restart_server(self, server_id: int) -> Dict[str, Any]:
        """Restart VPN server."""
        return self._client._request("POST", f"/vpn/servers/{server_id}/restart")

    def get_server_stats(self, server_id: int) -> Dict[str, Any]:
        """Get VPN server statistics."""
        return self._client._request("GET", f"/vpn/servers/{server_id}/stats")

    def list_clients(self, server_id: int) -> List[Dict[str, Any]]:
        """List VPN clients for a server."""
        return self._client._request("GET", f"/vpn/servers/{server_id}/clients")

    def create_client(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a VPN client."""
        return self._client._request("POST", f"/vpn/servers/{server_id}/clients", json=kwargs)

    def get_client(self, client_id: int) -> Dict[str, Any]:
        """Get VPN client by ID."""
        return self._client._request("GET", f"/vpn/clients/{client_id}")

    def update_client(self, client_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update VPN client."""
        return self._client._request("PATCH", f"/vpn/clients/{client_id}", json=kwargs)

    def delete_client(self, client_id: int) -> None:
        """Delete VPN client."""
        self._client._request("DELETE", f"/vpn/clients/{client_id}")

    def get_client_config(self, client_id: int, format: str = "wireguard") -> Dict[str, Any]:
        """Get VPN client configuration."""
        return self._client._request(
            "GET", f"/vpn/clients/{client_id}/config", params={"format": format}
        )

    def regenerate_client(self, client_id: int) -> Dict[str, Any]:
        """Regenerate VPN client credentials."""
        return self._client._request("POST", f"/vpn/clients/{client_id}/regenerate")
