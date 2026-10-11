"""Tests for host interface management (routers/network.py) and the
admin-only instance API key reveal endpoint."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.network as network_router
from main import app
from shared.database import get_db
from shared.models import Base, Instance, NetworkInterface, User
from shared.security import get_password_hash
from utils.agent_client import AgentConnectionError

pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


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
async def instance():
    async with TestSessionLocal() as session:
        item = Instance(
            name="net-instance-1",
            hostname="node1.example.local",
            api_endpoint="https://node1.example.local",
            api_key=TEST_INSTANCE_KEY,
            status="active",
            config={"agent_endpoints": {"node": "http://127.0.0.1:8085"}},
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


@pytest_asyncio.fixture
async def superadmin_user():
    async with TestSessionLocal() as session:
        user = User(
            username="netsuper",
            email="netsuper@example.com",
            password_hash=get_password_hash("netsuperpass"),
            auth_backend="local",
            role="superadmin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def scoped_admin_user(instance):
    """Admin whose instance scope excludes the test instance."""
    async with TestSessionLocal() as session:
        user = User(
            username="netscoped",
            email="netscoped@example.com",
            password_hash=get_password_hash("netscopedpass"),
            auth_backend="local",
            role="admin",
            is_active=True,
            instances=[],
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def readonly_user():
    async with TestSessionLocal() as session:
        user = User(
            username="netreader",
            email="netreader@example.com",
            password_hash=get_password_hash("netreaderpass"),
            auth_backend="local",
            role="readonly",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


async def _login(client: AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestInterfaceApi:
    async def test_crud_flow(self, client: AsyncClient, superadmin_user, instance):
        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}

        created = await client.post(
            f"/api/v1/network/interfaces/{instance.id}",
            json={
                "name": "ens18",
                "type": "wan",
                "config_type": "static",
                "ip_address": "10.0.0.5",
                "netmask": "255.255.255.0",
                "gateway": "10.0.0.1",
                "mtu": 1500,
                "description": "uplink",
            },
            headers=headers,
        )
        assert created.status_code == 201
        body = created.json()
        assert body["name"] == "ens18"
        assert body["mtu"] == 1500
        assert body["description"] == "uplink"
        interface_id = body["id"]

        listed = await client.get(
            f"/api/v1/network/interfaces/{instance.id}", headers=headers
        )
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        duplicate = await client.post(
            f"/api/v1/network/interfaces/{instance.id}",
            json={"name": "ens18", "config_type": "dhcp"},
            headers=headers,
        )
        assert duplicate.status_code == 409

        patched = await client.patch(
            f"/api/v1/network/interfaces/detail/{interface_id}",
            json={"mtu": 9000, "description": "jumbo uplink"},
            headers=headers,
        )
        assert patched.status_code == 200
        assert patched.json()["mtu"] == 9000

        deleted = await client.delete(
            f"/api/v1/network/interfaces/detail/{interface_id}", headers=headers
        )
        assert deleted.status_code == 204
        listed_again = await client.get(
            f"/api/v1/network/interfaces/{instance.id}", headers=headers
        )
        assert listed_again.json() == []

    async def test_scoped_admin_cannot_access_other_instance(
        self, client: AsyncClient, scoped_admin_user, instance
    ):
        token = await _login(client, "netscoped", "netscopedpass")
        headers = {"Authorization": f"Bearer {token}"}

        listed = await client.get(
            f"/api/v1/network/interfaces/{instance.id}", headers=headers
        )
        assert listed.status_code == 403

        created = await client.post(
            f"/api/v1/network/interfaces/{instance.id}",
            json={"name": "ens18"},
            headers=headers,
        )
        assert created.status_code == 403

    async def test_readonly_user_cannot_create(
        self, client: AsyncClient, readonly_user, instance
    ):
        token = await _login(client, "netreader", "netreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}",
            json={"name": "ens18"},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_live_relays_agent_state(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        async def fake_agent_request(db, iid, method, path, **kwargs):
            assert method == "GET"
            assert path == "/interfaces"
            return {
                "interfaces": [
                    {
                        "name": "ens18",
                        "operstate": "UP",
                        "up": True,
                        "mtu": 1500,
                        "mac": "aa:bb:cc:dd:ee:ff",
                        "addresses": [{"address": "10.0.0.5", "prefixlen": 24}],
                        "has_default_route": True,
                    }
                ],
                "default_route_interface": "ens18",
                "default_gateway": "10.0.0.1",
            }

        monkeypatch.setattr(network_router, "agent_request", fake_agent_request)

        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"/api/v1/network/interfaces/{instance.id}/live", headers=headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["default_route_interface"] == "ens18"
        assert body["interfaces"][0]["addresses"][0]["address"] == "10.0.0.5"

    async def test_live_returns_503_when_agent_unreachable(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        async def unreachable(db, iid, method, path, **kwargs):
            raise AgentConnectionError("cannot connect")

        monkeypatch.setattr(network_router, "agent_request", unreachable)

        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"/api/v1/network/interfaces/{instance.id}/live", headers=headers
        )
        assert response.status_code == 503

    async def test_apply_dispatches_desired_state(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        captured = {}

        async def fake_agent_request(db, iid, method, path, json_data=None, **kwargs):
            captured["payload"] = json_data
            return {
                "success": True,
                "changes": [
                    {"interface": "ens18", "action": "mtu", "detail": "set mtu 9000", "ok": True}
                ],
                "default_route_interface": "ens18",
                "netplan_file": "/etc/netplan/60-viswall.yaml",
                "netplan_written": True,
                "message": "interface configuration applied",
            }

        monkeypatch.setattr(network_router, "agent_request", fake_agent_request)

        async with TestSessionLocal() as session:
            session.add(
                NetworkInterface(
                    instance_id=instance.id,
                    name="ens18",
                    type="wan",
                    config_type="static",
                    ip_address="10.0.0.5",
                    netmask="255.255.255.0",
                    gateway="10.0.0.1",
                    mtu=9000,
                    enabled=True,
                )
            )
            await session.commit()

        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/apply",
            json={"force": False},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["netplan_written"] is True
        assert captured["payload"]["interfaces"][0]["name"] == "ens18"
        assert captured["payload"]["force"] is False

    async def test_apply_relays_agent_refusal_as_409(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        from utils.agent_client import AgentResponseError

        async def refusing_agent(db, iid, method, path, **kwargs):
            raise AgentResponseError("agent refused: default route", status_code=409)

        monkeypatch.setattr(network_router, "agent_request", refusing_agent)

        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/apply",
            json={"force": False},
            headers=headers,
        )
        assert response.status_code == 409


class TestInstanceApiKey:
    async def test_reveal_returns_key_for_superadmin(
        self, client: AsyncClient, superadmin_user, instance
    ):
        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"/api/v1/instances/{instance.id}/api-key", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["api_key"] == TEST_INSTANCE_KEY
        assert response.json()["instance_id"] == instance.id

    async def test_reveal_denied_for_scoped_admin_without_access(
        self, client: AsyncClient, scoped_admin_user, instance
    ):
        token = await _login(client, "netscoped", "netscopedpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"/api/v1/instances/{instance.id}/api-key", headers=headers
        )
        assert response.status_code == 403

    async def test_reveal_denied_for_readonly(
        self, client: AsyncClient, readonly_user, instance
    ):
        token = await _login(client, "netreader", "netreaderpass")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"/api/v1/instances/{instance.id}/api-key", headers=headers
        )
        assert response.status_code == 403
