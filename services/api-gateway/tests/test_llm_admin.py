"""Tests for LLM admin endpoints: test-connection, model discovery, and sync."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock

import routers.llm_admin as llm_admin_router
from main import app
from shared.database import get_db
from shared.llm_client import LLMError
from shared.models import Base, LLMModel, LLMProvider, User
from shared.security import get_password_hash


pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            username="llmadmin",
            email="llmadmin@example.com",
            password_hash=get_password_hash("llmadminpass"),
            auth_backend="local",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "llmadmin", "password": "llmadminpass"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _seed_provider(**overrides) -> LLMProvider:
    async with TestSessionLocal() as session:
        provider = LLMProvider(
            name=overrides.get("name", "Local Ollama"),
            provider_type=overrides.get("provider_type", "ollama"),
            base_url=overrides.get("base_url", "http://ollama:11434"),
            api_key=overrides.get("api_key"),
            is_enabled=True,
            is_default=True,
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        return provider


async def _seed_model(provider_id: int, name: str, is_enabled: bool) -> LLMModel:
    async with TestSessionLocal() as session:
        model = LLMModel(
            provider_id=provider_id,
            name=name,
            display_name=name,
            is_enabled=is_enabled,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return model


class _FakeClient:
    """Stands in for a BaseLLMProvider inside llm_admin endpoints."""

    def __init__(self, chat_response="ok", discovered=None, list_error=None):
        self.chat = AsyncMock(return_value=chat_response)
        self._discovered = discovered or []
        self._list_error = list_error

    async def list_models(self):
        if self._list_error:
            raise self._list_error
        return self._discovered


def _patch_factory(monkeypatch, fake_client):
    created_with = {}

    def _factory(provider_type, provider_config, http_client=None):
        created_with["provider_type"] = provider_type
        return fake_client

    monkeypatch.setattr(llm_admin_router.LLMClientFactory, "create_provider", _factory)
    return created_with


async def _get_models(provider_id: int):
    async with TestSessionLocal() as session:
        result = await session.execute(
            LLMModel.__table__.select().where(LLMModel.provider_id == provider_id)
        )
        return [dict(row) for row in result.mappings().all()]


class TestProviderTestConnection:
    async def test_explicit_model_wins(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        await _seed_model(provider.id, "stored:latest", is_enabled=True)
        fake = _FakeClient(chat_response="ok fine")
        created_with = _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            json={"model": "explicit:1b"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["model"] == "explicit:1b"
        assert "ok fine" in body["response"]
        assert created_with["provider_type"] == "ollama"
        fake.chat.assert_awaited_once()
        assert fake.chat.await_args.kwargs["model"] == "explicit:1b"

    async def test_falls_back_to_enabled_stored_model(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        await _seed_model(provider.id, "qwen3.5:9b", is_enabled=True)
        fake = _FakeClient()
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["model"] == "qwen3.5:9b"

    async def test_falls_back_to_discovered_model(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(discovered=[{"id": "llama3:8b"}])
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["model"] == "llama3:8b"

    async def test_400_when_no_models_available(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(list_error=LLMError("cannot reach"))
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "No models available" in response.json()["detail"]

    async def test_custom_provider_treated_as_openai_compatible(self, client, admin_user, monkeypatch):
        provider = await _seed_provider(provider_type="custom", base_url="http://llm.internal:8000")
        fake = _FakeClient()
        created_with = _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            json={"model": "mymodel"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert created_with["provider_type"] == "openai"

    async def test_provider_error_maps_to_502(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        await _seed_model(provider.id, "qwen3.5:9b", is_enabled=True)
        fake = _FakeClient()
        fake.chat = AsyncMock(side_effect=LLMError("Ollama API error: connection refused"))
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/test",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 502
        assert "connection refused" in response.json()["detail"]


class TestModelDiscovery:
    async def test_discover_returns_provider_models(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(discovered=[
            {"id": "qwen3.5:9b", "size": 5_000_000_000, "display_name": "qwen3.5:9b"},
            {"id": "llama3:8b"},
        ])
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.get(
            f"/api/v1/admin/llm/providers/{provider.id}/models/discover",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["provider_id"] == provider.id
        assert body["provider_type"] == "ollama"
        assert [m["id"] for m in body["models"]] == ["qwen3.5:9b", "llama3:8b"]

    async def test_discover_unreachable_maps_to_502(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(list_error=LLMError("connect timeout"))
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.get(
            f"/api/v1/admin/llm/providers/{provider.id}/models/discover",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 502
        assert "connect timeout" in response.json()["detail"]

    async def test_discover_400_for_custom_provider(self, client, admin_user, monkeypatch):
        provider = await _seed_provider(provider_type="custom")
        _patch_factory(monkeypatch, _FakeClient())

        token = await _login(client)
        response = await client.get(
            f"/api/v1/admin/llm/providers/{provider.id}/models/discover",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400


class TestModelSync:
    async def test_sync_creates_disabled_models(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(discovered=[{"id": "m1"}, {"id": "m2"}])
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/models/sync",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["discovered"] == 2
        assert body["created"] == 2

        models = await _get_models(provider.id)
        assert {m["name"] for m in models} == {"m1", "m2"}
        assert all(m["is_enabled"] is False for m in models)

    async def test_sync_keeps_existing_enabled_state(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        await _seed_model(provider.id, "qwen3.5:9b", is_enabled=True)
        fake = _FakeClient(discovered=[{"id": "qwen3.5:9b"}, {"id": "new:1b"}])
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/models/sync",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["created"] == 1

        models = await _get_models(provider.id)
        by_name = {m["name"]: m for m in models}
        assert by_name["qwen3.5:9b"]["is_enabled"] is True
        assert by_name["new:1b"]["is_enabled"] is False

    async def test_sync_unreachable_maps_to_502(self, client, admin_user, monkeypatch):
        provider = await _seed_provider()
        fake = _FakeClient(list_error=LLMError("no route to host"))
        _patch_factory(monkeypatch, fake)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/admin/llm/providers/{provider.id}/models/sync",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 502
