"""Firewall simulation resource."""

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class FirewallSimulationResource:
    """Firewall rule simulation and test suite operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def simulate_single(self, **kwargs: Any) -> Dict[str, Any]:
        """Simulate a single packet through a firewall configuration."""
        return self._client._request("POST", "/firewall_simulation/simulate/single", json=kwargs)

    def run_test_suite(self, **kwargs: Any) -> Dict[str, Any]:
        """Run a comprehensive test suite against a firewall configuration."""
        return self._client._request("POST", "/firewall_simulation/simulate/test-suite", json=kwargs)

    def simulate_multi_firewall(self, **kwargs: Any) -> Dict[str, Any]:
        """Simulate packet traversal across multiple firewalls."""
        return self._client._request("POST", "/firewall_simulation/simulate/multi-firewall", json=kwargs)

    def run_multi_firewall_tests(self, **kwargs: Any) -> Dict[str, Any]:
        """Run tests across multiple firewalls."""
        return self._client._request("POST", "/firewall_simulation/simulate/multi-firewall/tests", json=kwargs)

    def get_basic_test_suite(self) -> Dict[str, Any]:
        """Get the basic connectivity test suite."""
        return self._client._request("GET", "/firewall_simulation/test-suites/basic")

    def get_security_test_suite(self) -> Dict[str, Any]:
        """Get the security-focused test suite."""
        return self._client._request("GET", "/firewall_simulation/test-suites/security")

    def get_application_test_suite(self) -> Dict[str, Any]:
        """Get the application-specific test suite."""
        return self._client._request("GET", "/firewall_simulation/test-suites/application")

    def get_all_test_suites(self) -> Dict[str, Any]:
        """Get all predefined test suites."""
        return self._client._request("GET", "/firewall_simulation/test-suites/all")

    def get_visual_simulation_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get data for visual packet flow simulation."""
        return self._client._request("POST", "/firewall_simulation/simulate/visual", json=kwargs)
