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
        mta_forward_enabled: bool = False,
        mta_forward_host: Optional[str] = None,
        mta_forward_port: int = 25,
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
            mta_forward_enabled: Enable MTA forwarding
            mta_forward_host: MTA forward host (sent only when not None)
            mta_forward_port: MTA forward port (default 25)
            
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
            "mta_forward_enabled": mta_forward_enabled,
            "mta_forward_port": mta_forward_port,
            **kwargs,
        }
        if mta_forward_host is not None:
            data["mta_forward_host"] = mta_forward_host
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

    def get_dns_records(self, domain_id: int) -> Dict[str, Any]:
        """Get expected DNS records for a mail domain."""
        return self._client._request("GET", f"/mail/domains/{domain_id}/dns-records")

    def check_dns(self, domain_id: int) -> Dict[str, Any]:
        """Run a live DNS verification for a mail domain."""
        return self._client._request("POST", f"/mail/domains/{domain_id}/dns-check")

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

    def list_aliases(self, domain_id: int) -> List[Dict[str, Any]]:
        """List mail aliases for a domain."""
        return self._client._request("GET", f"/mail/aliases/{domain_id}")

    def create_alias(
        self,
        domain_id: int,
        source: str,
        destination: str,
        enabled: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mail alias.
        
        Args:
            domain_id: Domain ID
            source: Alias source address (e.g., "info@example.com")
            destination: Alias destination address (e.g., "john@example.com")
            enabled: Whether alias is enabled
            
        Returns:
            Created alias
        """
        data = {"source": source, "destination": destination, "enabled": enabled, **kwargs}
        return self._client._request("POST", f"/mail/aliases/{domain_id}", json=data)

    def update_alias(self, alias_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update mail alias."""
        return self._client._request("PATCH", f"/mail/aliases/{alias_id}", json=kwargs)

    def delete_alias(self, alias_id: int) -> None:
        """Delete mail alias."""
        self._client._request("DELETE", f"/mail/aliases/{alias_id}")

    def get_queue(self, instance_id: int) -> Dict[str, Any]:
        """Get mail queue status."""
        return self._client._request("GET", f"/mail/queue/{instance_id}")

    def flush_queue(self, instance_id: int) -> Dict[str, Any]:
        """Flush mail queue."""
        return self._client._request("POST", f"/mail/queue/{instance_id}/flush")

    def get_stats(self, instance_id: int) -> Dict[str, Any]:
        """Get mail statistics."""
        return self._client._request("GET", f"/mail/stats/{instance_id}")

    def get_logs(
        self,
        instance_id: int,
        offset: int = 0,
        limit: int = 200,
        q: Optional[str] = None,
        domain: Optional[str] = None,
        mail_id: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get one page of exim mainlog lines from an instance's mail agent.

        Args:
            instance_id: Instance ID
            offset: Pagination offset (default 0)
            limit: Lines per page (default 200)
            q: Keyword filter (matched anywhere in the line)
            domain: Filter by domain name
            mail_id: Filter by exim message ID
            since: Agent-local start time ("YYYY-MM-DD HH:MM[:SS]")
            until: Agent-local end time ("YYYY-MM-DD HH:MM[:SS]")

        Returns:
            Dict with lines, total_matched and next_offset (None = end of data)
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if q is not None:
            params["q"] = q
        if domain is not None:
            params["domain"] = domain
        if mail_id is not None:
            params["mail_id"] = mail_id
        if since is not None:
            params["since"] = since
        if until is not None:
            params["until"] = until
        return self._client._request("GET", f"/mail/logs/{instance_id}", params=params)

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
