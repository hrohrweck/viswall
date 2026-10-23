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
        """List VPN servers for an instance.

        Answers ``List[VPNServerResponse]`` — the plain shape carries no
        ``private_key``, so this call can never expose the site-to-site
        tunnel key, even for admins.
        """
        return self._client._request("GET", f"/vpn/servers/{instance_id}")

    def create_server(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a VPN server (admin-only).

        Answers ``VPNServerAdminResponse`` — the only server shape that may
        carry ``private_key`` (returned by this admin-gated route).
        """
        return self._client._request("POST", f"/vpn/servers/{instance_id}", json=kwargs)

    def get_server(self, server_id: int) -> Dict[str, Any]:
        """Get VPN server by ID.

        Answers ``VPNServerResponse`` — no ``private_key`` field.
        """
        return self._client._request("GET", f"/vpn/servers/detail/{server_id}")

    def update_server(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update VPN server (admin-only).

        Answers ``VPNServerAdminResponse`` — the only server shape that may
        carry ``private_key`` (returned by this admin-gated route).
        """
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
        """List VPN clients for a server.

        Answers ``List[VPNClientResponse]`` — the plain shape carries no
        ``config_file``/``config_qr`` (the generated config embeds the raw
        WireGuard private key, so it is never listable).
        """
        return self._client._request("GET", f"/vpn/servers/{server_id}/clients")

    def create_client(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a VPN client (admin-only).

        Answers ``VPNClientAdminResponse`` — the only client shape that
        carries the generated ``config_file``/``config_qr``.
        """
        return self._client._request("POST", f"/vpn/servers/{server_id}/clients", json=kwargs)

    def get_client(self, client_id: int) -> Dict[str, Any]:
        """Get VPN client by ID.

        Answers ``VPNClientResponse`` — no ``config_file``/``config_qr``.
        """
        return self._client._request("GET", f"/vpn/clients/{client_id}")

    def update_client(self, client_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update VPN client (admin-only).

        Answers ``VPNClientResponse`` — no ``config_file``/``config_qr``;
        use :meth:`get_client_config` for the generated config.
        """
        return self._client._request("PATCH", f"/vpn/clients/{client_id}", json=kwargs)

    def delete_client(self, client_id: int) -> None:
        """Delete VPN client."""
        self._client._request("DELETE", f"/vpn/clients/{client_id}")

    def get_client_config(self, client_id: int, format: str = "auto") -> Dict[str, Any]:
        """Get VPN client configuration (admin-only endpoint).

        The endpoint is admin-gated because the config embeds the raw
        WireGuard private key; non-admin callers receive a 403.
        """
        return self._client._request(
            "GET", f"/vpn/clients/{client_id}/config", params={"format": format}
        )

    def regenerate_client(self, client_id: int) -> Dict[str, Any]:
        """Regenerate VPN client credentials (admin-only endpoint)."""
        return self._client._request("POST", f"/vpn/clients/{client_id}/regenerate")

    def get_site_to_site_status(self, instance_id: int) -> List[Dict[str, Any]]:
        """Get status of all site-to-site tunnels for an instance."""
        return self._client._request(
            "GET", "/vpn/site-to-site/status", params={"instance_id": instance_id}
        )

    def initialize_site_to_site(
        self,
        instance_id: int,
        remote_endpoint: str,
        remote_public_key: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Initialize a site-to-site VPN tunnel and push it to the VPN agent.

        Optional keyword arguments mirror the backend query parameters:
        ``protocol``, ``local_address``, ``allowed_ips``, ``persistent_keepalive``.
        """
        params: Dict[str, Any] = {
            "local_instance_id": instance_id,
            "remote_endpoint": remote_endpoint,
            "remote_public_key": remote_public_key,
        }
        params.update(kwargs)
        return self._client._request("POST", "/vpn/site-to-site/initialize", params=params)
