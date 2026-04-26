import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from shared.database import get_db
from shared.models import Base, DHCPLease, Instance, User
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
            username="dhcpadmin",
            email="dhcpadmin@example.com",
            password_hash=get_password_hash("dhcpadminpass"),
            auth_backend="local",
            role="admin",
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
            username="dhcpreader",
            email="dhcpreader@example.com",
            password_hash=get_password_hash("dhcpreaderpass"),
            auth_backend="local",
            role="readonly",
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
            name="dhcp-instance-1",
            hostname="dhcp1.example.local",
            api_endpoint="https://dhcp1.example.local",
            api_key="dhcp-key-1",
            status="active",
            capabilities=["dhcp"],
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


async def _login(client: AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestDHCPModule:
    async def test_create_list_update_server_and_subnet_flow(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "dhcpadmin", "dhcpadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dhcp/servers/{instance.id}",
            json={
                "name": "kea-main",
                "dhcpv4_enabled": True,
                "dhcpv6_enabled": True,
                "ha_enabled": False,
            },
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        list_servers = await client.get(f"/api/v1/dhcp/servers/{instance.id}", headers=headers)
        assert list_servers.status_code == 200
        assert len(list_servers.json()) == 1

        update_server = await client.patch(
            f"/api/v1/dhcp/servers/{server_id}",
            json={"ha_enabled": True, "ha_peer_address": "10.0.0.2", "ha_mode": "hot-standby"},
            headers=headers,
        )
        assert update_server.status_code == 200
        assert update_server.json()["ha_enabled"] is True

        start_server = await client.post(
            f"/api/v1/dhcp/servers/{server_id}/actions/start", headers=headers
        )
        assert start_server.status_code == 200

        create_subnet = await client.post(
            f"/api/v1/dhcp/servers/{server_id}/subnets",
            json={
                "name": "lan-v4",
                "subnet": "192.168.10.0/24",
                "type": "v4",
                "lease_time_min": 300,
                "lease_time_default": 3600,
                "lease_time_max": 7200,
                "routers": ["192.168.10.1"],
                "dns_servers": ["192.168.10.53"],
            },
            headers=headers,
        )
        assert create_subnet.status_code == 201
        subnet_id = create_subnet.json()["id"]

        create_pool = await client.post(
            f"/api/v1/dhcp/subnets/{subnet_id}/pools",
            json={
                "start_address": "192.168.10.100",
                "end_address": "192.168.10.200",
                "type": "v4",
            },
            headers=headers,
        )
        assert create_pool.status_code == 201
        pool_id = create_pool.json()["id"]

        create_reservation = await client.post(
            f"/api/v1/dhcp/subnets/{subnet_id}/reservations",
            json={
                "hostname": "printer-01",
                "ip_address": "192.168.10.20",
                "hw_address": "aa:bb:cc:dd:ee:ff",
                "type": "v4",
                "description": "Office printer",
            },
            headers=headers,
        )
        assert create_reservation.status_code == 201
        reservation_id = create_reservation.json()["id"]

        create_option = await client.post(
            f"/api/v1/dhcp/subnets/{subnet_id}/options",
            json={
                "option_code": 66,
                "option_name": "tftp-server-name",
                "option_value": "192.168.10.2",
                "type": "v4",
            },
            headers=headers,
        )
        assert create_option.status_code == 201
        option_id = create_option.json()["id"]

        list_subnets = await client.get(
            f"/api/v1/dhcp/servers/{server_id}/subnets", headers=headers
        )
        assert list_subnets.status_code == 200
        assert list_subnets.json()[0]["pools_count"] == 1
        assert list_subnets.json()[0]["reservations_count"] == 1

        list_pools = await client.get(f"/api/v1/dhcp/subnets/{subnet_id}/pools", headers=headers)
        assert list_pools.status_code == 200
        assert len(list_pools.json()) == 1

        list_reservations = await client.get(
            f"/api/v1/dhcp/subnets/{subnet_id}/reservations", headers=headers
        )
        assert list_reservations.status_code == 200
        assert len(list_reservations.json()) == 1

        list_options = await client.get(
            f"/api/v1/dhcp/subnets/{subnet_id}/options", headers=headers
        )
        assert list_options.status_code == 200
        assert len(list_options.json()) == 1

        delete_option = await client.delete(f"/api/v1/dhcp/options/{option_id}", headers=headers)
        assert delete_option.status_code == 204

        delete_reservation = await client.delete(
            f"/api/v1/dhcp/reservations/{reservation_id}", headers=headers
        )
        assert delete_reservation.status_code == 204

        delete_pool = await client.delete(f"/api/v1/dhcp/pools/{pool_id}", headers=headers)
        assert delete_pool.status_code == 204

    async def test_readonly_cannot_create_dhcp_server(
        self, client: AsyncClient, readonly_user, instance
    ):
        token = await _login(client, "dhcpreader", "dhcpreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/dhcp/servers/{instance.id}",
            json={"name": "blocked-dhcp", "dhcpv4_enabled": True, "dhcpv6_enabled": False},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_lease_listing_and_release(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dhcpadmin", "dhcpadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dhcp/servers/{instance.id}",
            json={"name": "kea-leases", "dhcpv4_enabled": True, "dhcpv6_enabled": False},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_subnet = await client.post(
            f"/api/v1/dhcp/servers/{server_id}/subnets",
            json={
                "name": "lease-subnet",
                "subnet": "10.50.0.0/24",
                "type": "v4",
                "lease_time_min": 300,
                "lease_time_default": 1200,
                "lease_time_max": 3600,
            },
            headers=headers,
        )
        assert create_subnet.status_code == 201
        subnet_id = create_subnet.json()["id"]

        create_pool = await client.post(
            f"/api/v1/dhcp/subnets/{subnet_id}/pools",
            json={
                "start_address": "10.50.0.100",
                "end_address": "10.50.0.180",
                "type": "v4",
            },
            headers=headers,
        )
        assert create_pool.status_code == 201
        pool_id = create_pool.json()["id"]

        now = datetime.utcnow()
        async with TestSessionLocal() as session:
            lease = DHCPLease(
                subnet_id=subnet_id,
                pool_id=pool_id,
                ip_address="10.50.0.110",
                hw_address="52:54:00:12:34:56",
                hostname="test-client",
                client_id="client-1",
                lease_start=now,
                lease_end=now + timedelta(hours=1),
                state="active",
            )
            session.add(lease)
            await session.commit()
            await session.refresh(lease)
            lease_id = lease.id

        list_active = await client.get("/api/v1/dhcp/leases/active", headers=headers)
        assert list_active.status_code == 200
        assert len(list_active.json()) == 1
        assert list_active.json()[0]["id"] == lease_id

        subnet_leases = await client.get(f"/api/v1/dhcp/subnets/{subnet_id}/leases", headers=headers)
        assert subnet_leases.status_code == 200
        assert subnet_leases.json()[0]["state"] == "active"

        release = await client.delete(f"/api/v1/dhcp/leases/{lease_id}", headers=headers)
        assert release.status_code == 200
        assert release.json()["state"] == "released"

        async with TestSessionLocal() as session:
            result = await session.execute(select(DHCPLease).where(DHCPLease.id == lease_id))
            lease = result.scalar_one()
            assert lease.state == "released"
