"""Instances resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class InstancesResource:
    """Instance management operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all instances.
        
        Returns:
            List of instance objects
        """
        return self._client._request("GET", "/instances")

    def create(
        self,
        name: str,
        hostname: str,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new instance.
        
        Args:
            name: Instance name
            hostname: Hostname or IP address
            api_endpoint: API endpoint URL
            api_key: API key for agent communication
            **kwargs: Additional fields
            
        Returns:
            Created instance
        """
        data = {
            "name": name,
            "hostname": hostname,
            "api_endpoint": api_endpoint or f"http://{hostname}:8000",
            "api_key": api_key,
            **kwargs,
        }
        return self._client._request("POST", "/instances", json=data)

    def get(self, instance_id: int) -> Dict[str, Any]:
        """Get instance by ID.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Instance data
        """
        return self._client._request("GET", f"/instances/{instance_id}")

    def update(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update instance.
        
        Args:
            instance_id: Instance ID
            **kwargs: Fields to update
            
        Returns:
            Updated instance
        """
        return self._client._request("PATCH", f"/instances/{instance_id}", json=kwargs)

    def delete(self, instance_id: int) -> None:
        """Delete instance.
        
        Args:
            instance_id: Instance ID
        """
        self._client._request("DELETE", f"/instances/{instance_id}")

    def heartbeat(self, instance_id: int, api_key: str) -> Dict[str, Any]:
        """Send heartbeat from agent.
        
        Args:
            instance_id: Instance ID
            api_key: Agent API key
            
        Returns:
            Heartbeat response with config_version
        """
        return self._client._request(
            "POST",
            f"/instances/{instance_id}/heartbeat",
            json={"api_key": api_key},
        )
