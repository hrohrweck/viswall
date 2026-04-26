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
            username="dnssuper",
            email="dnssuper@example.com",
            password_hash=get_password_hash("dnssuperpass"),
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
            name="dns-sec-instance",
            hostname="dns-sec-1.example.local",
            api_endpoint="https://dns-sec-1.example.local",
            api_key="dns-sec-key",
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


class TestDNSSecurity:
    async def test_tsig_key_lifecycle(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnssuper", "dnssuperpass")
        headers = {"Authorization": f"Bearer {token}"}

        server_resp = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "dns-tsig"},
            headers=headers,
        )
        assert server_resp.status_code == 201
        server_id = server_resp.json()["id"]

        tsig_create = await client.post(
            f"/api/v1/dns/servers/{server_id}/tsig-keys",
            json={"name": "axfr-key-a", "algorithm": "hmac-sha256"},
            headers=headers,
        )
        assert tsig_create.status_code == 201
        key = tsig_create.json()
        assert key["secret"]
        key_id = key["id"]
        old_secret = key["secret"]

        tsig_rotate = await client.post(
            f"/api/v1/dns/tsig-keys/{key_id}/rotate",
            json={"algorithm": "hmac-sha512"},
            headers=headers,
        )
        assert tsig_rotate.status_code == 200
        rotated = tsig_rotate.json()
        assert rotated["algorithm"] == "hmac-sha512"
        assert rotated["secret"] != old_secret

        tsig_list = await client.get(
            f"/api/v1/dns/servers/{server_id}/tsig-keys",
            headers=headers,
        )
        assert tsig_list.status_code == 200
        assert len(tsig_list.json()) == 1

        tsig_delete = await client.delete(
            f"/api/v1/dns/tsig-keys/{key_id}",
            headers=headers,
        )
        assert tsig_delete.status_code == 204

        tsig_list_after = await client.get(
            f"/api/v1/dns/servers/{server_id}/tsig-keys",
            headers=headers,
        )
        assert tsig_list_after.status_code == 200
        assert tsig_list_after.json()[0]["is_active"] is False

    async def test_dnssec_sign_and_rollover(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnssuper", "dnssuperpass")
        headers = {"Authorization": f"Bearer {token}"}

        server_resp = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "dns-dnssec"},
            headers=headers,
        )
        assert server_resp.status_code == 201
        server_id = server_resp.json()["id"]

        zone_resp = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "secure.example", "zone_type": "master", "dnssec_enabled": False},
            headers=headers,
        )
        assert zone_resp.status_code == 201
        zone_id = zone_resp.json()["id"]

        sign_resp = await client.post(f"/api/v1/dns/zones/{zone_id}/sign", headers=headers)
        assert sign_resp.status_code == 200
        assert sign_resp.json()["dnssec_enabled"] is True

        keys_resp = await client.get(f"/api/v1/dns/zones/{zone_id}/dnssec-keys", headers=headers)
        assert keys_resp.status_code == 200
        keys = keys_resp.json()
        assert len(keys) >= 2
        active_keys = [item for item in keys if item["is_active"]]
        assert any(item["key_type"] == "KSK" for item in active_keys)
        assert any(item["key_type"] == "ZSK" for item in active_keys)

        rollover_resp = await client.post(
            f"/api/v1/dns/zones/{zone_id}/dnssec-rollover",
            json={"key_type": "ZSK", "algorithm": "ECDSAP256SHA256", "key_size": 256},
            headers=headers,
        )
        assert rollover_resp.status_code == 200
        rolled = rollover_resp.json()
        assert rolled["key_type"] == "ZSK"
        assert rolled["is_active"] is True

        unsign_resp = await client.post(f"/api/v1/dns/zones/{zone_id}/unsign", headers=headers)
        assert unsign_resp.status_code == 200
        assert unsign_resp.json()["dnssec_enabled"] is False
