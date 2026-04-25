"""Firewall resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class FirewallResource:
    """Firewall rule and NAT operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_rules(self, instance_id: int) -> List[Dict[str, Any]]:
        """List firewall rules for an instance."""
        return self._client._request("GET", f"/firewall/rules/{instance_id}")

    def create_rule(
        self,
        instance_id: int,
        name: str,
        action: str,
        chain: str = "input",
        protocol: str = "tcp",
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a firewall rule.
        
        Args:
            instance_id: Instance ID
            name: Rule name
            action: accept, drop, or reject
            chain: input, output, or forward
            protocol: tcp, udp, icmp, or any
            src_ip: Source IP or CIDR
            dst_ip: Destination IP or CIDR
            src_port: Source port
            dst_port: Destination port
            
        Returns:
            Created rule
        """
        data = {
            "name": name,
            "action": action,
            "chain": chain,
            "protocol": protocol,
            **kwargs,
        }
        if src_ip:
            data["src_ip"] = src_ip
        if dst_ip:
            data["dst_ip"] = dst_ip
        if src_port:
            data["src_port"] = src_port
        if dst_port:
            data["dst_port"] = dst_port
        
        return self._client._request("POST", f"/firewall/rules/{instance_id}", json=data)

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Get firewall rule by ID."""
        return self._client._request("GET", f"/firewall/rules/detail/{rule_id}")

    def update_rule(self, rule_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update firewall rule."""
        return self._client._request("PATCH", f"/firewall/rules/{rule_id}", json=kwargs)

    def delete_rule(self, rule_id: int) -> None:
        """Delete firewall rule."""
        self._client._request("DELETE", f"/firewall/rules/{rule_id}")

    def apply_rules(self, instance_id: int) -> Dict[str, Any]:
        """Apply firewall configuration to instance."""
        return self._client._request("POST", f"/firewall/apply/{instance_id}")

    def list_interfaces(self, instance_id: int) -> List[Dict[str, Any]]:
        """List network interfaces for an instance."""
        return self._client._request("GET", f"/firewall/interfaces/{instance_id}")

    def list_nat_rules(self, instance_id: int) -> List[Dict[str, Any]]:
        """List NAT rules for an instance."""
        return self._client._request("GET", f"/firewall/nat/{instance_id}")

    def create_nat_rule(self, instance_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Create a NAT rule."""
        return self._client._request("POST", f"/firewall/nat/{instance_id}", json=kwargs)

    def block_ip(self, instance_id: int, ip: str, duration: Optional[int] = None) -> Dict[str, Any]:
        """Block an IP address."""
        data = {"ip": ip}
        if duration:
            data["duration"] = duration
        return self._client._request("POST", f"/firewall/block/{instance_id}", json=data)

    def unblock_ip(self, instance_id: int, ip: str) -> Dict[str, Any]:
        """Unblock an IP address."""
        return self._client._request("POST", f"/firewall/unblock/{instance_id}", json={"ip": ip})

    def get_stats(self, instance_id: int) -> Dict[str, Any]:
        """Get firewall statistics."""
        return self._client._request("GET", f"/firewall/stats/{instance_id}")
