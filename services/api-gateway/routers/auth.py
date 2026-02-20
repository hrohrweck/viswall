from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from shared.database import get_db
from shared.models import User
from shared.schemas import LoginRequest, LoginResponse, UserResponse, LDAPConfig
from shared.security import verify_password, create_access_token, get_password_hash, require_auth, require_admin

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by username
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    # Handle different auth backends
    if user.auth_backend == "local":
        if not user.password_hash or not verify_password(
            credentials.password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
    elif user.auth_backend in ["ldap", "ad"]:
        # TODO: Implement LDAP/AD authentication
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{user.auth_backend.upper()} authentication not yet implemented",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "username": user.username}
    )

    return LoginResponse(
        access_token=access_token, user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: int = Depends(require_auth), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.post("/test-ldap")
async def test_ldap_connection(config: LDAPConfig):
    """Test LDAP connection without saving"""
    try:
        import ldap3

        server = ldap3.Server(config.server_url)
        conn = ldap3.Connection(
            server, user=config.bind_dn, password=config.bind_password, auto_bind=True
        )

        # Test search
        conn.search(
            search_base=config.base_dn,
            search_filter=config.user_filter,
            search_scope=ldap3.SUBTREE,
            attributes=["cn", "mail"],
            size_limit=1,
        )

        conn.unbind()
        return {"status": "success", "message": "LDAP connection successful"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LDAP connection failed: {str(e)}",
        )

