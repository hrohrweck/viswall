"""Metrics resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class MetricsResource:
    """Metrics and monitoring operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def get_latest(self, instance_id: int) -> Dict[str, Any]:
        """Get latest metrics snapshot for an instance."""
        return self._client._request("GET", f"/metrics/latest/{instance_id}")

    def query(
        self,
        instance_id: int,
        metric_type: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Query metrics history.
        
        Args:
            instance_id: Instance ID
            metric_type: Metric type filter
            start: Start time (ISO format)
            end: End time (ISO format)
            
        Returns:
            List of metric snapshots
        """
        data = {"instance_id": instance_id, **kwargs}
        if metric_type:
            data["metric_type"] = metric_type
        if start:
            data["start"] = start
        if end:
            data["end"] = end
        return self._client._request("POST", "/metrics/query", json=data)

    def get_summary(self, instance_id: int, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get metrics summary."""
        return self._client._request("POST", "/metrics/summary", json={"instance_id": instance_id, **kwargs})

    def get_dashboard(self, instance_id: int) -> Dict[str, Any]:
        """Get dashboard data for an instance."""
        return self._client._request("GET", f"/metrics/dashboard/{instance_id}")

    def get_overview(self) -> Dict[str, Any]:
        """Get global metrics overview."""
        return self._client._request("GET", "/metrics/overview")
