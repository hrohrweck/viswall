"""Assistant resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class AssistantResource:
    """LLM assistant operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def chat(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        """Send a message to the LLM assistant.
        
        Args:
            message: User message
            **kwargs: Optional context (instance_id, conversation_id, etc.)
            
        Returns:
            Assistant response
        """
        return self._client._request("POST", "/assistant/chat", json={"message": message, **kwargs})

    def suggest_firewall_rule(self, description: str, **kwargs: Any) -> Dict[str, Any]:
        """Get LLM-suggested firewall rule from description.
        
        Args:
            description: Natural language description of desired rule
            **kwargs: Optional instance_id
            
        Returns:
            Suggested rule with explanation
        """
        return self._client._request(
            "POST", "/assistant/suggest-firewall-rule", json={"description": description, **kwargs}
        )

    def generate_tests(self, description: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate test cases for a configuration.
        
        Args:
            description: What to test
            **kwargs: Optional rules, instance_id
            
        Returns:
            Generated test cases
        """
        return self._client._request(
            "POST", "/assistant/generate-tests", json={"description": description, **kwargs}
        )

    def explain_configuration(self, config_type: str, config: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Explain a configuration in natural language.
        
        Args:
            config_type: Type of config (firewall, vpn, mail, etc.)
            config: Configuration dictionary
            **kwargs: Optional question
            
        Returns:
            Explanation
        """
        return self._client._request(
            "POST",
            "/assistant/explain-configuration",
            json={"config_type": config_type, "config": config, **kwargs},
        )

    def security_audit(self, rules: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """Run security audit on firewall rules.
        
        Args:
            rules: List of firewall rules
            **kwargs: Optional standard (pci-dss, iso27001, etc.)
            
        Returns:
            Audit findings and recommendations
        """
        return self._client._request(
            "POST", "/assistant/security-audit", json={"rules": rules, **kwargs}
        )

    def get_capabilities(self) -> Dict[str, Any]:
        """Get LLM assistant capabilities."""
        return self._client._request("GET", "/assistant/capabilities")

    def get_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self._client._request("GET", "/assistant/config")

    def update_config(self, **kwargs: Any) -> Dict[str, Any]:
        """Update LLM configuration (admin only)."""
        return self._client._request("POST", "/assistant/config", json=kwargs)
