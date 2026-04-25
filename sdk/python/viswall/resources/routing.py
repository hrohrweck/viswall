"""Routing resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class RoutingResource:
    """Policy routing operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_rules(self, instance_id: int) -> List[Dict[str, Any]]:
        """List routing rules for an instance."""
        return self._client._request("GET", f"/routing/rules/{instance_id}")

    def create_rule(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a routing rule."""
        return self._client._request("POST", f"/routing/rules/{instance_id}", json=kwargs)

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Get routing rule by ID."""
        return self._client._request("GET", f"/routing/rules/detail/{rule_id}")

    def update_rule(self, rule_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update routing rule."""
        return self._client._request("PATCH", f"/routing/rules/{rule_id}", json=kwargs)

    def delete_rule(self, rule_id: int) -> None:
        """Delete routing rule."""
        self._client._request("DELETE", f"/routing/rules/{rule_id}")

    def apply_rules(self, instance_id: int) -> Dict[str, Any]:
        """Apply routing configuration."""
        return self._client._request("POST", f"/routing/apply/{instance_id}")
