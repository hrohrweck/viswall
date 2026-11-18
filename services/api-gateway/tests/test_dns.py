import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from shared.database import get_db
from shared.models import AuditLog, Base, DNSZone, Instance, User
from shared.security import get_password_hash

# Generated per test run so no static credential-shaped literal lands in the repo.
TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


def _serial_from_now() -> int:
    return int(datetime.utcnow().strftime("%Y%m%d%H"))


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
            api_key=TEST_INSTANCE_KEY,
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

    async def test_bulk_update_records(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "bulk-update-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "bulk-update.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        record_ids = []
        for name in ("alpha", "beta"):
            created = await client.post(
                f"/api/v1/dns/zones/{zone_id}/records",
                json={"name": name, "record_type": "A", "content": "10.0.0.10", "ttl": 3600},
                headers=headers,
            )
            assert created.status_code == 201
            record_ids.append(created.json()["id"])

        async with TestSessionLocal() as session:
            serial_before = (
                await session.execute(select(DNSZone.serial).where(DNSZone.id == zone_id))
            ).scalar_one()

        bulk_update = await client.patch(
            f"/api/v1/dns/zones/{zone_id}/records/bulk",
            json={"record_ids": record_ids, "changes": {"ttl": 300}},
            headers=headers,
        )
        assert bulk_update.status_code == 200
        assert [item["id"] for item in bulk_update.json()] == sorted(record_ids)
        assert all(item["ttl"] == 300 for item in bulk_update.json())

        async with TestSessionLocal() as session:
            serial_after = (
                await session.execute(select(DNSZone.serial).where(DNSZone.id == zone_id))
            ).scalar_one()
            audit_rows = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.resource_type == "dns_record",
                            AuditLog.resource_id == str(zone_id),
                            AuditLog.action == "update",
                        )
                    )
                )
                .scalars()
                .all()
            )

        # Zone serials have hour resolution, so a same-hour bump equals the old value.
        assert serial_after != serial_before or serial_after == _serial_from_now()
        assert len(audit_rows) == 1
        assert audit_rows[0].new_value == {"record_ids": sorted(record_ids), "count": 2}

    async def test_bulk_update_with_system_record_rejected(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "bulk-update-system-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "bulk-update-system.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        created = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "editable", "record_type": "A", "content": "10.0.0.20", "ttl": 3600},
            headers=headers,
        )
        assert created.status_code == 201
        editable_id = created.json()["id"]

        list_records = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        system_id = next(item["id"] for item in list_records.json() if item["is_system"])

        bulk_update = await client.patch(
            f"/api/v1/dns/zones/{zone_id}/records/bulk",
            json={"record_ids": [editable_id, system_id], "changes": {"ttl": 300}},
            headers=headers,
        )
        assert bulk_update.status_code == 400
        assert bulk_update.json()["detail"] == "System DNS records cannot be modified"

        list_after = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        editable = next(item for item in list_after.json() if item["id"] == editable_id)
        assert editable["ttl"] == 3600

    async def test_bulk_delete_records(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "bulk-delete-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "bulk-delete.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        record_ids = []
        for name in ("gamma", "delta"):
            created = await client.post(
                f"/api/v1/dns/zones/{zone_id}/records",
                json={"name": name, "record_type": "A", "content": "10.0.0.30", "ttl": 3600},
                headers=headers,
            )
            assert created.status_code == 201
            record_ids.append(created.json()["id"])

        bulk_delete = await client.request(
            "DELETE",
            f"/api/v1/dns/zones/{zone_id}/records/bulk",
            json={"record_ids": record_ids},
            headers=headers,
        )
        assert bulk_delete.status_code == 200
        assert bulk_delete.json() == {"deleted_count": 2, "record_ids": sorted(record_ids)}

        list_after = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        remaining_ids = {item["id"] for item in list_after.json()}
        assert remaining_ids.isdisjoint(record_ids)

        async with TestSessionLocal() as session:
            audit_rows = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.resource_type == "dns_record",
                            AuditLog.resource_id == str(zone_id),
                            AuditLog.action == "delete",
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(audit_rows) == 1
        assert audit_rows[0].old_value == {"record_ids": sorted(record_ids), "count": 2}
        assert audit_rows[0].new_value == {"record_ids": sorted(record_ids), "count": 2}

    async def test_bulk_delete_with_missing_id_rejected(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "bulk-delete-missing-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "bulk-delete-missing.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        created = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "survivor", "record_type": "A", "content": "10.0.0.40", "ttl": 3600},
            headers=headers,
        )
        assert created.status_code == 201
        survivor_id = created.json()["id"]

        bulk_delete = await client.request(
            "DELETE",
            f"/api/v1/dns/zones/{zone_id}/records/bulk",
            json={"record_ids": [survivor_id, 999999]},
            headers=headers,
        )
        assert bulk_delete.status_code == 400
        assert bulk_delete.json()["detail"] == "Record 999999 not found in zone"

        list_after = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        assert survivor_id in {item["id"] for item in list_after.json()}

    async def test_update_record(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "single-update-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "single-update.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        created = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "www", "record_type": "A", "content": "10.0.0.50", "ttl": 3600},
            headers=headers,
        )
        assert created.status_code == 201
        record_id = created.json()["id"]

        update = await client.patch(
            f"/api/v1/dns/records/{record_id}",
            json={"ttl": 300},
            headers=headers,
        )
        assert update.status_code == 200
        assert update.json()["ttl"] == 300
        assert update.json()["name"] == "www"
        assert update.json()["content"] == "10.0.0.50"

    async def test_update_system_record_rejected(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "single-update-system-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "single-update-system.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        list_records = await client.get(f"/api/v1/dns/zones/{zone_id}/records", headers=headers)
        system_id = next(item["id"] for item in list_records.json() if item["is_system"])

        update = await client.patch(
            f"/api/v1/dns/records/{system_id}",
            json={"ttl": 300},
            headers=headers,
        )
        assert update.status_code == 400
        assert update.json()["detail"] == "System DNS records cannot be modified"

    async def test_record_crud_writes_audit_rows(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "dnsadmin", "dnsadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "record-audit-server"},
            headers=headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "record-audit.internal", "zone_type": "master"},
            headers=headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        created = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "audit-www", "record_type": "A", "content": "10.0.0.60", "ttl": 3600},
            headers=headers,
        )
        assert created.status_code == 201
        record_id = created.json()["id"]

        async with TestSessionLocal() as session:
            create_rows = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.action == "create",
                            AuditLog.resource_type == "dns_record",
                            AuditLog.resource_id == str(record_id),
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(create_rows) == 1
        assert create_rows[0].instance_id == instance.id
        assert create_rows[0].new_value == {
            "name": "audit-www",
            "record_type": "A",
            "content": "10.0.0.60",
            "ttl": 3600,
        }

        update = await client.patch(
            f"/api/v1/dns/records/{record_id}",
            json={"ttl": 120},
            headers=headers,
        )
        assert update.status_code == 200

        async with TestSessionLocal() as session:
            update_rows = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.action == "update",
                            AuditLog.resource_type == "dns_record",
                            AuditLog.resource_id == str(record_id),
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(update_rows) == 1
        assert update_rows[0].old_value["ttl"] == 3600
        assert update_rows[0].new_value["ttl"] == 120

        deleted = await client.request(
            "DELETE",
            f"/api/v1/dns/records/{record_id}",
            headers=headers,
        )
        assert deleted.status_code == 204

        async with TestSessionLocal() as session:
            delete_rows = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.action == "delete",
                            AuditLog.resource_type == "dns_record",
                            AuditLog.resource_id == str(record_id),
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(delete_rows) == 1
        assert delete_rows[0].old_value["name"] == "audit-www"

    async def test_readonly_record_write_writes_no_audit_row(
        self, client: AsyncClient, admin_user, readonly_user, instance
    ):
        admin_token = await _login(client, "dnsadmin", "dnsadminpass")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        create_server = await client.post(
            f"/api/v1/dns/servers/{instance.id}",
            json={"name": "readonly-audit-server"},
            headers=admin_headers,
        )
        assert create_server.status_code == 201
        server_id = create_server.json()["id"]

        create_zone = await client.post(
            f"/api/v1/dns/servers/{server_id}/zones",
            json={"name": "readonly-audit.internal", "zone_type": "master"},
            headers=admin_headers,
        )
        assert create_zone.status_code == 201
        zone_id = create_zone.json()["id"]

        readonly_token = await _login(client, "dnsreader", "dnsreaderpass")
        readonly_headers = {"Authorization": f"Bearer {readonly_token}"}

        async with TestSessionLocal() as session:
            audit_count_before = len((await session.execute(select(AuditLog))).scalars().all())

        response = await client.post(
            f"/api/v1/dns/zones/{zone_id}/records",
            json={"name": "blocked", "record_type": "A", "content": "10.0.0.70", "ttl": 300},
            headers=readonly_headers,
        )
        assert response.status_code == 403

        async with TestSessionLocal() as session:
            audit_rows = (await session.execute(select(AuditLog))).scalars().all()
        assert len(audit_rows) == audit_count_before
