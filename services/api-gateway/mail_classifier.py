"""
LLM-based email classification engine for Viswall.

Uses the modular LLM client factory (shared.llm_client) to route requests
to the configured provider for the 'email_classification' use case.

Per-domain JSON configuration (llm_config) is deprecated — categories and
provider settings now live in the LLM provider registry tables.
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from shared.llm_client import LLMClientFactory, LLMError

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


def _get_categories(categories: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Extract validated category list"""
    cats = categories or DEFAULT_CATEGORIES

    if not isinstance(cats, list):
        cats = DEFAULT_CATEGORIES

    if len(cats) < MIN_CATEGORIES:
        logger.warning(f"Too few categories ({len(cats)}), using defaults")
        cats = DEFAULT_CATEGORIES
    if len(cats) > MAX_CATEGORIES:
        logger.warning(f"Too many categories ({len(cats)}), truncating to {MAX_CATEGORIES}")
        cats = cats[:MAX_CATEGORIES]

    validated = []
    for cat in cats:
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
    db: AsyncSession,
    subject: str,
    sender: str,
    body_preview: Optional[str],
    categories: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Classify an email using the 'email_classification' use-case config.

    Args:
        db: Database session for looking up provider configuration.
        subject: Email subject line.
        sender: Email sender address.
        body_preview: Optional body preview text.
        categories: Optional override categories (falls back to defaults).

    Returns:
        Dict with keys: category, confidence, reason, default_action, provider, model.
    """
    validated_categories = _get_categories(categories)
    prompt = _build_prompt(subject, sender, body_preview, validated_categories)

    try:
        result = await LLMClientFactory.classify_for_use_case(
            db=db,
            use_case="email_classification",
            prompt=prompt,
        )
    except LLMError as e:
        raise LLMClassificationError(str(e))

    # Validate result against allowed categories
    if result["category"] not in [c["name"] for c in validated_categories]:
        logger.warning(f"LLM returned invalid category '{result['category']}', defaulting")
        result["category"] = validated_categories[0]["name"]

    # Get default action for the category
    category_map = {c["name"]: c["default_action"] for c in validated_categories}
    result["default_action"] = category_map.get(result["category"], "deliver")

    return result


# Legacy compatibility wrapper — will be removed in a future release.
async def classify_email_with_domain_config(
    subject: str,
    sender: str,
    body_preview: Optional[str],
    llm_config: Dict[str, Any],
) -> Dict[str, Any]:
    """DEPRECATED: Use classify_email(db, ...) instead.

    This wrapper exists for backwards compatibility with code that does not
    yet have access to an AsyncSession. It will raise an error because the
    old per-domain JSON config approach is no longer supported.
    """
    raise LLMClassificationError(
        "classify_email_with_domain_config is deprecated. "
        "Use classify_email(db, subject, sender, body_preview) with the LLM provider registry."
    )
