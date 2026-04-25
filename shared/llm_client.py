"""
Modular LLM client factory for Viswall.

Supports OpenAI, Anthropic Claude, and Ollama via a pluggable provider pattern.
Use-case configurations are read from the llm_use_case_configs database table.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.models import LLMProvider as LLMProviderModel, LLMModel, LLMUseCaseConfig


class LLMError(Exception):
    """Base exception for LLM operations"""
    pass


class LLMProviderError(LLMError):
    """Provider-specific error"""
    pass


class LLMConfigError(LLMError):
    """Configuration error"""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, provider_config: LLMProviderModel, http_client: Optional[httpx.AsyncClient] = None):
        self.provider_config = provider_config
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """Send a chat completion request and return the content string."""
        pass

    async def classify(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 200,
    ) -> Dict[str, Any]:
        """Classify using the provider and parse JSON response."""
        content = await self.chat(
            messages=[
                {"role": "system", "content": "You are an email classification assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return _parse_json_response(content)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        base_url = self.provider_config.base_url or self.DEFAULT_BASE_URL
        api_key = self.provider_config.api_key
        if not api_key:
            raise LLMProviderError("OpenAI API key is required")

        try:
            response = await self._client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise LLMProviderError(f"OpenAI API error: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid OpenAI response: {e}")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        base_url = self.provider_config.base_url or self.DEFAULT_BASE_URL
        api_key = self.provider_config.api_key
        if not api_key:
            raise LLMProviderError("Anthropic API key is required")

        try:
            response = await self._client.post(
                f"{base_url}/messages",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except httpx.HTTPError as e:
            raise LLMProviderError(f"Anthropic API error: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid Anthropic response: {e}")


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider"""

    DEFAULT_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        base_url = self.provider_config.base_url or self.DEFAULT_BASE_URL

        try:
            response = await self._client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPError as e:
            raise LLMProviderError(f"Ollama API error: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid Ollama response: {e}")


# Provider type registry
_PROVIDER_REGISTRY: Dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def _parse_json_response(content: str) -> Dict[str, Any]:
    """Parse and validate JSON response from LLM."""
    # Extract JSON from markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise LLMProviderError(f"Invalid JSON response: {e}")

    if "category" not in parsed:
        raise LLMProviderError("Missing 'category' field in response")

    result = {
        "category": str(parsed["category"]).lower().strip(),
        "confidence": float(parsed.get("confidence", 0.5)),
        "reason": str(parsed.get("reason", "No reason provided"))[:200],
    }
    result["confidence"] = max(0.0, min(1.0, result["confidence"]))
    return result


class LLMClientFactory:
    """Factory for creating LLM providers and executing use-case requests."""

    @staticmethod
    def create_provider(provider_type: str, provider_config: LLMProviderModel) -> BaseLLMProvider:
        """Create a provider instance by type."""
        provider_class = _PROVIDER_REGISTRY.get(provider_type)
        if not provider_class:
            raise LLMConfigError(f"Unsupported provider type: {provider_type}")
        return provider_class(provider_config)

    @staticmethod
    async def get_use_case_config(db: AsyncSession, use_case: str) -> Optional[LLMUseCaseConfig]:
        """Fetch use-case configuration from the database."""
        result = await db.execute(
            select(LLMUseCaseConfig)
            .where(LLMUseCaseConfig.use_case == use_case)
            .where(LLMUseCaseConfig.is_enabled == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def classify_for_use_case(
        db: AsyncSession,
        use_case: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """Classify using the configured provider for a specific use case."""
        config = await LLMClientFactory.get_use_case_config(db, use_case)
        if not config:
            raise LLMConfigError(f"No enabled LLM configuration found for use case: {use_case}")

        if not config.provider or not config.model:
            raise LLMConfigError(f"Incomplete LLM configuration for use case: {use_case}")

        provider = LLMClientFactory.create_provider(
            config.provider.provider_type,
            config.provider,
        )

        result = await provider.classify(
            prompt=prompt,
            model=config.model.name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        result["provider"] = config.provider.provider_type
        result["model"] = config.model.name
        return result

    @staticmethod
    async def chat_for_use_case(
        db: AsyncSession,
        use_case: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """Send a chat request using the configured provider for a specific use case."""
        config = await LLMClientFactory.get_use_case_config(db, use_case)
        if not config:
            raise LLMConfigError(f"No enabled LLM configuration found for use case: {use_case}")

        if not config.provider or not config.model:
            raise LLMConfigError(f"Incomplete LLM configuration for use case: {use_case}")

        provider = LLMClientFactory.create_provider(
            config.provider.provider_type,
            config.provider,
        )

        return await provider.chat(
            messages=messages,
            model=config.model.name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
