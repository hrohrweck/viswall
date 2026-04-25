"""Audit resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class AuditResource:
    """Audit log operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """List audit logs.
        
        Args:
            limit: Number of results to return
            offset: Offset for pagination
            **filters: Optional filters (user_id, instance_id, action, resource_type, etc.)
            
        Returns:
            List of audit log entries
        """
        params = {"limit": limit, "offset": offset, **filters}
        return self._client._request("GET", "/audit", params=params)

    def get_instance_logs(self, instance_id: int, **params: Any) -> List[Dict[str, Any]]:
        """Get audit logs for a specific instance."""
        return self._client._request("GET", f"/audit/instance/{instance_id}", params=params)

    def get_resource_logs(
        self, resource_type: str, resource_id: int, **params: Any
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a specific resource."""
        return self._client._request(
            "GET", f"/audit/resource/{resource_type}/{resource_id}", params=params
        )

    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get audit summary statistics.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Summary statistics
        """
        return self._client._request("GET", "/audit/summary", params={"days": days})
