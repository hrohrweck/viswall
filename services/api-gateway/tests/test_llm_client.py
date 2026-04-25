"""Tests for the modular LLM client factory."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from shared.llm_client import (
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    LLMClientFactory,
    LLMConfigError,
    _parse_json_response,
)
from shared.models import LLMProvider


@pytest.fixture
def mock_provider_config():
    config = MagicMock(spec=LLMProvider)
    config.provider_type = "openai"
    config.base_url = None
    config.api_key = "test-key"
    return config


@pytest.fixture
def mock_ollama_config():
    config = MagicMock(spec=LLMProvider)
    config.provider_type = "ollama"
    config.base_url = "http://ollama:11434"
    config.api_key = None
    return config


class TestParseJsonResponse:
    def test_valid_json(self):
        content = '{"category": "spam", "confidence": 0.95, "reason": "Test"}'
        result = _parse_json_response(content)
        assert result["category"] == "spam"
        assert result["confidence"] == 0.95

    def test_json_in_code_block(self):
        content = '```json\n{"category": "spam", "confidence": 0.95}\n```'
        result = _parse_json_response(content)
        assert result["category"] == "spam"

    def test_missing_category_raises(self):
        content = '{"confidence": 0.95}'
        with pytest.raises(Exception):
            _parse_json_response(content)


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_chat_success(self, mock_provider_config):
        provider = OpenAIProvider(mock_provider_config)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}]
        }
        provider._client = MagicMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        result = await provider.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4",
        )
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_chat_missing_api_key(self, mock_provider_config):
        mock_provider_config.api_key = None
        provider = OpenAIProvider(mock_provider_config)
        with pytest.raises(Exception, match="API key is required"):
            await provider.chat(messages=[], model="gpt-4")


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_chat_success(self, mock_ollama_config):
        provider = OllamaProvider(mock_ollama_config)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Hello from Ollama"}
        }
        provider._client = MagicMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        result = await provider.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="qwen3.5:9b",
        )
        assert result == "Hello from Ollama"


class TestLLMClientFactory:
    def test_create_provider_openai(self, mock_provider_config):
        provider = LLMClientFactory.create_provider("openai", mock_provider_config)
        assert isinstance(provider, OpenAIProvider)

    def test_create_provider_ollama(self, mock_ollama_config):
        provider = LLMClientFactory.create_provider("ollama", mock_ollama_config)
        assert isinstance(provider, OllamaProvider)

    def test_create_provider_unsupported(self, mock_provider_config):
        with pytest.raises(LLMConfigError, match="Unsupported provider type"):
            LLMClientFactory.create_provider("unknown", mock_provider_config)

    @pytest.mark.asyncio
    async def test_get_use_case_config(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        config = await LLMClientFactory.get_use_case_config(mock_db, "email_classification")
        assert config is None
