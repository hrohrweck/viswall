from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import secrets

from shared.database import get_db
from shared.models import User, Instance
from shared.schemas import (
    InstanceCreate, InstanceUpdate, InstanceResponse,
    UserResponse
)
from shared.security import require_auth, require_admin

router = APIRouter()

@router.get("", response_model=List[InstanceResponse])
async def list_instances(
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List all instances accessible to the current user"""
    # Get user's accessible instances
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    if user.role == "superadmin":
        # Superadmins see all instances
        result = await db.execute(select(Instance))
    else:
        # Others see only their assigned instances
        result = await db.execute(
            select(Instance).where(Instance.id.in_(user.instances or []))
        )
    
    instances = result.scalars().all()
    return [InstanceResponse.model_validate(i) for i in instances]

@router.post("", response_model=InstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_instance(
    data: InstanceCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Register a new viswall instance"""
    # Generate API key for instance
    api_key = f"vis_{secrets.token_urlsafe(32)}"
    
    instance = Instance(
        name=data.name,
        hostname=data.hostname,
        api_endpoint=f"https://{data.hostname}/api/v1",  # Default
        api_key=api_key,
        capabilities=data.capabilities,
        status="inactive"  # Will be updated when instance connects
    )
    
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    
    return InstanceResponse.model_validate(instance)

@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get instance details"""
    # Verify user has access
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this instance"
        )
    
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    return InstanceResponse.model_validate(instance)

@router.patch("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: int,
    data: InstanceUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update instance configuration"""
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(instance, field, value)
    
    await db.commit()
    await db.refresh(instance)
    
    return InstanceResponse.model_validate(instance)

@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instance(
    instance_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Remove an instance from management"""
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    await db.delete(instance)
    await db.commit()
    
    return None

@router.post("/{instance_id}/heartbeat")
async def instance_heartbeat(
    instance_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Receive heartbeat from an instance (called by instances)"""
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.api_key == data.get("api_key"))
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid instance or API key"
        )
    
    from datetime import datetime
    instance.last_seen = datetime.utcnow()
    instance.status = data.get("status", "active")
    
    await db.commit()
    
    # Return any pending configuration changes
    return {"status": "ok", "config_version": instance.config.get("version", 1)}
