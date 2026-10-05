"""Tests for mail domain deletion endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.mail as mail_router
from main import app
from shared.database import get_db
from shared.models import AuditLog, Base, Instance, MailAlias, MailDomain, MailMessage, MailUser, User
from shared.security import get_password_hash


pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite does not enforce foreign keys by default; enable per-connection so
    the ON DELETE CASCADE defined on the models actually fires during tests."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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


@pytest_asyncio.fixture(autouse=True)
async def no_mail_background_tasks(monkeypatch):
    """Mail mutations schedule background tasks (reload_mail_config,
    generate_dkim_keys) that would dial out to agent endpoints. Neutralize them,
    mirroring the DNS dispatch noop in conftest."""

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(mail_router, "reload_mail_config", _noop)
    monkeypatch.setattr(mail_router, "generate_dkim_keys", _noop)
    monkeypatch.setattr(mail_router, "create_maildir", _noop)


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            username="mailadmin",
            email="mailadmin@example.com",
            password_hash=get_password_hash("mailadminpass"),
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
            username="mailreader",
            email="mailreader@example.com",
            password_hash=get_password_hash("mailreaderpass"),
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
            name="mail-instance-1",
            hostname="mail1.example.local",
            api_endpoint="https://mail1.example.local",
            api_key="mail-key-1",
            status="active",
            capabilities=["mail"],
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


@pytest_asyncio.fixture
async def mail_domain(instance):
    async with TestSessionLocal() as session:
        domain = MailDomain(
            instance_id=instance.id,
            domain="example.test",
            enabled=True,
        )
        session.add(domain)
        await session.commit()
        await session.refresh(domain)
        yield domain


async def _login(client: AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestMailDomainDeletion:
    async def test_delete_domain_without_children(self, client: AsyncClient, admin_user, instance, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/v1/mail/domains/{mail_domain.id}", headers=headers)
        assert response.status_code == 204

        # Row gone
        async with TestSessionLocal() as session:
            result = await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))
            assert result.scalar_one_or_none() is None

        # Audit log row exists with correct user_id
        async with TestSessionLocal() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.action == "delete",
                    AuditLog.resource_type == "mail_domain",
                    AuditLog.resource_id == str(mail_domain.id),
                )
            )
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].user_id == admin_user.id
            assert logs[0].instance_id == instance.id

    async def test_delete_domain_cascades_to_children(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        async with TestSessionLocal() as session:
            mail_user = MailUser(domain_id=mail_domain.id, username="alice")
            session.add(mail_user)
            message = MailMessage(
                domain_id=mail_domain.id,
                message_id="cascade-test-message-1",
                sender="alice@example.test",
                status="pending",
            )
            session.add(message)
            alias = MailAlias(domain_id=mail_domain.id, source="*", destination="alice@example.test")
            session.add(alias)
            await session.commit()
            await session.refresh(mail_user)
            await session.refresh(message)
            await session.refresh(alias)
            user_id = mail_user.id
            message_row_id = message.id
            alias_id = alias.id

        response = await client.delete(f"/api/v1/mail/domains/{mail_domain.id}", headers=headers)
        assert response.status_code == 204

        # Domain and all three children gone (cascade verified end-to-end)
        async with TestSessionLocal() as session:
            assert (await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))).scalar_one_or_none() is None
            assert (await session.execute(select(MailUser).where(MailUser.id == user_id))).scalar_one_or_none() is None
            assert (await session.execute(select(MailMessage).where(MailMessage.id == message_row_id))).scalar_one_or_none() is None
            assert (await session.execute(select(MailAlias).where(MailAlias.id == alias_id))).scalar_one_or_none() is None

    async def test_delete_domain_not_found(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/mail/domains/999999", headers=headers)
        assert response.status_code == 404

    async def test_delete_domain_requires_admin(self, client: AsyncClient, readonly_user, mail_domain):
        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/v1/mail/domains/{mail_domain.id}", headers=headers)
        assert response.status_code == 403

        # Domain must still exist
        async with TestSessionLocal() as session:
            result = await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))
            assert result.scalar_one_or_none() is not None


class TestMailAliasEndpoints:
    async def test_list_aliases(self, client: AsyncClient, admin_user, mail_domain):
        async with TestSessionLocal() as session:
            admin_row = (await session.execute(select(User).where(User.id == admin_user.id))).scalar_one()
            admin_row.instances = [mail_domain.instance_id]
            session.add(MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test"))
            session.add(MailAlias(domain_id=mail_domain.id, source="sales", destination="bob@example.test", enabled=False))
            await session.commit()

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/aliases/{mail_domain.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for alias in data:
            assert set(alias.keys()) == {"id", "domain_id", "source", "destination", "enabled", "created_at", "updated_at"}
            assert alias["domain_id"] == mail_domain.id
        by_source = {alias["source"]: alias for alias in data}
        assert by_source["info"]["destination"] == "alice@example.test"
        assert by_source["info"]["enabled"] is True
        assert by_source["sales"]["destination"] == "bob@example.test"
        assert by_source["sales"]["enabled"] is False

    async def test_list_aliases_readonly_forbidden(self, client: AsyncClient, readonly_user, mail_domain):
        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/aliases/{mail_domain.id}", headers=headers)
        assert response.status_code == 403

    async def test_list_aliases_unknown_domain(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/mail/aliases/999999", headers=headers)
        assert response.status_code == 404

    async def test_create_alias(self, client: AsyncClient, admin_user, instance, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/aliases/{mail_domain.id}",
            json={"source": "info", "destination": "alice@example.test"},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["source"] == "info"
        assert body["destination"] == "alice@example.test"
        assert body["enabled"] is True
        assert body["domain_id"] == mail_domain.id
        alias_id = body["id"]

        # Row in DB
        async with TestSessionLocal() as session:
            result = await session.execute(select(MailAlias).where(MailAlias.id == alias_id))
            assert result.scalar_one_or_none() is not None

        # Audit log row
        async with TestSessionLocal() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.action == "create",
                    AuditLog.resource_type == "mail_alias",
                    AuditLog.resource_id == str(alias_id),
                )
            )
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].user_id == admin_user.id
            assert logs[0].instance_id == instance.id

    async def test_create_alias_duplicate(self, client: AsyncClient, admin_user, mail_domain):
        async with TestSessionLocal() as session:
            session.add(MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test"))
            await session.commit()

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/aliases/{mail_domain.id}",
            json={"source": "info", "destination": "alice@example.test"},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_create_alias_invalid_source(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        for bad_source in ["bad@part", "has space"]:
            response = await client.post(
                f"/api/v1/mail/aliases/{mail_domain.id}",
                json={"source": bad_source, "destination": "alice@example.test"},
                headers=headers,
            )
            assert response.status_code == 422, f"source {bad_source!r} should be rejected"

    async def test_create_alias_invalid_destination(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/aliases/{mail_domain.id}",
            json={"source": "info", "destination": "not-an-email"},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_patch_alias_toggle_enabled(self, client: AsyncClient, admin_user, mail_domain):
        async with TestSessionLocal() as session:
            alias = MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test", enabled=True)
            session.add(alias)
            await session.commit()
            await session.refresh(alias)
            alias_id = alias.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(f"/api/v1/mail/aliases/{alias_id}", json={"enabled": False}, headers=headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is False

        async with TestSessionLocal() as session:
            result = await session.execute(select(MailAlias).where(MailAlias.id == alias_id))
            row = result.scalar_one()
            assert row.enabled is False

    async def test_patch_alias_destination(self, client: AsyncClient, admin_user, mail_domain):
        async with TestSessionLocal() as session:
            alias = MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test")
            session.add(alias)
            await session.commit()
            await session.refresh(alias)
            alias_id = alias.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/aliases/{alias_id}",
            json={"destination": "carol@example.test"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["destination"] == "carol@example.test"

        async with TestSessionLocal() as session:
            result = await session.execute(select(MailAlias).where(MailAlias.id == alias_id))
            row = result.scalar_one()
            assert row.destination == "carol@example.test"

    async def test_patch_alias_duplicate_destination(self, client: AsyncClient, admin_user, mail_domain):
        async with TestSessionLocal() as session:
            session.add(MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test"))
            alias_b = MailAlias(domain_id=mail_domain.id, source="info", destination="bob@example.test")
            session.add(alias_b)
            await session.commit()
            await session.refresh(alias_b)
            alias_b_id = alias_b.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/aliases/{alias_b_id}",
            json={"destination": "alice@example.test"},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_patch_alias_unknown_id(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch("/api/v1/mail/aliases/999999", json={"enabled": False}, headers=headers)
        assert response.status_code == 404

    async def test_delete_alias(self, client: AsyncClient, admin_user, instance, mail_domain):
        async with TestSessionLocal() as session:
            alias = MailAlias(domain_id=mail_domain.id, source="info", destination="alice@example.test")
            session.add(alias)
            await session.commit()
            await session.refresh(alias)
            alias_id = alias.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/v1/mail/aliases/{alias_id}", headers=headers)
        assert response.status_code == 204

        # Row gone
        async with TestSessionLocal() as session:
            result = await session.execute(select(MailAlias).where(MailAlias.id == alias_id))
            assert result.scalar_one_or_none() is None

        # Audit log row
        async with TestSessionLocal() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.action == "delete",
                    AuditLog.resource_type == "mail_alias",
                    AuditLog.resource_id == str(alias_id),
                )
            )
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].user_id == admin_user.id
            assert logs[0].instance_id == instance.id

    async def test_delete_alias_unknown_id(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/mail/aliases/999999", headers=headers)
        assert response.status_code == 404
