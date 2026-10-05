"""
LLM Provider Admin Router

CRUD endpoints for managing LLM providers, models, and use-case configurations.
All endpoints require admin access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

import httpx

from shared.database import get_db
from shared.security import require_admin
from shared.models import LLMProvider, LLMModel, LLMUseCaseConfig
from shared.schemas import (
    LLMProviderCreate, LLMProviderUpdate, LLMProviderResponse,
    LLMModelCreate, LLMModelUpdate, LLMModelResponse,
    LLMModelDiscoveryResponse, LLMModelDiscovery, LLMModelSyncResponse,
    LLMProviderTestRequest,
    LLMUseCaseConfigCreate, LLMUseCaseConfigUpdate, LLMUseCaseConfigResponse,
)
from shared.llm_client import LLMClientFactory, LLMConfigError, LLMError

router = APIRouter()


# ============================================================================
# LLM PROVIDERS
# ============================================================================

@router.get("/providers", response_model=List[LLMProviderResponse])
async def list_llm_providers(
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all LLM providers."""
    result = await db.execute(select(LLMProvider).order_by(LLMProvider.id))
    providers = result.scalars().all()
    return providers


@router.post("/providers", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_provider(
    data: LLMProviderCreate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new LLM provider."""
    provider = LLMProvider(**data.model_dump())
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
async def get_llm_provider(
    provider_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single LLM provider."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.patch("/providers/{provider_id}", response_model=LLMProviderResponse)
async def update_llm_provider(
    provider_id: int,
    data: LLMProviderUpdate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an LLM provider."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)
    return provider


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_provider(
    provider_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an LLM provider (cascades to models)."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()


async def _resolve_test_model(
    db: AsyncSession,
    provider: LLMProvider,
    requested_model: Optional[str],
    client,
) -> str:
    """Pick the model to test with: explicit → first enabled → first discovered."""
    if requested_model:
        return requested_model

    result = await db.execute(
        select(LLMModel)
        .where(LLMModel.provider_id == provider.id, LLMModel.is_enabled == True)  # noqa: E712
        .order_by(LLMModel.id)
        .limit(1)
    )
    stored = result.scalar_one_or_none()
    if stored:
        return stored.name

    try:
        discovered = await client.list_models()
    except LLMError:
        discovered = []
    if discovered:
        return discovered[0]["id"]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "No models available for this provider: none configured, enabled, "
            "or discoverable. Sync or add a model first (e.g. pull one in Ollama)."
        ),
    )


@router.post("/providers/{provider_id}/test")
async def test_llm_provider(
    provider_id: int,
    data: Optional[LLMProviderTestRequest] = None,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test connectivity to an LLM provider with a real (small) chat request."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Cold model loads (Ollama) can take a while — allow more than the
    # default 30s client timeout for this diagnostic call.
    http_client = httpx.AsyncClient(timeout=90.0)
    try:
        if provider.provider_type == "custom":
            # "custom" endpoints are treated as OpenAI-compatible.
            client = LLMClientFactory.create_provider(
                "openai", provider, http_client=http_client
            )
        else:
            client = LLMClientFactory.create_provider(
                provider.provider_type, provider, http_client=http_client
            )

        model = await _resolve_test_model(db, provider, data.model if data else None, client)
        test_response = await client.chat(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            model=model,
            max_tokens=10,
        )
        return {"status": "success", "response": test_response[:100], "model": model}
    except HTTPException:
        raise
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"Provider test failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider test failed: {str(e)}")
    finally:
        await http_client.aclose()


# ============================================================================
# LLM MODEL DISCOVERY
# ============================================================================

@router.get("/providers/{provider_id}/models/discover", response_model=LLMModelDiscoveryResponse)
async def discover_provider_models(
    provider_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List the models a live provider advertises (Ollama /api/tags, OpenAI & Anthropic /models)."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.provider_type == "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model discovery is not supported for custom providers. Add models manually.",
        )

    client = LLMClientFactory.create_provider(provider.provider_type, provider)
    try:
        models = await client.list_models()
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach provider '{provider.name}': {str(e)}",
        )

    return LLMModelDiscoveryResponse(
        provider_id=provider.id,
        provider_type=provider.provider_type,
        models=[LLMModelDiscovery(**m) for m in models],
    )


@router.post("/providers/{provider_id}/models/sync", response_model=LLMModelSyncResponse)
async def sync_provider_models(
    provider_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import a provider's advertised models into the registry.

    Newly discovered models are created **disabled**; existing rows keep
    their enabled state (so preconfigured models stay active).
    """
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.provider_type == "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model discovery is not supported for custom providers. Add models manually.",
        )

    client = LLMClientFactory.create_provider(provider.provider_type, provider)
    try:
        discovered = await client.list_models()
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach provider '{provider.name}': {str(e)}",
        )

    existing_result = await db.execute(
        select(LLMModel.name).where(LLMModel.provider_id == provider_id)
    )
    existing = {row[0] for row in existing_result.all()}

    created = 0
    for m in discovered:
        if m["id"] in existing:
            continue
        db.add(LLMModel(
            provider_id=provider_id,
            name=m["id"],
            display_name=m.get("display_name") or m["id"],
            is_enabled=False,
        ))
        created += 1

    if created:
        await db.commit()

    return LLMModelSyncResponse(
        provider_id=provider_id,
        discovered=len(discovered),
        created=created,
    )


