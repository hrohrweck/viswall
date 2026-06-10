"""Proper tests for authentication endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from shared.database import get_db
from shared.models import Base, User
from shared.security import get_password_hash
from main import app

pytestmark = pytest.mark.asyncio


# Use async SQLite for isolated tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_user():
    """Create a standard test user in the database."""
    async with TestSessionLocal() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("testpass"),
            auth_backend="local",
            role="user",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def test_admin():
    """Create an admin test user in the database."""
    async with TestSessionLocal() as session:
        user = User(
            username="testadmin",
            email="admin@example.com",
            password_hash=get_password_hash("adminpass"),
            auth_backend="local",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def disabled_user():
    """Create a disabled test user in the database."""
    async with TestSessionLocal() as session:
        user = User(
            username="disableduser",
            email="disabled@example.com",
            password_hash=get_password_hash("disabledpass"),
            auth_backend="local",
            role="user",
            is_active=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


class TestLogin:
    async def test_login_missing_fields(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_valid_user(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"

    async def test_login_disabled_user(self, client: AsyncClient, disabled_user):
        response = await client.post("/api/v1/auth/login", json={
            "username": "disableduser",
            "password": "disabledpass"
        })
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestGetCurrentUser:
    async def test_me_without_token(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_me_with_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401

    async def test_me_with_valid_token(self, client: AsyncClient, test_user):
        # Login to get token
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_resp.json()["access_token"]

        # Use token to fetch current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    async def test_me_admin_user(self, client: AsyncClient, test_admin):
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "adminpass"
        })
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"
