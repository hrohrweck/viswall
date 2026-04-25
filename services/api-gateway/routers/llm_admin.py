"""
LLM Provider Admin Router

CRUD endpoints for managing LLM providers, models, and use-case configurations.
All endpoints require admin access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from shared.database import get_db
from shared.security import require_admin
from shared.models import LLMProvider, LLMModel, LLMUseCaseConfig
from shared.schemas import (
    LLMProviderCreate, LLMProviderUpdate, LLMProviderResponse,
    LLMModelCreate, LLMModelUpdate, LLMModelResponse,
    LLMUseCaseConfigCreate, LLMUseCaseConfigUpdate, LLMUseCaseConfigResponse,
)
from shared.llm_client import LLMClientFactory, LLMConfigError

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


@router.post("/providers/{provider_id}/test")
async def test_llm_provider(
    provider_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test connectivity to an LLM provider."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        client = LLMClientFactory.create_provider(provider.provider_type, provider)
        # Send a minimal test prompt
        test_response = await client.chat(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            model="qwen3.5:9b",  # Use default model; caller can override if needed
            max_tokens=10,
        )
        return {"status": "success", "response": test_response[:100]}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider test failed: {str(e)}")


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
