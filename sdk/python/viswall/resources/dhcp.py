"""DHCP resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class DHCPResource:
    """DHCP server, subnet, and lease operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_servers(self, instance_id: int) -> List[Dict[str, Any]]:
        """List DHCP servers for an instance."""
        return self._client._request("GET", f"/dhcp/servers/{instance_id}")

    def create_server(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DHCP server."""
        return self._client._request("POST", f"/dhcp/servers/{instance_id}", json=kwargs)

    def get_server(self, server_id: int) -> Dict[str, Any]:
        """Get DHCP server details by ID."""
        return self._client._request("GET", f"/dhcp/servers/detail/{server_id}")

    def update_server(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update DHCP server."""
        return self._client._request("PATCH", f"/dhcp/servers/{server_id}", json=kwargs)

    def delete_server(self, server_id: int) -> None:
        """Delete DHCP server."""
        self._client._request("DELETE", f"/dhcp/servers/{server_id}")

    def server_action(self, server_id: int, action: str) -> Dict[str, Any]:
        """Run DHCP server action: start, stop, reload."""
        return self._client._request("POST", f"/dhcp/servers/{server_id}/actions/{action}")

    def list_subnets(self, server_id: int) -> List[Dict[str, Any]]:
        """List DHCP subnets for a server."""
        return self._client._request("GET", f"/dhcp/servers/{server_id}/subnets")

    def create_subnet(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DHCP subnet on a server."""
        return self._client._request("POST", f"/dhcp/servers/{server_id}/subnets", json=kwargs)

    def get_subnet(self, subnet_id: int) -> Dict[str, Any]:
        """Get DHCP subnet details."""
        return self._client._request("GET", f"/dhcp/subnets/detail/{subnet_id}")

    def update_subnet(self, subnet_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update DHCP subnet."""
        return self._client._request("PATCH", f"/dhcp/subnets/{subnet_id}", json=kwargs)

    def delete_subnet(self, subnet_id: int) -> None:
        """Delete DHCP subnet."""
        self._client._request("DELETE", f"/dhcp/subnets/{subnet_id}")

    def list_pools(self, subnet_id: int) -> List[Dict[str, Any]]:
        """List DHCP pools for a subnet."""
        return self._client._request("GET", f"/dhcp/subnets/{subnet_id}/pools")

    def create_pool(self, subnet_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DHCP pool."""
        return self._client._request("POST", f"/dhcp/subnets/{subnet_id}/pools", json=kwargs)

    def delete_pool(self, pool_id: int) -> None:
        """Delete DHCP pool."""
        self._client._request("DELETE", f"/dhcp/pools/{pool_id}")

    def list_reservations(self, subnet_id: int) -> List[Dict[str, Any]]:
        """List DHCP reservations for a subnet."""
        return self._client._request("GET", f"/dhcp/subnets/{subnet_id}/reservations")

    def create_reservation(self, subnet_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DHCP reservation."""
        return self._client._request(
            "POST", f"/dhcp/subnets/{subnet_id}/reservations", json=kwargs
        )

    def delete_reservation(self, reservation_id: int) -> None:
        """Delete DHCP reservation."""
        self._client._request("DELETE", f"/dhcp/reservations/{reservation_id}")

    def list_options(self, subnet_id: int) -> List[Dict[str, Any]]:
        """List DHCP options for a subnet."""
        return self._client._request("GET", f"/dhcp/subnets/{subnet_id}/options")

    def create_option(self, subnet_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DHCP option."""
        return self._client._request("POST", f"/dhcp/subnets/{subnet_id}/options", json=kwargs)

    def delete_option(self, option_id: int) -> None:
        """Delete DHCP option."""
        self._client._request("DELETE", f"/dhcp/options/{option_id}")

    def list_subnet_leases(self, subnet_id: int) -> List[Dict[str, Any]]:
        """List DHCP leases for a subnet."""
        return self._client._request("GET", f"/dhcp/subnets/{subnet_id}/leases")

    def list_active_leases(self) -> List[Dict[str, Any]]:
        """List all active DHCP leases."""
        return self._client._request("GET", "/dhcp/leases/active")

    def release_lease(self, lease_id: int) -> Dict[str, Any]:
        """Release a DHCP lease."""
        return self._client._request("DELETE", f"/dhcp/leases/{lease_id}")
