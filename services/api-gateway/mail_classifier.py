"""
LLM-based email classification engine for Viswall.

Supports OpenAI, Anthropic Claude, and local models (Ollama).
Categories are configurable per-domain via llm_config.
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default classification categories (7 baseline categories)
DEFAULT_CATEGORIES = [
    {"name": "important", "color": "#10b981", "default_action": "deliver"},
    {"name": "newsletter", "color": "#3b82f6", "default_action": "deliver"},
    {"name": "promotional", "color": "#f59e0b", "default_action": "deliver"},
    {"name": "social", "color": "#8b5cf6", "default_action": "deliver"},
    {"name": "spam", "color": "#ef4444", "default_action": "quarantine"},
    {"name": "phishing", "color": "#dc2626", "default_action": "reject"},
    {"name": "legitimate", "color": "#6b7280", "default_action": "deliver"},
]

# Category validation limits
MAX_CATEGORIES = 10
MIN_CATEGORIES = 2


class LLMClassificationError(Exception):
    """Raised when LLM classification fails"""
    pass


class MailClassifier:
    """Async LLM client for email classification"""

    def __init__(self):
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx is required for LLM classification")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    def _get_categories(self, llm_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract validated category list from domain config"""
        categories = llm_config.get("categories", DEFAULT_CATEGORIES)

        if not isinstance(categories, list):
            categories = DEFAULT_CATEGORIES

        # Validate count
        if len(categories) < MIN_CATEGORIES:
            logger.warning(f"Too few categories ({len(categories)}), using defaults")
            categories = DEFAULT_CATEGORIES
        if len(categories) > MAX_CATEGORIES:
            logger.warning(f"Too many categories ({len(categories)}), truncating to {MAX_CATEGORIES}")
            categories = categories[:MAX_CATEGORIES]

        # Validate each category has required fields
        validated = []
        for cat in categories:
            if isinstance(cat, dict) and "name" in cat:
                validated.append({
                    "name": str(cat["name"])[:50],
                    "color": str(cat.get("color", "#6b7280"))[:20],
                    "default_action": str(cat.get("default_action", "deliver"))[:20],
                })

        if len(validated) < MIN_CATEGORIES:
            return DEFAULT_CATEGORIES

        return validated

    def _build_prompt(
        self,
        subject: str,
        sender: str,
        body_preview: Optional[str],
        categories: List[Dict[str, Any]],
    ) -> str:
        """Build classification prompt"""
        category_names = [c["name"] for c in categories]
        category_list = ", ".join(category_names)

        prompt = f"""Analyze this email and classify it into exactly one of the following categories: {category_list}.

Email details:
- From: {sender}
- Subject: {subject}
"""
        if body_preview:
            prompt += f"- Body preview: {body_preview[:1500]}\n"

        prompt += f"""
Respond ONLY with a JSON object in this exact format:
{{
    "category": "one_of_the_categories",
    "confidence": 0.95,
    "reason": "Brief explanation of why this category was chosen"
}}

Rules:
- The category MUST be exactly one of: {category_list}
- Confidence must be a float between 0.0 and 1.0
- Keep the reason under 200 characters
"""
        return prompt

    async def classify_email(
        self,
        subject: str,
        sender: str,
        body_preview: Optional[str],
        llm_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Classify an email using the configured LLM provider"""
        provider = llm_config.get("provider", "openai")
        api_key = llm_config.get("api_key")
        model = llm_config.get("model", "gpt-4")
        categories = self._get_categories(llm_config)

        if not api_key and provider != "local":
            raise LLMClassificationError(f"API key required for provider: {provider}")

        prompt = self._build_prompt(subject, sender, body_preview, categories)

        # Route to provider-specific handler
        if provider == "openai":
            result = await self._classify_openai(prompt, api_key, model)
        elif provider == "anthropic":
            result = await self._classify_anthropic(prompt, api_key, model)
        elif provider == "local":
            result = await self._classify_local(prompt, model)
        else:
            raise LLMClassificationError(f"Unsupported provider: {provider}")

        # Validate result against allowed categories
        if result["category"] not in [c["name"] for c in categories]:
            logger.warning(f"LLM returned invalid category '{result['category']}', defaulting")
            result["category"] = categories[0]["name"]

        # Get default action for the category
        category_map = {c["name"]: c["default_action"] for c in categories}
        result["default_action"] = category_map.get(result["category"], "deliver")
        result["provider"] = provider
        result["model"] = model

        return result

    async def _classify_openai(self, prompt: str, api_key: str, model: str) -> Dict[str, Any]:
        """Classify using OpenAI API"""
        try:
            response = await self._client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an email classification assistant. Respond only with valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        except httpx.HTTPError as e:
            raise LLMClassificationError(f"OpenAI API error: {e}")
        except (KeyError, IndexError) as e:
            raise LLMClassificationError(f"Invalid OpenAI response: {e}")

    async def _classify_anthropic(self, prompt: str, api_key: str, model: str) -> Dict[str, Any]:
        """Classify using Anthropic Claude API"""
        try:
            response = await self._client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": 200,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"You are an email classification assistant. Respond only with valid JSON.\n\n{prompt}",
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            return self._parse_json_response(content)
        except httpx.HTTPError as e:
            raise LLMClassificationError(f"Anthropic API error: {e}")
        except (KeyError, IndexError) as e:
            raise LLMClassificationError(f"Invalid Anthropic response: {e}")

    async def _classify_local(self, prompt: str, model: str) -> Dict[str, Any]:
        """Classify using local LLM via Ollama"""
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        try:
            response = await self._client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "")
            return self._parse_json_response(content)
        except httpx.HTTPError as e:
            raise LLMClassificationError(f"Local LLM error: {e}")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate JSON response from LLM"""
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMClassificationError(f"Invalid JSON response: {e}")

        # Validate required fields
        if "category" not in parsed:
            raise LLMClassificationError("Missing 'category' field in response")

        # Validate and normalize
        result = {
            "category": str(parsed["category"]).lower().strip(),
            "confidence": float(parsed.get("confidence", 0.5)),
            "reason": str(parsed.get("reason", "No reason provided"))[:200],
        }

        # Clamp confidence
        result["confidence"] = max(0.0, min(1.0, result["confidence"]))

        return result


# Global classifier instance (lazy init)
_classifier: Optional[MailClassifier] = None


def get_classifier() -> MailClassifier:
    """Get or create the global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = MailClassifier()
    return _classifier


async def classify_email_with_domain_config(
    subject: str,
    sender: str,
    body_preview: Optional[str],
    llm_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Convenience function to classify an email"""
    classifier = get_classifier()
    return await classifier.classify_email(subject, sender, body_preview, llm_config)
