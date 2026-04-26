import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from shared.database import get_db
from shared.models import Base, Instance, User
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
            username="dnsadmin",
            email="dnsadmin@example.com",
            password_hash=get_password_hash("dnsadminpass"),
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
            username="dnsreader",
            email="dnsreader@example.com",
            password_hash=get_password_hash("dnsreaderpass"),
            auth_backend="local",
            role="readonly",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def instance(admin_user):
    async with TestSessionLocal() as session:
        item = Instance(
            name="dns-instance-1",
            hostname="dns1.example.local",
            api_endpoint="https://dns1.example.local",
            api_key="dns-key-1",
            status="active",
            capabilities=["dns"],
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


class TestDNSModule:
    async def test_create_list_zone_record_flow(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={
                "name": "bind-main",
                "is_recursive": True,
                "is_authoritative": True,
                "forwarders": ["1.1.1.1", "8.8.8.8"],
            },
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        list_servers = await client.get(f"/api/v1/dns/servers/{instance.id}", headers=headers)
        assert list_servers.status_code == 200
        assert len(list_servers.json()) == 1

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={
                "name": "example.internal",
                "zone_type": "master",
                "dnssec_enabled": True,
            },
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        list_zones = await client.get(f"/api/v1/dns/servers/{server_id}/zones", headers=headers)
        assert list_zones.status_code == 200
        assert len(list_zones.json()) == 1

        create_record = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "www", "record_type": "A", "content": "192.168.10.10", "ttl": 300},
            headers=headers,
        )
        assert create_record.status_code == 201

        list_records = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        assert list_records.status_code == 200
        record_types = [item["record_type"] for item in list_records.json()]
        assert "A" in record_types

    async def test_readonly_cannot_create_dns_server(self, client: AsyncClient, readonly_user, instance):
        token = await _login(client, "dnsreader", "dnsreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "blocked-server", "is_recursive": True},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_reverse_zone_and_ptr_record(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "reverse-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        reverse_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones/reverse",
            json={
                "network": "192.168.50.0/24",
                "nameserver": "ns1.example.internal",
                "admin_email": "admin@example.internal",
            },
            headers=headers,
        )
        assert reverse_zone.status_code == 201
        zone_id = reverse_zone.json()["id"]

        ptr_record = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records/ptr",
            json={
                "ip_address": "192.168.50.42",
                "hostname": "app01.example.internal",
                "ttl": 600,
            },
            headers=headers,
        )
        assert ptr_record.status_code == 200
        assert ptr_record.json()["record_type"] == "PTR"
