"""Tests for mail domain endpoints and DKIM key management."""

import base64
import uuid
from datetime import datetime

import dns.resolver
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.mail as mail_router
import utils.dns_check as dns_check_module
from main import app
from shared.database import get_db
from shared.models import AuditLog, Base, Instance, MailAlias, MailDomain, MailMessage, MailUser, User
from shared.security import get_password_hash

# Generated per test run so no static credential-shaped literal lands in the repo.
TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


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
    create_maildir) that would dial out to agent endpoints. Neutralize them,
    mirroring the DNS dispatch noop in conftest."""

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(mail_router, "reload_mail_config", _noop)
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
            api_key=TEST_INSTANCE_KEY,
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


class TestMailDomainMtaForwarding:
    async def test_create_domain_with_mta_forwarding(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{instance.id}",
            json={
                "domain": "fwd-create.test",
                "mta_forward_enabled": True,
                "mta_forward_host": "smtp.relay.example.net",
                "mta_forward_port": 2525,
            },
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["mta_forward_enabled"] is True
        assert body["mta_forward_host"] == "smtp.relay.example.net"
        assert body["mta_forward_port"] == 2525
        domain_id = body["id"]

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == domain_id))).scalar_one()
            assert row.mta_forward_enabled is True
            assert row.mta_forward_host == "smtp.relay.example.net"
            assert row.mta_forward_port == 2525

    async def test_create_domain_mta_enabled_without_host(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{instance.id}",
            json={"domain": "fwd-nohost.test", "mta_forward_enabled": True},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_create_domain_mta_host_with_forwarding_disabled(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{instance.id}",
            json={
                "domain": "fwd-disabled.test",
                "mta_forward_enabled": False,
                "mta_forward_host": "mx.example.net",
            },
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["mta_forward_enabled"] is False
        assert body["mta_forward_host"] == "mx.example.net"

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == body["id"]))).scalar_one()
            assert row.mta_forward_enabled is False
            assert row.mta_forward_host == "mx.example.net"

    async def test_update_domain_enable_mta_with_host(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/domains/{mail_domain.id}",
            json={"mta_forward_enabled": True, "mta_forward_host": "smtp.example.net"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["mta_forward_enabled"] is True
        assert body["mta_forward_host"] == "smtp.example.net"

    async def test_update_domain_disable_mta_retains_host(self, client: AsyncClient, admin_user, instance):
        async with TestSessionLocal() as session:
            domain = MailDomain(
                instance_id=instance.id,
                domain="fwd-existing.test",
                enabled=True,
                mta_forward_enabled=True,
                mta_forward_host="smtp.example.net",
                mta_forward_port=587,
            )
            session.add(domain)
            await session.commit()
            await session.refresh(domain)
            domain_id = domain.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/domains/{domain_id}",
            json={"mta_forward_enabled": False},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["mta_forward_enabled"] is False
        assert body["mta_forward_host"] == "smtp.example.net"
        assert body["mta_forward_port"] == 587

    async def test_update_domain_enable_mta_without_stored_host(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/domains/{mail_domain.id}",
            json={"mta_forward_enabled": True},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_update_domain_clear_host_while_enabled(self, client: AsyncClient, admin_user, instance):
        async with TestSessionLocal() as session:
            domain = MailDomain(
                instance_id=instance.id,
                domain="fwd-clear.test",
                enabled=True,
                mta_forward_enabled=True,
                mta_forward_host="smtp.example.net",
            )
            session.add(domain)
            await session.commit()
            await session.refresh(domain)
            domain_id = domain.id

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/domains/{domain_id}",
            json={"mta_forward_host": ""},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_update_domain_invalid_port(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        for bad_port in (0, 65536):
            response = await client.patch(
                f"/api/v1/mail/domains/{mail_domain.id}",
                json={"mta_forward_port": bad_port},
                headers=headers,
            )
            assert response.status_code == 422, f"port {bad_port} should be rejected"

    async def test_update_domain_invalid_host(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        for bad_host in ["https://example.com", "has space", "foo/bar"]:
            response = await client.patch(
                f"/api/v1/mail/domains/{mail_domain.id}",
                json={"mta_forward_host": bad_host},
                headers=headers,
            )
            assert response.status_code == 422, f"host {bad_host!r} should be rejected"

    async def test_update_domain_host_only_keeps_default_port(self, client: AsyncClient, admin_user, mail_domain):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.patch(
            f"/api/v1/mail/domains/{mail_domain.id}",
            json={"mta_forward_host": "mx.example.net"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["mta_forward_host"] == "mx.example.net"
        assert body["mta_forward_port"] == 25

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))).scalar_one()
            assert row.mta_forward_host == "mx.example.net"
            assert row.mta_forward_port == 25


class TestDkimKeygen:
    async def test_generate_dkim_keypair_shape(self):
        from utils.dkim import generate_dkim_keypair

        selector, public_key_b64, private_key_pem = generate_dkim_keypair()

        assert selector == "viswall"
        assert "\n" not in public_key_b64
        assert " " not in public_key_b64

        public_key = serialization.load_der_public_key(base64.b64decode(public_key_b64))
        assert public_key.key_size == 2048

        private_key = serialization.load_pem_private_key(private_key_pem.encode("ascii"), password=None)
        assert private_key.key_size == 2048
        assert private_key_pem.startswith("-----BEGIN PRIVATE KEY-----")

        derived_pub_b64 = base64.b64encode(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode("ascii")
        assert derived_pub_b64 == public_key_b64


class TestDkimRegenerate:
    @staticmethod
    async def _enable_dkim(domain_id: int, enabled: bool = True) -> None:
        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == domain_id))).scalar_one()
            row.dkim_enabled = enabled
            await session.commit()

    async def test_regenerate_dkim_success(
        self, client: AsyncClient, admin_user, instance, mail_domain, monkeypatch
    ):
        await self._enable_dkim(mail_domain.id)

        calls = {}

        async def _fake_agent_request(**kwargs):
            calls["kwargs"] = kwargs
            return {"status": "ok"}

        monkeypatch.setattr(mail_router, "agent_request", _fake_agent_request)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{mail_domain.id}/dkim/regenerate", headers=headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["installed"] is True
        assert body["dns_name"] == f"viswall._domainkey.{mail_domain.domain}"
        assert body["dns_value"].startswith("v=DKIM1; k=rsa; p=")
        assert "private_key" not in response.text

        kwargs = calls["kwargs"]
        assert kwargs["path"] == "/dkim/install"
        assert kwargs["service"] == "mail"
        assert kwargs["json_data"]["domain"] == mail_domain.domain
        assert kwargs["json_data"]["selector"] == "viswall"
        assert "private_key_pem" in kwargs["json_data"]

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))).scalar_one()
            assert row.dkim_selector == "viswall"
            assert row.dkim_public_key
            assert row.dkim_private_key
            assert f"p={row.dkim_public_key}" in body["dns_value"]
            assert kwargs["json_data"]["private_key_pem"] == row.dkim_private_key

        async with TestSessionLocal() as session:
            dispatches = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "mail_agent",
                        AuditLog.resource_id == str(instance.id),
                    )
                )
            ).scalars().all()
            assert any(
                log.new_value
                and log.new_value.get("path") == "/dkim/install"
                and log.new_value.get("status") == "success"
                for log in dispatches
            )
            updates = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.action == "update",
                        AuditLog.resource_type == "mail_domain",
                        AuditLog.resource_id == str(mail_domain.id),
                    )
                )
            ).scalars().all()
            assert len(updates) == 1

    async def test_regenerate_dkim_agent_unreachable(
        self, client: AsyncClient, admin_user, instance, mail_domain, monkeypatch
    ):
        await self._enable_dkim(mail_domain.id)

        async def _boom(**kwargs):
            raise mail_router.AgentClientError("agent unreachable")

        monkeypatch.setattr(mail_router, "agent_request", _boom)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{mail_domain.id}/dkim/regenerate", headers=headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["installed"] is False
        assert body["dns_name"] == f"viswall._domainkey.{mail_domain.domain}"
        assert "private_key" not in response.text

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == mail_domain.id))).scalar_one()
            assert row.dkim_public_key
            assert row.dkim_private_key

            dispatches = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "mail_agent",
                        AuditLog.resource_id == str(instance.id),
                    )
                )
            ).scalars().all()
            assert any(
                log.new_value
                and log.new_value.get("path") == "/dkim/install"
                and log.new_value.get("status") == "failed"
                for log in dispatches
            )
            updates = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.action == "update",
                        AuditLog.resource_type == "mail_domain",
                        AuditLog.resource_id == str(mail_domain.id),
                    )
                )
            ).scalars().all()
            assert len(updates) == 1

    async def test_regenerate_dkim_disabled_rejected(self, client: AsyncClient, admin_user, mail_domain):
        await self._enable_dkim(mail_domain.id, enabled=False)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{mail_domain.id}/dkim/regenerate", headers=headers
        )
        assert response.status_code == 400

    async def test_regenerate_dkim_unknown_domain(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/v1/mail/domains/999999/dkim/regenerate", headers=headers)
        assert response.status_code == 404


class TestDkimOnCreate:
    async def test_create_domain_with_dkim_persists_key(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{instance.id}",
            json={"domain": "dkim-create.test", "dkim_enabled": True},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert "private_key" not in response.text

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == body["id"]))).scalar_one()
            assert row.dkim_selector == "viswall"
            assert row.dkim_public_key
            assert row.dkim_private_key
            assert base64.b64decode(row.dkim_public_key)

    async def test_create_domain_dkim_disabled_no_key(self, client: AsyncClient, admin_user, instance):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/mail/domains/{instance.id}",
            json={"domain": "dkim-off.test", "dkim_enabled": False},
            headers=headers,
        )
        assert response.status_code == 201

        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.domain == "dkim-off.test"))).scalar_one()
            assert row.dkim_public_key is None
            assert row.dkim_private_key is None


class TestDnsRecords:
    @staticmethod
    async def _set_domain_flags(domain_id: int, **flags) -> None:
        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == domain_id))).scalar_one()
            for field, value in flags.items():
                setattr(row, field, value)
            await session.commit()

    @staticmethod
    async def _add_domain(instance_id: int, name: str) -> int:
        async with TestSessionLocal() as session:
            domain = MailDomain(instance_id=instance_id, domain=name, enabled=True)
            session.add(domain)
            await session.commit()
            await session.refresh(domain)
            return domain.id

    async def test_dns_records_unknown_domain_404(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/mail/domains/999999/dns-records", headers=headers)
        assert response.status_code == 404

    async def test_dns_records_all_toggles_off_mx_only(self, client: AsyncClient, admin_user, mail_domain):
        await self._set_domain_flags(
            mail_domain.id,
            spf_enabled=False,
            dkim_enabled=False,
            dmarc_enabled=False,
        )

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["domain"] == mail_domain.domain
        assert len(body["records"]) == 1
        mx = body["records"][0]
        assert mx["key"] == "mx"
        assert mx["type"] == "MX"
        assert mx["name"] == mail_domain.domain
        assert mx["value"] == f"10 mail.{mail_domain.domain}."
        assert f"mail.{mail_domain.domain}" in mx["note"]

    async def test_dns_records_dkim_with_public_key(self, client: AsyncClient, admin_user, mail_domain):
        await self._set_domain_flags(
            mail_domain.id,
            dkim_selector="sel2026",
            dkim_public_key="PubKeyABC123",
        )

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        dkim = next(r for r in response.json()["records"] if r["key"] == "dkim")
        assert dkim["type"] == "TXT"
        assert dkim["name"] == f"sel2026._domainkey.{mail_domain.domain}"
        assert dkim["value"].startswith("v=DKIM1; k=rsa; p=")
        assert "PubKeyABC123" in dkim["value"]
        assert dkim["note"] is None

    async def test_dns_records_dkim_missing_key_not_generated(self, client: AsyncClient, admin_user, mail_domain):
        await self._set_domain_flags(mail_domain.id, dkim_public_key=None, dkim_private_key=None)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        dkim = next(r for r in response.json()["records"] if r["key"] == "dkim")
        assert dkim["name"] == f"viswall._domainkey.{mail_domain.domain}"
        assert dkim["value"] is None
        assert dkim["note"] == "not_generated"

    async def test_dns_records_readable_by_non_admin(self, client: AsyncClient, readonly_user, mail_domain):
        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        keys = [r["key"] for r in response.json()["records"]]
        assert keys == ["mx", "spf", "dkim", "dmarc"]

        spf = response.json()["records"][1]
        assert spf["value"] == f"v=spf1 mx a:mail.{mail_domain.domain} ~all"
        dmarc = response.json()["records"][3]
        assert dmarc["value"] == f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{mail_domain.domain}"
        # Values must be bare record data, not wrapped in literal quotes.
        assert not spf["value"].startswith('"')
        assert not dmarc["value"].endswith('"')

    async def test_dns_records_expose_no_private_material(self, client: AsyncClient, admin_user, mail_domain):
        await self._set_domain_flags(
            mail_domain.id,
            dkim_public_key="PubKeyVisible",
            dkim_private_key="-----BEGIN PRIVATE KEY-----SECRETBODY-----END PRIVATE KEY-----",
        )

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        assert "private" not in response.text.lower()
        assert "SECRETBODY" not in response.text
        assert "PubKeyVisible" in response.text

    async def test_dns_records_multi_domain_signing_no_caveat(self, client: AsyncClient, admin_user, instance, mail_domain):
        # Multi-domain DKIM signing is supported by the mail agent, so several
        # signing domains on one instance must not add any caveat note.
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeySecond")
        await self._add_domain(instance.id, "second-signed.test")

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/domains/{mail_domain.id}/dns-records", headers=headers)
        assert response.status_code == 200
        dkim = next(r for r in response.json()["records"] if r["key"] == "dkim")
        assert dkim["value"] is not None
        assert dkim["note"] is None


class _FakeMX:
    def __init__(self, preference: int, exchange: str):
        self.preference = preference
        self.exchange = exchange


class _FakeTXT:
    def __init__(self, *chunks: str):
        self.strings = tuple(chunk.encode("ascii") for chunk in chunks)


class _FakeA:
    def __init__(self, address: str = "192.0.2.10"):
        self.address = address


class TestDnsCheck:
    @staticmethod
    async def _set_domain_flags(domain_id: int, **flags) -> None:
        async with TestSessionLocal() as session:
            row = (await session.execute(select(MailDomain).where(MailDomain.id == domain_id))).scalar_one()
            for field, value in flags.items():
                setattr(row, field, value)
            await session.commit()

    @staticmethod
    def _routes_all_correct(
        domain_name: str, public_key: str = "PubKeyABC123", selector: str = "viswall"
    ) -> dict:
        return {
            (domain_name, "MX"): [_FakeMX(10, f"mail.{domain_name}.")],
            (domain_name, "TXT"): [_FakeTXT(f"v=spf1 mx a:mail.{domain_name} ~all")],
            (f"{selector}._domainkey.{domain_name}", "TXT"): [
                _FakeTXT("v=DKIM1; ", "k=rsa; ", f"p={public_key}")
            ],
            (f"_dmarc.{domain_name}", "TXT"): [
                _FakeTXT(f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain_name}")
            ],
            (f"mail.{domain_name}", "A"): [_FakeA()],
        }

    @staticmethod
    def _fake_resolve(monkeypatch, routes: dict) -> None:
        async def _resolve(qname: str, rdtype: str):
            key = (qname.lower(), rdtype)
            if key not in routes:
                raise dns.resolver.NXDOMAIN()
            outcome = routes[key]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        monkeypatch.setattr(dns_check_module, "_resolve", _resolve)

    @staticmethod
    def _by_key(body: dict) -> dict:
        return {row["key"]: row for row in body["results"]}

    async def test_dns_check_all_correct(self, client: AsyncClient, admin_user, mail_domain, monkeypatch):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        self._fake_resolve(monkeypatch, self._routes_all_correct(mail_domain.domain))

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert [row["key"] for row in body["results"]] == ["mx", "spf", "dkim", "dmarc"]
        rows = self._by_key(body)
        for key, row in rows.items():
            assert row["status"] == "correct", f"{key}: {row}"
            assert row["found_values"], f"{key} should carry the found value"

        assert rows["mx"]["expected_value"] == f"10 mail.{mail_domain.domain}."
        assert "found priority 10" in rows["mx"]["detail"]
        assert "mail host resolves" in rows["mx"]["detail"]
        assert rows["mx"]["found_values"] == [f"10 mail.{mail_domain.domain}."]

        assert rows["spf"]["expected_value"] == f"v=spf1 mx a:mail.{mail_domain.domain} ~all"
        assert rows["dkim"]["name"] == f"viswall._domainkey.{mail_domain.domain}"
        assert rows["dkim"]["expected_value"] == f"v=DKIM1; k=rsa; p=PubKeyABC123"
        assert rows["dmarc"]["expected_value"] == (
            f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{mail_domain.domain}"
        )

    async def test_dns_check_spf_present_but_different(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        routes = self._routes_all_correct(mail_domain.domain)
        routes[(mail_domain.domain, "TXT")] = [_FakeTXT("v=spf1 -all")]
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        rows = self._by_key(response.json())
        assert rows["spf"]["status"] == "incorrect"
        assert rows["spf"]["found_values"] == ["v=spf1 -all"]
        assert rows["mx"]["status"] == "correct"
        assert rows["dkim"]["status"] == "correct"
        assert rows["dmarc"]["status"] == "correct"

    async def test_dns_check_spf_txt_without_spf_is_missing(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        routes = self._routes_all_correct(mail_domain.domain)
        routes[(mail_domain.domain, "TXT")] = [_FakeTXT("google-site-verification=abc123")]
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        rows = self._by_key(response.json())
        assert rows["spf"]["status"] == "missing"
        assert rows["spf"]["found_values"] == []

    async def test_dns_check_dkim_nxdomain_missing(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        routes = self._routes_all_correct(mail_domain.domain)
        routes[(f"viswall._domainkey.{mail_domain.domain}", "TXT")] = dns.resolver.NXDOMAIN()
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        rows = self._by_key(response.json())
        assert rows["dkim"]["status"] == "missing"
        assert rows["dkim"]["found_values"] == []
        # One absent record does not take down the rest of the response.
        assert rows["mx"]["status"] == "correct"
        assert rows["spf"]["status"] == "correct"

    async def test_dns_check_dkim_wrong_key_incorrect(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        routes = self._routes_all_correct(mail_domain.domain)
        routes[(f"viswall._domainkey.{mail_domain.domain}", "TXT")] = [
            _FakeTXT("v=DKIM1; k=rsa; p=OtherKey999")
        ]
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        rows = self._by_key(response.json())
        assert rows["dkim"]["status"] == "incorrect"
        assert rows["dkim"]["found_values"] == ["v=DKIM1; k=rsa; p=OtherKey999"]

    async def test_dns_check_timeout_yields_error_and_response(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        routes = self._routes_all_correct(mail_domain.domain)
        routes[(mail_domain.domain, "TXT")] = dns.resolver.LifetimeTimeout()
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        rows = self._by_key(response.json())
        assert rows["spf"]["status"] == "error"
        assert rows["spf"]["detail"]
        assert "timed out" in rows["spf"]["detail"]
        # The gather still returns: one erroring row does not kill the response.
        assert rows["mx"]["status"] == "correct"
        assert rows["dkim"]["status"] == "correct"
        assert rows["dmarc"]["status"] == "correct"

    async def test_dns_check_checked_at_timezone_aware(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        self._fake_resolve(monkeypatch, self._routes_all_correct(mail_domain.domain))

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        checked_at = datetime.fromisoformat(response.json()["checked_at"])
        assert checked_at.tzinfo is not None

    async def test_dns_check_non_admin_gets_200(
        self, client: AsyncClient, readonly_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(mail_domain.id, dkim_public_key="PubKeyABC123")
        self._fake_resolve(monkeypatch, self._routes_all_correct(mail_domain.domain))

        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["results"]) == 4

    async def test_dns_check_toggles_off_mx_only(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(
            mail_domain.id,
            spf_enabled=False,
            dkim_enabled=False,
            dmarc_enabled=False,
        )
        routes = {
            (mail_domain.domain, "MX"): [_FakeMX(25, f"mail.{mail_domain.domain}.")],
        }
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert [row["key"] for row in body["results"]] == ["mx"]
        mx = body["results"][0]
        # Priority is informational only: 25 vs the advised 10 still matches.
        assert mx["status"] == "correct"
        # mail host has no A/AAAA: informational note, MX status unaffected.
        assert "mail host does not resolve" in mx["detail"]

    async def test_dns_check_unknown_domain_404(self, client: AsyncClient, admin_user):
        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/v1/mail/domains/999999/dns-check", headers=headers)
        assert response.status_code == 404

    async def test_dns_check_exposes_no_private_material(
        self, client: AsyncClient, admin_user, mail_domain, monkeypatch
    ):
        await self._set_domain_flags(
            mail_domain.id,
            dkim_public_key="PubKeyVisible",
            dkim_private_key="-----BEGIN PRIVATE KEY-----SECRETBODY-----END PRIVATE KEY-----",
        )
        routes = self._routes_all_correct(mail_domain.domain, public_key="PubKeyVisible")
        routes[(f"viswall._domainkey.{mail_domain.domain}", "TXT")] = [
            _FakeTXT("v=DKIM1; k=rsa; p=PubKeyVisible")
        ]
        self._fake_resolve(monkeypatch, routes)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(f"/api/v1/mail/domains/{mail_domain.id}/dns-check", headers=headers)
        assert response.status_code == 200
        assert "private" not in response.text.lower()
        assert "SECRETBODY" not in response.text
        assert "PubKeyVisible" in response.text


class TestMailLogs:
    """GET /mail/logs/{instance_id} — proxied exim mainlog pages.

    The agent response also carries a diagnostic source_files field that
    MailLogsPage intentionally omits (pydantic strips extras); the API
    surface stays lines/total_matched/next_offset only.
    """

    PAGE = {
        "lines": [
            "2026-01-01 00:00:01 1aBcDe-0001 <= sender@remote.example",
            "2026-01-01 00:00:02 1aBcDe-0002 rejected SPAM",
        ],
        "total_matched": 2,
        "next_offset": None,
        "source_files": ["/var/log/exim4/mainlog"],
    }

    @staticmethod
    def _fake_agent(page: dict):
        calls = []

        async def _fake(**kwargs):
            calls.append(kwargs)
            return dict(page)

        return calls, _fake

    @staticmethod
    async def _grant_instance_access(user_id: int, instance_id: int) -> None:
        async with TestSessionLocal() as session:
            row = (await session.execute(select(User).where(User.id == user_id))).scalar_one()
            row.instances = [instance_id]
            await session.commit()

    async def test_logs_happy_path(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {
            "lines": self.PAGE["lines"],
            "total_matched": 2,
            "next_offset": None,
        }

        assert len(calls) == 1
        kwargs = calls[0]
        assert kwargs["path"] == "/logs"
        assert kwargs["service"] == "mail"
        assert kwargs["method"] == "GET"
        assert kwargs["instance_id"] == instance.id
        assert kwargs["timeout"] == 15.0
        assert kwargs["params"] == {"offset": 0, "limit": 200}

    async def test_logs_forwards_all_filters(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/mail/logs/{instance.id}",
            params={
                "offset": 400,
                "limit": 100,
                "q": "rejected",
                "domain": "example.test",
                "mail_id": "1aBcDe",
                "since": "2026-01-01 00:00",
                "until": "2026-01-02 23:59",
            },
            headers=headers,
        )
        assert response.status_code == 200
        assert calls[0]["params"] == {
            "offset": 400,
            "limit": 100,
            "q": "rejected",
            "domain": "example.test",
            "mail_id": "1aBcDe",
            "since": "2026-01-01 00:00",
            "until": "2026-01-02 23:59",
        }

    async def test_logs_omits_unset_filters(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/mail/logs/{instance.id}",
            params={"q": "spam", "since": "2026-01-01 00:00"},
            headers=headers,
        )
        assert response.status_code == 200
        assert calls[0]["params"] == {
            "offset": 0,
            "limit": 200,
            "q": "spam",
            "since": "2026-01-01 00:00",
        }

    async def test_logs_readonly_user_with_instance_access(self, client: AsyncClient, readonly_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(readonly_user.id, instance.id)

        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["total_matched"] == 2
        assert len(calls) == 1

    async def test_logs_denied_without_instance_access(self, client: AsyncClient, readonly_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)

        token = await _login(client, "mailreader", "mailreaderpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied to this instance"
        assert calls == []

    async def test_logs_requires_auth(self, client: AsyncClient, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)

        response = await client.get(f"/api/v1/mail/logs/{instance.id}")
        # No Authorization header: FastAPI's http_bearer auto_error replies
        # 403 "Not authenticated"; 401 is only for present-but-invalid tokens.
        assert response.status_code == 403
        assert calls == []

    async def test_logs_agent_unreachable_502(self, client: AsyncClient, admin_user, instance, monkeypatch):
        async def _boom(**kwargs):
            raise mail_router.AgentClientError("cannot connect to agent")

        monkeypatch.setattr(mail_router, "agent_request", _boom)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", headers=headers)
        assert response.status_code == 502
        assert response.json()["detail"] == "mail agent unreachable or logs endpoint unavailable"

    async def test_logs_limit_clamped_to_500(self, client: AsyncClient, admin_user, instance, monkeypatch):
        page = dict(self.PAGE, next_offset=500)
        calls, fake = self._fake_agent(page)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", params={"limit": 1000}, headers=headers)
        assert response.status_code == 200
        assert response.json()["next_offset"] == 500
        assert calls[0]["params"]["limit"] == 500

    async def test_logs_limit_zero_clamped_to_1(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", params={"limit": 0}, headers=headers)
        assert response.status_code == 200
        assert calls[0]["params"]["limit"] == 1

    async def test_logs_negative_offset_rejected(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/mail/logs/{instance.id}", params={"offset": -1}, headers=headers)
        assert response.status_code == 422
        assert calls == []

    async def test_logs_large_offset_forwarded(self, client: AsyncClient, admin_user, instance, monkeypatch):
        calls, fake = self._fake_agent(self.PAGE)
        monkeypatch.setattr(mail_router, "agent_request", fake)
        await self._grant_instance_access(admin_user.id, instance.id)

        token = await _login(client, "mailadmin", "mailadminpass")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/mail/logs/{instance.id}", params={"offset": 999999999}, headers=headers
        )
        assert response.status_code == 200
        assert calls[0]["params"]["offset"] == 999999999
