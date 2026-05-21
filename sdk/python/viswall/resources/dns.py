"""DNS resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class DNSResource:
    """DNS server, zone, and record operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_servers(self, instance_id: int) -> List[Dict[str, Any]]:
        """List DNS servers for an instance."""
        return self._client._request("GET", f"/dns/servers/{instance_id}")

    def create_server(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DNS server."""
        return self._client._request("POST", f"/dns/servers/{instance_id}", json=kwargs)

    def get_server(self, server_id: int) -> Dict[str, Any]:
        """Get DNS server by ID."""
        return self._client._request("GET", f"/dns/servers/detail/{server_id}")

    def update_server(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update DNS server."""
        return self._client._request("PATCH", f"/dns/servers/{server_id}", json=kwargs)

    def delete_server(self, server_id: int) -> None:
        """Delete DNS server."""
        self._client._request("DELETE", f"/dns/servers/{server_id}")

    def server_action(self, server_id: int, action: str) -> Dict[str, Any]:
        """Start, stop, or reload a DNS server."""
        return self._client._request("POST", f"/dns/servers/{server_id}/actions/{action}")

    def list_zones(self, server_id: int) -> List[Dict[str, Any]]:
        """List zones for a DNS server."""
        return self._client._request("GET", f"/dns/servers/{server_id}/zones")

    def create_zone(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DNS zone."""
        return self._client._request("POST", f"/dns/servers/{server_id}/zones", json=kwargs)

    def create_reverse_zone(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a reverse DNS zone."""
        return self._client._request("POST", f"/dns/servers/{server_id}/zones/reverse", json=kwargs)

    def get_zone(self, zone_id: int) -> Dict[str, Any]:
        """Get DNS zone by ID."""
        return self._client._request("GET", f"/dns/zones/detail/{zone_id}")

    def update_zone(self, zone_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update DNS zone."""
        return self._client._request("PATCH", f"/dns/zones/{zone_id}", json=kwargs)

    def delete_zone(self, zone_id: int) -> None:
        """Delete DNS zone."""
        self._client._request("DELETE", f"/dns/zones/{zone_id}")

    def sign_zone(self, zone_id: int) -> Dict[str, Any]:
        """Enable DNSSEC for a zone."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/sign")

    def unsign_zone(self, zone_id: int) -> Dict[str, Any]:
        """Disable DNSSEC for a zone."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/unsign")

    def list_dnssec_keys(self, zone_id: int) -> List[Dict[str, Any]]:
        """List DNSSEC keys for a zone."""
        return self._client._request("GET", f"/dns/zones/{zone_id}/dnssec-keys")

    def dnssec_rollover(self, zone_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Rollover DNSSEC keys for a zone."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/dnssec-rollover", json=kwargs)

    def list_records(self, zone_id: int) -> List[Dict[str, Any]]:
        """List records for a DNS zone."""
        return self._client._request("GET", f"/dns/zones/{zone_id}/records")

    def create_record(self, zone_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a DNS record."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/records", json=kwargs)

    def bulk_import_records(self, zone_id: int, **kwargs: Any) -> List[Dict[str, Any]]:
        """Bulk import DNS records."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/records/bulk", json=kwargs)

    def create_ptr_record(self, zone_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a PTR record in a reverse zone."""
        return self._client._request("POST", f"/dns/zones/{zone_id}/records/ptr", json=kwargs)

    def update_record(self, record_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update DNS record."""
        return self._client._request("PATCH", f"/dns/records/{record_id}", json=kwargs)

    def delete_record(self, record_id: int) -> None:
        """Delete DNS record."""
        self._client._request("DELETE", f"/dns/records/{record_id}")

    def list_zone_slaves(self, zone_id: int) -> List[Dict[str, Any]]:
        """List slave servers for a zone."""
        return self._client._request("GET", f"/dns/zones/{zone_id}/slaves")

    def list_tsig_keys(self, server_id: int) -> List[Dict[str, Any]]:
        """List TSIG keys for a DNS server."""
        return self._client._request("GET", f"/dns/servers/{server_id}/tsig-keys")

    def create_tsig_key(self, server_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a TSIG key."""
        return self._client._request("POST", f"/dns/servers/{server_id}/tsig-keys", json=kwargs)

    def rotate_tsig_key(self, key_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Rotate a TSIG key."""
        return self._client._request("POST", f"/dns/tsig-keys/{key_id}/rotate", json=kwargs)

    def delete_tsig_key(self, key_id: int) -> None:
        """Delete a TSIG key."""
        self._client._request("DELETE", f"/dns/tsig-keys/{key_id}")
