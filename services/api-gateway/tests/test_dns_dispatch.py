"""Tests for DNS desired-state composition and gateway→agent dispatch."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.dns as dns_router
from main import app
from shared.database import get_db
from shared.models import Base, DNSRecord, DNSServer, DNSZone, Instance, User
from shared.security import get_password_hash
from utils.agent_client import AgentClientError, AgentConnectionError


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
            username="dnsdisp",
            email="dnsdisp@example.com",
            password_hash=get_password_hash("dnsdisppass"),
            auth_backend="local",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def instance():
    async with TestSessionLocal() as session:
        item = Instance(
            name="dispatch-instance",
            hostname="node0.example.local",
            api_endpoint="http://fallback-agent:9000",
            api_key="placeholder-inst-key",
            status="active",
            capabilities=["dns"],
            config={"agent_endpoints": {"dns": "http://dns-agent:8082"}},
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


async def _seed_server_with_zone(instance_id: int) -> int:
    async with TestSessionLocal() as session:
        server = DNSServer(
            instance_id=instance_id,
            name="bind-main",
            is_recursive=False,
            allow_transfer=["93.111.66.28"],
            also_notify=["93.111.66.28"],
        )
        session.add(server)
        await session.flush()
        zone = DNSZone(
            server_id=server.id,
            name="example.com",
            zone_type="master",
            serial=2026090512,
        )
        session.add(zone)
        await session.flush()
        session.add(
            DNSRecord(
                zone_id=zone.id,
                name="@",
                record_type="SOA",
                content="dns1.example.com. admin.example.com. 2026090512 3600 600 86400 3600",
            )
        )
        await session.commit()
        return server.id


async def _login(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "dnsdisp", "password": "dnsdisppass"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestBuildInstanceDnsPayload:
    async def test_composes_all_enabled_servers_into_one_payload(self, instance):
        from utils.dns_dispatch import build_instance_dns_payload

        server_id = await _seed_server_with_zone(instance.id)
        async with TestSessionLocal() as session:
            payload = await build_instance_dns_payload(session, instance.id)

        assert payload["server_id"] == server_id
        assert payload["is_recursive"] is False
        assert payload["allow_transfer"] == ["93.111.66.28"]
        assert payload["also_notify"] == ["93.111.66.28"]
        assert [zone["name"] for zone in payload["zones"]] == ["example.com"]
        assert payload["zones"][0]["records"][0]["record_type"] == "SOA"

    async def test_no_enabled_servers_yields_safe_empty_state(self, instance):
        from utils.dns_dispatch import build_instance_dns_payload

        async with TestSessionLocal() as session:
            payload = await build_instance_dns_payload(session, instance.id)

        assert payload["zones"] == []
        assert payload["is_recursive"] is False


class TestDispatchUsesServiceEndpoint:
    async def test_apply_resolves_dns_endpoint_from_instance_config(self, instance, monkeypatch):
        import utils.dns_dispatch as dispatch
        from utils import agent_client

        await _seed_server_with_zone(instance.id)
        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["url_path"] = path
            captured["service"] = kwargs.get("service")
            captured["json"] = json_data
            return {"success": True}

        monkeypatch.setattr(agent_client, "agent_request", _fake_agent_request)
        monkeypatch.setattr(dispatch, "agent_request", _fake_agent_request)

        async with TestSessionLocal() as session:
            result = await dispatch.apply_dns_config(session, instance.id)

        assert result == {"success": True}
        assert captured["url_path"] == "/dns/apply"
        assert captured["service"] == "dns"
        assert captured["json"]["zones"][0]["name"] == "example.com"


class TestApplyActionEndpoint:
    async def test_apply_returns_502_when_agent_unreachable(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        server_id = await _seed_server_with_zone(instance.id)

        async def _unreachable(db, instance_id):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(dns_router, "apply_dns_config", _unreachable)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/dns/servers/{server_id}/actions/apply",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502
        assert "agent down" in response.json()["detail"]

        async with TestSessionLocal() as session:
            server = await session.get(DNSServer, server_id)
            assert server.status == "error"

    async def test_apply_marks_running_and_returns_agent_result(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        server_id = await _seed_server_with_zone(instance.id)

        async def _ok(db, instance_id):
            return {"success": True, "message": "applied"}

        monkeypatch.setattr(dns_router, "apply_dns_config", _ok)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/dns/servers/{server_id}/actions/apply",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["agent_result"]["success"] is True

        async with TestSessionLocal() as session:
            server = await session.get(DNSServer, server_id)
            assert server.status == "running"


class TestMutationSchedulesBackgroundApply:
    async def test_create_server_schedules_apply(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        calls: list = []

        async def _recorder(instance_id):
            calls.append(instance_id)

        monkeypatch.setattr(dns_router, "apply_dns_config_task", _recorder)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "bind-main", "is_recursive": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert calls == [instance.id]
