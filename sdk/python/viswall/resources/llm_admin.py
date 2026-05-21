"""LLM admin resource."""

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class LLMAdminResource:
    """LLM provider, model, and use-case configuration operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all LLM providers."""
        return self._client._request("GET", "/llm_admin/providers")

    def create_provider(self, **kwargs: Any) -> Dict[str, Any]:
        """Create a new LLM provider."""
        return self._client._request("POST", "/llm_admin/providers", json=kwargs)

    def get_provider(self, provider_id: int) -> Dict[str, Any]:
        """Get an LLM provider by ID."""
        return self._client._request("GET", f"/llm_admin/providers/{provider_id}")

    def update_provider(self, provider_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update an LLM provider."""
        return self._client._request("PATCH", f"/llm_admin/providers/{provider_id}", json=kwargs)

    def delete_provider(self, provider_id: int) -> None:
        """Delete an LLM provider."""
        self._client._request("DELETE", f"/llm_admin/providers/{provider_id}")

    def test_provider(self, provider_id: int) -> Dict[str, Any]:
        """Test connectivity to an LLM provider."""
        return self._client._request("POST", f"/llm_admin/providers/{provider_id}/test")

    def list_models(self, provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List LLM models, optionally filtered by provider."""
        params = {}
        if provider_id is not None:
            params["provider_id"] = provider_id
        return self._client._request("GET", "/llm_admin/models", params=params)

    def create_model(self, **kwargs: Any) -> Dict[str, Any]:
        """Create a new LLM model."""
        return self._client._request("POST", "/llm_admin/models", json=kwargs)

    def get_model(self, model_id: int) -> Dict[str, Any]:
        """Get an LLM model by ID."""
        return self._client._request("GET", f"/llm_admin/models/{model_id}")

    def update_model(self, model_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update an LLM model."""
        return self._client._request("PATCH", f"/llm_admin/models/{model_id}", json=kwargs)

    def delete_model(self, model_id: int) -> None:
        """Delete an LLM model."""
        self._client._request("DELETE", f"/llm_admin/models/{model_id}")

    def list_use_case_configs(self) -> List[Dict[str, Any]]:
        """List all use-case configurations."""
        return self._client._request("GET", "/llm_admin/use-cases")

    def create_use_case_config(self, **kwargs: Any) -> Dict[str, Any]:
        """Create a new use-case configuration."""
        return self._client._request("POST", "/llm_admin/use-cases", json=kwargs)

    def get_use_case_config(self, config_id: int) -> Dict[str, Any]:
        """Get a use-case configuration by ID."""
        return self._client._request("GET", f"/llm_admin/use-cases/{config_id}")

    def update_use_case_config(self, config_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update a use-case configuration."""
        return self._client._request("PATCH", f"/llm_admin/use-cases/{config_id}", json=kwargs)

    def delete_use_case_config(self, config_id: int) -> None:
        """Delete a use-case configuration."""
        self._client._request("DELETE", f"/llm_admin/use-cases/{config_id}")
