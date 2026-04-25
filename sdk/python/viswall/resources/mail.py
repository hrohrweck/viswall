"""Mail resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class MailResource:
    """Mail domain and user operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_domains(self, instance_id: int) -> List[Dict[str, Any]]:
        """List mail domains for an instance."""
        return self._client._request("GET", f"/mail/domains/{instance_id}")

    def create_domain(
        self,
        instance_id: int,
        domain: str,
        enabled: bool = True,
        spam_filter_enabled: bool = True,
        virus_scan_enabled: bool = True,
        dkim_enabled: bool = True,
        dmarc_enabled: bool = True,
        spf_enabled: bool = True,
        llm_enabled: bool = False,
        groupware_enabled: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mail domain.
        
        Args:
            instance_id: Instance ID
            domain: Domain name (e.g., "example.com")
            enabled: Whether domain is enabled
            spam_filter_enabled: Enable spam filtering
            virus_scan_enabled: Enable virus scanning
            dkim_enabled: Enable DKIM signing
            dmarc_enabled: Enable DMARC policy
            spf_enabled: Enable SPF
            llm_enabled: Enable LLM classification
            groupware_enabled: Enable groupware (SOGo)
            
        Returns:
            Created domain
        """
        data = {
            "domain": domain,
            "enabled": enabled,
            "spam_filter_enabled": spam_filter_enabled,
            "virus_scan_enabled": virus_scan_enabled,
            "dkim_enabled": dkim_enabled,
            "dmarc_enabled": dmarc_enabled,
            "spf_enabled": spf_enabled,
            "llm_enabled": llm_enabled,
            "groupware_enabled": groupware_enabled,
            **kwargs,
        }
        return self._client._request("POST", f"/mail/domains/{instance_id}", json=data)

    def get_domain(self, domain_id: int) -> Dict[str, Any]:
        """Get mail domain by ID."""
        return self._client._request("GET", f"/mail/domains/detail/{domain_id}")

    def update_domain(self, domain_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update mail domain."""
        return self._client._request("PATCH", f"/mail/domains/{domain_id}", json=kwargs)

    def delete_domain(self, domain_id: int) -> None:
        """Delete mail domain."""
        self._client._request("DELETE", f"/mail/domains/{domain_id}")

    def list_users(self, domain_id: int) -> List[Dict[str, Any]]:
        """List mail users for a domain."""
        return self._client._request("GET", f"/mail/users/{domain_id}")

    def create_user(
        self,
        domain_id: int,
        username: str,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mail user.
        
        Args:
            domain_id: Domain ID
            username: Username (without domain)
            password: Initial password
            full_name: Full display name
            
        Returns:
            Created user
        """
        data = {"username": username, **kwargs}
        if password:
            data["password"] = password
        if full_name:
            data["full_name"] = full_name
        return self._client._request("POST", f"/mail/users/{domain_id}", json=data)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get mail user by ID."""
        return self._client._request("GET", f"/mail/users/detail/{user_id}")

    def update_user(self, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update mail user."""
        return self._client._request("PATCH", f"/mail/users/{user_id}", json=kwargs)

    def delete_user(self, user_id: int) -> None:
        """Delete mail user."""
        self._client._request("DELETE", f"/mail/users/{user_id}")

    def get_queue(self, instance_id: int) -> Dict[str, Any]:
        """Get mail queue status."""
        return self._client._request("GET", f"/mail/queue/{instance_id}")

    def flush_queue(self, instance_id: int) -> Dict[str, Any]:
        """Flush mail queue."""
        return self._client._request("POST", f"/mail/queue/{instance_id}/flush")

    def get_stats(self, instance_id: int) -> Dict[str, Any]:
        """Get mail statistics."""
        return self._client._request("GET", f"/mail/stats/{instance_id}")

    def test_classify(self, domain_id: int, subject: str, sender: str, **kwargs: Any) -> Dict[str, Any]:
        """Test LLM classification on a sample email."""
        data = {"subject": subject, "sender": sender, **kwargs}
        return self._client._request("POST", f"/mail/domains/{domain_id}/classify", json=data)

    def list_messages(self, domain_id: int, **params: Any) -> List[Dict[str, Any]]:
        """List classified messages for a domain."""
        return self._client._request("GET", f"/mail/messages/{domain_id}", params=params)

    def get_message(self, message_id: int) -> Dict[str, Any]:
        """Get classified message details."""
        return self._client._request("GET", f"/mail/messages/detail/{message_id}")

    def reclassify_message(self, message_id: int) -> Dict[str, Any]:
        """Reclassify a message."""
        return self._client._request("POST", f"/mail/messages/{message_id}/reclassify")

    def message_action(self, message_id: int, action: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Take action on a classified message."""
        data = {"action": action}
        if reason:
            data["reason"] = reason
        return self._client._request("POST", f"/mail/messages/{message_id}/action", json=data)
