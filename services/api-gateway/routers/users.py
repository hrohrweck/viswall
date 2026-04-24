from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from shared.database import get_db
from shared.models import User
from shared.schemas import UserCreate, UserUpdate, UserResponse, UserPasswordChange
from shared.security import require_admin, get_password_hash, require_auth

router = APIRouter()

@router.get("", response_model=List[UserResponse])
async def list_users(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    from sqlalchemy import select
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]

@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    from sqlalchemy import select
    
    # Check for existing username
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check for existing email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        username=data.username,
        email=data.email,
        auth_backend=data.auth_backend.value,
        role=data.role.value,
        instances=data.instances
    )
    
    if data.password:
        user.password_hash = get_password_hash(data.password)
    
    db.add(user)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="create", resource_type="user", resource_id=user.id)

    await db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.get("/{target_user_id}", response_model=UserResponse)
async def get_user(
    target_user_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == target_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)

@router.patch("/{target_user_id}", response_model=UserResponse)
async def update_user(
    target_user_id: int,
    data: UserUpdate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == target_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "role" and value:
            value = value.value
        setattr(user, field, value)
    
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="update", resource_type="user", resource_id=str(data.id))

    await db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/{target_user_id}", status_code=204)
async def delete_user(
    target_user_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == target_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="delete", resource_type="user", resource_id=str(user_id))

    
    return None

@router.post("/{target_user_id}/change-password")
async def change_password(
    target_user_id: int,
    data: UserPasswordChange,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Change user password (self or admin)"""
    from sqlalchemy import select
    
    # Users can only change their own password unless they're admin
    if user_id != target_user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        current_user = result.scalar_one()
        if current_user.role not in ["superadmin", "admin"]:
            raise HTTPException(status_code=403, detail="Cannot change other user's password")
    
    result = await db.execute(select(User).where(User.id == target_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.auth_backend != "local":
        raise HTTPException(status_code=400, detail="Cannot change password for LDAP/AD users")
    
    # Verify current password
    from shared.security import verify_password
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    
    return {"status": "success"}
