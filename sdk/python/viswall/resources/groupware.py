"""Groupware resource."""

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class GroupwareResource:
    """Groupware (SOGo) operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def get_status(self, domain_id: int) -> Dict[str, Any]:
        """Get groupware status for a domain.
        
        Args:
            domain_id: Mail domain ID
            
        Returns:
            Groupware status and SOGo URL
        """
        return self._client._request("GET", f"/groupware/status/{domain_id}")

    def enable(self, domain_id: int) -> Dict[str, Any]:
        """Enable groupware for a domain (admin only).
        
        Args:
            domain_id: Mail domain ID
            
        Returns:
            Updated domain
        """
        return self._client._request("POST", f"/groupware/enable/{domain_id}")

    def disable(self, domain_id: int) -> Dict[str, Any]:
        """Disable groupware for a domain (admin only).
        
        Args:
            domain_id: Mail domain ID
            
        Returns:
            Updated domain
        """
        return self._client._request("POST", f"/groupware/disable/{domain_id}")

    def get_stats(self, domain_id: int) -> Dict[str, Any]:
        """Get groupware usage statistics (admin only).
        
        Args:
            domain_id: Mail domain ID
            
        Returns:
            Usage statistics
        """
        return self._client._request("GET", f"/groupware/stats/{domain_id}")
