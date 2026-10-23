"""Tests for interface live-discovery refresh (routers/network.py, plan todo 22).

Covers the plan todo 25 gateway items:

- POST /network/interfaces/{instance_id}/refresh GETs /interfaces from the
  node agent (service="node") and upserts NetworkInterface rows by name;
- idempotent re-refresh (no duplicates, no phantom updates);
- refresh never deletes rows the agent no longer reports;
- agent unreachable -> 503; malformed agent row -> 502;
- refresh is admin-only (403 for readonly).
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.network as network_router
from main import app
from shared.database import get_db
from shared.models import AuditLog, Base, Instance, NetworkInterface, User
from shared.security import get_password_hash
from utils.agent_client import AgentConnectionError

pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex

LIVE_PAYLOAD = {
    "interfaces": [
        {
            "name": "enp0s31f6",
            "operstate": "UP",
            "up": True,
            "mtu": 1500,
            "mac": "aa:bb:cc:dd:ee:ff",
            "addresses": [
                {"address": "46.4.63.216", "prefixlen": 24, "family": "inet"},
                {"address": "2a01:4f8:140:22ef::2", "prefixlen": 64, "family": "inet6"},
            ],
            "has_default_route": True,
        },
        {
            "name": "docker0",
            "operstate": "UP",
            "up": True,
            "mtu": 1500,
            "mac": "02:42:aa:bb:cc:dd",
            "addresses": [{"address": "172.17.0.1", "prefixlen": 16, "family": "inet"}],
            "has_default_route": False,
        },
        {
            "name": "lo",
            "operstate": "UNKNOWN",
            "up": True,
            "mtu": 65536,
            "mac": "00:00:00:00:00:00",
            "addresses": [{"address": "127.0.0.1", "prefixlen": 8, "family": "inet"}],
            "has_default_route": False,
        },
    ],
    "default_route_interface": "enp0s31f6",
    "default_gateway": "46.4.63.193",
}


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


async def _refresh(
    client: AsyncClient, instance, monkeypatch, agent_result=LIVE_PAYLOAD
) -> tuple:
    captured: dict = {}

    async def fake_agent_request(db, iid, method, path, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["service"] = kwargs.get("service")
        return agent_result

    monkeypatch.setattr(network_router, "agent_request", fake_agent_request)

    token = await _login(client, "netsuper", "netsuperpass")
    response = await client.post(
        f"/api/v1/network/interfaces/{instance.id}/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response, captured


class TestInterfaceRefresh:
    async def test_refresh_upserts_live_interfaces(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        response, captured = await _refresh(client, instance, monkeypatch)

        assert response.status_code == 200
        body = response.json()
        assert body["created"] == 2  # enp0s31f6, docker0 (lo is skipped)
        assert body["updated"] == 0
        assert body["interfaces"] == ["enp0s31f6", "docker0", "lo"]

        assert captured["method"] == "GET"
        assert captured["path"] == "/interfaces"
        assert captured["service"] == "node"

        async with TestSessionLocal() as session:
            rows = (
                await session.execute(
                    select(NetworkInterface).where(
                        NetworkInterface.instance_id == instance.id
                    )
                )
            ).scalars().all()
        by_name = {row.name: row for row in rows}
        assert set(by_name) == {"enp0s31f6", "docker0"}  # never lo
        wan = by_name["enp0s31f6"]
        assert wan.ip_address == "46.4.63.216"
        assert wan.netmask == "255.255.255.0"
        assert wan.gateway == "46.4.63.193"
        assert wan.mtu == 1500
        assert wan.type == "other"
        assert wan.config_type == "dhcp"
        assert wan.enabled is True
        docker = by_name["docker0"]
        assert docker.ip_address == "172.17.0.1"
        assert docker.netmask == "255.255.0.0"
        assert docker.gateway is None

        async with TestSessionLocal() as session:
            audit = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "network_interface",
                        AuditLog.action == "refresh",
                    )
                )
            ).scalars().all()
        assert len(audit) == 1
        assert audit[0].new_value["status"] == "success"

    async def test_refresh_is_idempotent(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        first, _ = await _refresh(client, instance, monkeypatch)
        assert first.json()["created"] == 2

        second, _ = await _refresh(client, instance, monkeypatch)
        assert second.status_code == 200
        assert second.json()["created"] == 0
        assert second.json()["updated"] == 0

        async with TestSessionLocal() as session:
            count = (
                await session.execute(
                    select(NetworkInterface).where(
                        NetworkInterface.instance_id == instance.id
                    )
                )
            ).scalars().all()
        assert len(count) == 2

    async def test_refresh_never_deletes_rows_the_agent_no_longer_reports(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        async with TestSessionLocal() as session:
            session.add(
                NetworkInterface(
                    instance_id=instance.id,
                    name="stale0",
                    type="wan",
                    config_type="static",
                    ip_address="10.0.0.5",
                    enabled=True,
                )
            )
            await session.commit()

        partial = {
            "interfaces": [
                {
                    "name": "enp0s31f6",
                    "up": True,
                    "mtu": 1500,
                    "addresses": [{"address": "46.4.63.216", "prefixlen": 24, "family": "inet"}],
                    "has_default_route": True,
                }
            ],
            "default_gateway": "46.4.63.193",
        }
        response, _ = await _refresh(client, instance, monkeypatch, agent_result=partial)
        assert response.status_code == 200

        async with TestSessionLocal() as session:
            rows = (
                await session.execute(
                    select(NetworkInterface).where(
                        NetworkInterface.instance_id == instance.id
                    )
                )
            ).scalars().all()
        names = {row.name for row in rows}
        assert "stale0" in names
        assert "enp0s31f6" in names

    async def test_refresh_agent_unreachable_returns_503(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        async def unreachable(db, iid, method, path, **kwargs):
            raise AgentConnectionError("cannot connect")

        monkeypatch.setattr(network_router, "agent_request", unreachable)

        token = await _login(client, "netsuper", "netsuperpass")
        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_refresh_malformed_row_returns_502(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        malformed = {"interfaces": [{"mtu": 1500}]}  # no valid 'name'
        response, _ = await _refresh(
            client, instance, monkeypatch, agent_result=malformed
        )
        assert response.status_code == 502
        assert "malformed" in response.json()["detail"]

        # Nothing was written on a malformed response.
        async with TestSessionLocal() as session:
            rows = (
                await session.execute(
                    select(NetworkInterface).where(
                        NetworkInterface.instance_id == instance.id
                    )
                )
            ).scalars().all()
        assert rows == []

    async def test_refresh_requires_admin(
        self, client: AsyncClient, readonly_user, instance
    ):
        token = await _login(client, "netreader", "netreaderpass")
        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


async def _seed_interface(instance, name: str = "enp0s31f6") -> NetworkInterface:
    async with TestSessionLocal() as session:
        iface = NetworkInterface(
            instance_id=instance.id,
            name=name,
            type="other",
            config_type="dhcp",
            enabled=True,
        )
        session.add(iface)
        await session.commit()
        await session.refresh(iface)
        return iface


class TestInterfacePatchAndApply:
    async def test_patch_persists_type(
        self, client: AsyncClient, superadmin_user, instance
    ):
        iface = await _seed_interface(instance)

        token = await _login(client, "netsuper", "netsuperpass")
        response = await client.patch(
            f"/api/v1/network/interfaces/detail/{iface.id}",
            json={"type": "wan", "config_type": "static"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["type"] == "wan"
        assert response.json()["config_type"] == "static"

        async with TestSessionLocal() as session:
            row = (
                await session.execute(
                    select(NetworkInterface).where(NetworkInterface.id == iface.id)
                )
            ).scalar_one()
        assert row.type == "wan"
        assert row.config_type == "static"

    async def test_patch_then_apply_dispatches_patched_config(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        iface = await _seed_interface(instance)

        captured: dict = {}

        async def fake_agent_request(db, iid, method, path, json_data=None, **kwargs):
            captured["method"] = method
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            captured["payload"] = json_data
            return {
                "success": True,
                "changes": [],
                "netplan_written": True,
                "message": "applied",
            }

        token = await _login(client, "netsuper", "netsuperpass")
        headers = {"Authorization": f"Bearer {token}"}

        patched = await client.patch(
            f"/api/v1/network/interfaces/detail/{iface.id}",
            json={"type": "wan", "config_type": "static"},
            headers=headers,
        )
        assert patched.status_code == 200

        monkeypatch.setattr(network_router, "agent_request", fake_agent_request)
        applied = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/apply",
            json={"force": False},
            headers=headers,
        )
        assert applied.status_code == 200

        assert captured["method"] == "POST"
        assert captured["path"] == "/interfaces/apply"
        assert captured["service"] == "node"
        entry = captured["payload"]["interfaces"][0]
        assert entry["name"] == "enp0s31f6"
        assert entry["config_type"] == "static"

    async def test_apply_returns_probe_netplan_passthrough(
        self, client: AsyncClient, superadmin_user, instance, monkeypatch
    ):
        await _seed_interface(instance)

        agent_result = {
            "success": True,
            "changes": [],
            "default_route_interface": "enp0s31f6",
            "netplan_file": "/etc/netplan/60-viswall.yaml",
            "netplan_written": True,
            "message": "netplan accepted",
            "try_mode": True,
            "probes": [
                {"name": "ssh-22", "ok": True},
                {"name": "gateway-127.0.0.1:8010", "ok": True},
                {"name": "ping-46.4.63.193", "ok": True},
            ],
            "netplan_outcome": "accepted",
            "snapshot_dir": "/var/lib/viswall-node/snapshots/20261022T120000Z",
        }

        async def fake_agent_request(db, iid, method, path, json_data=None, **kwargs):
            return agent_result

        monkeypatch.setattr(network_router, "agent_request", fake_agent_request)

        token = await _login(client, "netsuper", "netsuperpass")
        response = await client.post(
            f"/api/v1/network/interfaces/{instance.id}/apply",
            json={"force": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["try_mode"] is True
        assert [p["name"] for p in body["probes"]] == [
            "ssh-22",
            "gateway-127.0.0.1:8010",
            "ping-46.4.63.193",
        ]
        assert body["netplan_outcome"] == "accepted"
        assert body["snapshot_dir"] == "/var/lib/viswall-node/snapshots/20261022T120000Z"