# ============================================================================
# LLM MODELS
# ============================================================================

@router.get("/models", response_model=List[LLMModelResponse])
async def list_llm_models(
    provider_id: int = None,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List LLM models, optionally filtered by provider."""
    query = select(LLMModel).order_by(LLMModel.id)
    if provider_id:
        query = query.where(LLMModel.provider_id == provider_id)
    result = await db.execute(query)
    models = result.scalars().all()
    return models


@router.post("/models", response_model=LLMModelResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_model(
    data: LLMModelCreate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new LLM model."""
    # Verify provider exists
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == data.provider_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Provider not found")

    model = LLMModel(**data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.get("/models/{model_id}", response_model=LLMModelResponse)
async def get_llm_model(
    model_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single LLM model."""
    result = await db.execute(select(LLMModel).where(LLMModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.patch("/models/{model_id}", response_model=LLMModelResponse)
async def update_llm_model(
    model_id: int,
    data: LLMModelUpdate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an LLM model."""
    result = await db.execute(select(LLMModel).where(LLMModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_model(
    model_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an LLM model."""
    result = await db.execute(select(LLMModel).where(LLMModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()


# ============================================================================
# LLM USE CASE CONFIGS
# ============================================================================

@router.get("/use-cases", response_model=List[LLMUseCaseConfigResponse])
async def list_llm_use_case_configs(
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all use-case configurations."""
    result = await db.execute(select(LLMUseCaseConfig).order_by(LLMUseCaseConfig.id))
    configs = result.scalars().all()
    return configs


@router.post("/use-cases", response_model=LLMUseCaseConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_use_case_config(
    data: LLMUseCaseConfigCreate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new use-case configuration."""
    config = LLMUseCaseConfig(**data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/use-cases/{config_id}", response_model=LLMUseCaseConfigResponse)
async def get_llm_use_case_config(
    config_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single use-case configuration."""
    result = await db.execute(select(LLMUseCaseConfig).where(LLMUseCaseConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Use-case config not found")
    return config


@router.patch("/use-cases/{config_id}", response_model=LLMUseCaseConfigResponse)
async def update_llm_use_case_config(
    config_id: int,
    data: LLMUseCaseConfigUpdate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a use-case configuration."""
    result = await db.execute(select(LLMUseCaseConfig).where(LLMUseCaseConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Use-case config not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/use-cases/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_use_case_config(
    config_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a use-case configuration."""
    result = await db.execute(select(LLMUseCaseConfig).where(LLMUseCaseConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Use-case config not found")

    await db.delete(config)
    await db.commit()
