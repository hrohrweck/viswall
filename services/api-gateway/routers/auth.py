from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from shared.database import get_db
from shared.models import User
from shared.schemas import LoginRequest, LoginResponse, UserResponse, LDAPConfig
from shared.security import verify_password, create_access_token, get_password_hash, require_auth, require_admin

router = APIRouter()


# In-memory store for LDAP config (would be database table in production)
_ldap_config_store: Optional[dict] = None


def _get_ldap_config() -> Optional[LDAPConfig]:
    """Get configured LDAP settings if available."""
    global _ldap_config_store
    if _ldap_config_store is None:
        return None
    return LDAPConfig(**_ldap_config_store)


async def _authenticate_ldap(username: str, password: str) -> dict:
    """Authenticate user against LDAP/AD and return user attributes.

    Raises HTTPException on failure.
    """
    config = _get_ldap_config()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LDAP/AD not configured",
        )

    try:
        import ldap3
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LDAP library not installed",
        )

    try:
        server = ldap3.Server(config.server_url)

        # First, bind with service account to search for the user
        conn = ldap3.Connection(
            server,
            user=config.bind_dn,
            password=config.bind_password,
            auto_bind=True,
        )

        # Search for the user
        search_filter = f"(&{config.user_filter}(cn={username}))"
        conn.search(
            search_base=config.base_dn,
            search_filter=search_filter,
            search_scope=ldap3.SUBTREE,
            attributes=["cn", "mail", "givenName", "sn", "memberOf"],
            size_limit=1,
        )

        if not conn.entries:
            conn.unbind()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        email = user_entry.mail.value if hasattr(user_entry, "mail") else None
        first_name = user_entry.givenName.value if hasattr(user_entry, "givenName") else None
        last_name = user_entry.sn.value if hasattr(user_entry, "sn") else None

        conn.unbind()

        # Now bind with the user's credentials to verify password
        user_conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            auto_bind=True,
        )
        user_conn.unbind()

        return {
            "username": username,
            "email": email or f"{username}@localhost",
            "first_name": first_name,
            "last_name": last_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"LDAP authentication failed: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by username
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user:
        # For LDAP/AD, try to authenticate even if user doesn't exist locally yet
        # (auto-provisioning). First check if we have any LDAP config.
        if _get_ldap_config() is not None:
            try:
                ldap_attrs = await _authenticate_ldap(credentials.username, credentials.password)
                # Auto-create user
                user = User(
                    username=ldap_attrs["username"],
                    email=ldap_attrs["email"],
                    auth_backend="ldap",
                    role="user",
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            except HTTPException:
                # LDAP auth failed
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                )
        else:
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
        # Authenticate against LDAP/AD
        await _authenticate_ldap(credentials.username, credentials.password)
        # Update email if it changed
        # (In a real implementation, we'd sync more attributes here)

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


# ============================================================================
# LDAP Configuration (admin only)
# ============================================================================

@router.get("/ldap-config", response_model=Optional[LDAPConfig])
async def get_ldap_config(
    user_id: int = Depends(require_admin),
):
    """Get current LDAP configuration (admin only)"""
    config = _get_ldap_config()
    if config is None:
        return None
    # Don't return the bind password
    return LDAPConfig(
        server_url=config.server_url,
        bind_dn=config.bind_dn,
        bind_password="",  # Mask password
        base_dn=config.base_dn,
        user_filter=config.user_filter,
        group_filter=config.group_filter,
    )


@router.post("/ldap-config", response_model=LDAPConfig)
async def set_ldap_config(
    config: LDAPConfig,
    user_id: int = Depends(require_admin),
):
    """Save LDAP configuration (admin only)"""
    global _ldap_config_store
    _ldap_config_store = config.model_dump()
    return config


@router.delete("/ldap-config")
async def delete_ldap_config(
    user_id: int = Depends(require_admin),
):
    """Clear LDAP configuration (admin only)"""
    global _ldap_config_store
    _ldap_config_store = None
    return {"status": "success", "message": "LDAP configuration cleared"}


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
