"""Network interface management resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class NetworkResource:
    """Host interface configuration and node-agent dispatch."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_interfaces(self, instance_id: int) -> List[Dict[str, Any]]:
        """Configured (desired-state) interfaces for an instance."""
        return self._client._request("GET", f"/network/interfaces/{instance_id}")

    def create_interface(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Add an interface to the instance's desired configuration."""
        return self._client._request("POST", f"/network/interfaces/{instance_id}", json=kwargs)

    def update_interface(self, interface_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update desired state for one interface (apply separately)."""
        return self._client._request(
            "PATCH", f"/network/interfaces/detail/{interface_id}", json=kwargs
        )

    def delete_interface(self, interface_id: int) -> None:
        """Remove an interface from the desired configuration."""
        self._client._request("DELETE", f"/network/interfaces/detail/{interface_id}")

    def live_interfaces(self, instance_id: int) -> Dict[str, Any]:
        """Live interface state reported by the instance's node agent."""
        return self._client._request("GET", f"/network/interfaces/{instance_id}/live")

    def apply_interfaces(
        self, instance_id: int, force: bool = False
    ) -> Dict[str, Any]:
        """Dispatch desired interface configuration to the node agent.

        Args:
            instance_id: Instance ID
            force: Allow changes touching the default-route interface
                (may cut management connectivity)
        """
        return self._client._request(
            "POST", f"/network/interfaces/{instance_id}/apply", json={"force": force}
        )
