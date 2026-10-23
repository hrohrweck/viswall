"""Tests for the real VPN site-to-site wiring (routers/vpn.py, plan todo 24).

Covers the plan todo 25 gateway items:

- vpn payload builder: site-to-site rows -> /vpn/apply body, server-mode
  tunnels skipped, no tunnel -> {} (utils/firewall_dispatch.py);
- site-to-site initialize: full mock chain (row + agent_request POST
  /vpn/apply with the built payload), agent down -> 502 with the DB row
  kept, invalid endpoint/key -> 422, duplicate -> 409;
- start/stop dispatch: Pydantic-style body {"protocol", "name"} to
  service="vpn" (/vpn/start, /vpn/stop), agent down -> 502;
- client credential regeneration: real agent keys, no "placeholder"
  material anywhere in the result.
"""

import base64
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.vpn as vpn_router
import utils.firewall_dispatch as dispatch_mod
from main import app
from shared.database import get_db
from shared.models import Base, Instance, User, VPNClient, VPNServer
from shared.schemas import VPNServerCreate, VPNServerUpdate
from shared.security import get_password_hash
from utils.agent_client import AgentConnectionError

pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex

# 44-char base64 WireGuard-shaped material, generated at import time so no
# credential-looking literal lands in the repo (gitleaks-safe).
VALID_WG_PUB = base64.b64encode(b"p" * 32).decode()
VALID_WG_PRIV = base64.b64encode(b"v" * 32).decode()


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
            name="vpn-dispatch-instance",
            hostname="vpn0.example.local",
            api_endpoint="http://fallback-agent:9000",
            api_key=TEST_INSTANCE_KEY,
            status="active",
            capabilities=["vpn"],
            config={"agent_endpoints": {"vpn": "http://vpn-agent:8083"}},
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            username="vpnadmin",
            email="vpnadmin@example.com",
            password_hash=get_password_hash("vpnadminpass"),
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
            username="vpnreader",
            email="vpnreader@example.com",
            password_hash=get_password_hash("vpnreaderpass"),
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


async def _seed_site_to_site(instance_id: int) -> VPNServer:
    async with TestSessionLocal() as session:
        server = VPNServer(
            instance_id=instance_id,
            name="site-to-site-base0",
            enabled=True,
            protocol="wireguard",
            tunnel_type="site-to-site",
            endpoint="base0.example.com:51820",
            peer_public_key=VALID_WG_PUB,
            allowed_ips="10.80.0.0/16",
            persistent_keepalive=25,
            local_address="10.80.210.2/24",
            status="stopped",
        )
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return server


class TestBuildInstanceVpnPayload:
    async def test_site_to_site_tunnel_builds_vpn_apply_body(self, instance):
        await _seed_site_to_site(instance.id)

        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_vpn_payload(
                session, instance.id
            )

        assert payload == {
            "protocol": "wireguard",
            "name": "site-to-site-base0",
            "address": "10.80.210.2/24",
            "endpoint": "base0.example.com:51820",
            "peer_public_key": VALID_WG_PUB,
            "allowed_ips": "10.80.0.0/16",
            "persistent_keepalive": 25,
        }

    async def test_server_mode_tunnel_is_skipped(self, instance):
        async with TestSessionLocal() as session:
            session.add(
                VPNServer(
                    instance_id=instance.id,
                    name="road-warrior-vpn",
                    enabled=True,
                    protocol="wireguard",
                    tunnel_type="server",
                )
            )
            await session.commit()

        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_vpn_payload(
                session, instance.id
            )

        assert payload == {}

    async def test_no_tunnels_yields_empty_payload(self, instance):
        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_vpn_payload(
                session, instance.id
            )

        assert payload == {}


class TestInitializeSiteToSite:
    async def test_initialize_dispatches_vpn_apply_payload(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["method"] = method
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            captured["json"] = json_data
            return {"applied": True}

        # The initialize route re-reads the committed row through a fresh
        # session; point it at the in-memory test DB.
        monkeypatch.setattr(vpn_router, "AsyncSessionLocal", TestSessionLocal)
        monkeypatch.setattr(dispatch_mod, "agent_request", _fake_agent_request)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert isinstance(body["server_id"], int)
        assert body["agent"] == {"applied": True}

        assert captured["method"] == "POST"
        assert captured["path"] == "/vpn/apply"
        assert captured["service"] == "vpn"
        sent = captured["json"]
        assert sent["protocol"] == "wireguard"
        assert sent["name"] == "site-to-site-base0.example.com-51820"
        assert sent["endpoint"] == "base0.example.com:51820"
        assert sent["peer_public_key"] == VALID_WG_PUB
        assert sent["allowed_ips"] == "10.80.0.0/16"
        assert sent["persistent_keepalive"] == 25
        assert sent["address"] == "10.200.0.2/24"  # default local address
        assert "private_key" not in sent

        async with TestSessionLocal() as session:
            server = (
                await session.execute(
                    select(VPNServer).where(VPNServer.tunnel_type == "site-to-site")
                )
            ).scalars().all()
        assert len(server) == 1
        assert server[0].status == "stopped"
        assert server[0].enabled is True

    async def test_initialize_returns_502_when_agent_down_and_keeps_row(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async def _unreachable(db, instance_id, method, path, json_data=None, **kwargs):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(vpn_router, "AsyncSessionLocal", TestSessionLocal)
        monkeypatch.setattr(dispatch_mod, "agent_request", _unreachable)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502
        assert "VPN agent error" in response.json()["detail"]

        # Desired-state model: the row survives the failed dispatch.
        async with TestSessionLocal() as session:
            servers = (
                await session.execute(
                    select(VPNServer).where(VPNServer.tunnel_type == "site-to-site")
                )
            ).scalars().all()
        assert len(servers) == 1

    async def test_invalid_endpoint_returns_422(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "not a valid endpoint!",
                "remote_public_key": VALID_WG_PUB,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert "remote_endpoint" in response.json()["detail"]

    async def test_invalid_public_key_returns_422(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": "not-a-key",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malicious_allowed_ips_newline_returns_422(
        self, client: AsyncClient, admin_user, instance
    ):
        """F2 BLOCKER #3: a newline smuggles PostUp into the client.conf."""
        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
                "allowed_ips": "10.80.0.0/16\nPostUp = /tmp/pwned",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert "allowed_ips" in response.json()["detail"]

    async def test_malicious_local_address_returns_422(
        self, client: AsyncClient, admin_user, instance
    ):
        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
                "local_address": "10.200.0.2\nPostUp = /tmp/pwned",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert "local_address" in response.json()["detail"]

    async def test_duplicate_initialize_returns_409(
        self, client: AsyncClient, admin_user, instance
    ):
        await _seed_site_to_site(instance.id)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "other.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_initialize_requires_admin(
        self, client: AsyncClient, readonly_user, instance
    ):
        token = await _login(client, "vpnreader", "vpnreaderpass")
        response = await client.post(
            "/api/v1/vpn/site-to-site/initialize",
            params={
                "local_instance_id": instance.id,
                "remote_endpoint": "base0.example.com:51820",
                "remote_public_key": VALID_WG_PUB,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestVPNServerSchemaInjectionGuard:
    """F2 BLOCKER #3: VPNServerCreate/Update must reject config-injection
    values at the schema boundary (newline/CR/`=`, bad CIDRs, bad keys)."""

    @pytest.mark.parametrize(
        "field,value",
        [
            ("allowed_ips", "10.80.0.0/16\nPostUp = /tmp/pwned"),
            ("allowed_ips", "10.80.0.0/16 = evil"),
            ("allowed_ips", "10.80.0.0/16,not-a-cidr"),
            ("local_address", "10.200.0.2/24\nPostUp = /tmp/pwned"),
            ("local_address", "10.200.0.2/33"),
            ("endpoint", "base0.example:51820\nPostUp = /tmp/pwned"),
            ("endpoint", "evil host:51820"),
            ("peer_public_key", "not-a-key"),
            ("peer_public_key", VALID_WG_PUB + "\nPostUp = /tmp/pwned"),
            ("private_key", VALID_WG_PRIV + "\nPostUp = /tmp/pwned"),
        ],
    )
    def test_create_rejects_injection(self, field, value):
        payload = {
            "name": "wg-server",
            "protocol": "wireguard",
            "tunnel_type": "site-to-site",
            field: value,
        }
        with pytest.raises(ValidationError):
            VPNServerCreate(**payload)

    @pytest.mark.parametrize(
        "field,value",
        [
            ("allowed_ips", "10.80.0.0/16\nPostUp = /tmp/pwned"),
            ("local_address", "10.200.0.2/24\nPostUp = /tmp/pwned"),
            ("endpoint", "base0.example:51820\nPostUp = /tmp/pwned"),
            ("peer_public_key", "not-a-key"),
            ("private_key", "short"),
        ],
    )
    def test_update_rejects_injection(self, field, value):
        with pytest.raises(ValidationError):
            VPNServerUpdate(**{field: value})

    def test_create_accepts_valid_tunnel_values(self):
        server = VPNServerCreate(
            name="wg-server",
            protocol="wireguard",
            tunnel_type="site-to-site",
            endpoint="base0.example.com:51820",
            peer_public_key=VALID_WG_PUB,
            allowed_ips="10.80.0.0/16,10.200.0.0/24",
            local_address="10.200.0.2/24",
            private_key=VALID_WG_PRIV,
        )
        assert server.allowed_ips == "10.80.0.0/16,10.200.0.0/24"


class TestClientPrivateKeyExposure:
    """F2 MAJOR #6: the generated config embeds the raw WireGuard private
    key — list/get must never carry it for a non-admin, and the download
    route is admin-only."""

    async def _seed_wireguard_server(self, instance_id: int) -> int:
        async with TestSessionLocal() as session:
            server = VPNServer(
                instance_id=instance_id,
                name="wg-main",
                enabled=True,
                protocol="wireguard",
                tunnel_type="server",
                status="running",
                config={"public_key": VALID_WG_PUB},
            )
            session.add(server)
            await session.commit()
            await session.refresh(server)
            return server.id

    async def _seed_wireguard_client(self, server_id: int) -> int:
        async with TestSessionLocal() as session:
            client_row = VPNClient(
                server_id=server_id,
                name="road-warrior",
                enabled=True,
                public_key=VALID_WG_PUB,
                assigned_ip="10.200.0.10",
                allowed_ips=["10.200.0.0/24"],
            )
            session.add(client_row)
            await session.commit()
            await session.refresh(client_row)
            return client_row.id

    async def test_list_and_get_never_expose_config_to_non_admin(
        self, client: AsyncClient, admin_user, readonly_user, instance, monkeypatch
    ):
        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            return {"public_key": VALID_WG_PUB, "private_key": VALID_WG_PRIV}

        monkeypatch.setattr(vpn_router, "agent_request", _fake_agent_request)
        server_id = await self._seed_wireguard_server(instance.id)

        admin_token = await _login(client, "vpnadmin", "vpnadminpass")
        created = await client.post(
            f"/api/v1/vpn/servers/{server_id}/clients",
            json={"name": "road-warrior", "assigned_ip": "10.200.0.10"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert created.status_code == 200
        assert VALID_WG_PRIV in base64.b64decode(created.json()["config_file"]).decode()

        client_id = created.json()["id"]

        readonly_token = await _login(client, "vpnreader", "vpnreaderpass")
        listed = await client.get(
            f"/api/v1/vpn/servers/{server_id}/clients",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert listed.status_code == 200
        assert all("config_file" not in item for item in listed.json())
        assert VALID_WG_PRIV not in listed.text

        fetched = await client.get(
            f"/api/v1/vpn/clients/{client_id}",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert fetched.status_code == 200
        assert "config_file" not in fetched.json()
        assert VALID_WG_PRIV not in fetched.text

        download = await client.get(
            f"/api/v1/vpn/clients/{client_id}/config",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert download.status_code == 403

    async def test_admin_can_download_config_with_private_key(
        self, client: AsyncClient, admin_user, readonly_user, instance, monkeypatch
    ):
        server_id = await self._seed_wireguard_server(instance.id)
        client_id = await self._seed_wireguard_client(server_id)

        async with TestSessionLocal() as session:
            row = await session.get(VPNClient, client_id)
            config_text = "# VPN Client Configuration\nPrivateKey = real-key-material\n"
            row.config_file = base64.b64encode(config_text.encode()).decode()
            await session.commit()

        admin_token = await _login(client, "vpnadmin", "vpnadminpass")
        download = await client.get(
            f"/api/v1/vpn/clients/{client_id}/config",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert download.status_code == 200
        body = download.json()
        decoded = base64.b64decode(body["config_data"]).decode()
        assert "PrivateKey = real-key-material" in decoded

    async def test_admin_create_response_still_contains_config(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            return {"public_key": VALID_WG_PUB, "private_key": VALID_WG_PRIV}

        monkeypatch.setattr(vpn_router, "agent_request", _fake_agent_request)
        server_id = await self._seed_wireguard_server(instance.id)

        admin_token = await _login(client, "vpnadmin", "vpnadminpass")
        created = await client.post(
            f"/api/v1/vpn/servers/{server_id}/clients",
            json={"name": "road-warrior", "assigned_ip": "10.200.0.10"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert created.status_code == 200
        assert "config_file" in created.json()
        assert VALID_WG_PRIV in base64.b64decode(created.json()["config_file"]).decode()


class TestServerPrivateKeyExposure:
    """F2 REMAINING MAJOR: VPNServerResponse inherited VPNServerBase, which
    carried ``private_key`` (the site-to-site tunnel key). list_servers and
    get_server are require_auth (not require_admin) — any logged-in user could
    read the tunnel private key. The plain server shape must never carry it;
    only the admin variant (VPNServerAdminResponse) on admin-gated routes may."""

    async def _seed_server_with_key(self, instance_id: int) -> int:
        async with TestSessionLocal() as session:
            server = VPNServer(
                instance_id=instance_id,
                name="site-to-site-base0",
                enabled=True,
                protocol="wireguard",
                tunnel_type="site-to-site",
                endpoint="base0.example.com:51820",
                peer_public_key=VALID_WG_PUB,
                local_address="10.80.210.2/24",
                network_cidr="10.200.0.0/24",
                private_key=VALID_WG_PRIV,
                status="stopped",
            )
            session.add(server)
            await session.commit()
            await session.refresh(server)
            return server.id

    async def test_non_admin_list_never_exposes_private_key(
        self, client: AsyncClient, readonly_user, instance
    ):
        await self._seed_server_with_key(instance.id)

        token = await _login(client, "vpnreader", "vpnreaderpass")
        listed = await client.get(
            f"/api/v1/vpn/servers/{instance.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert listed.status_code == 200
        assert all("private_key" not in item for item in listed.json())
        assert VALID_WG_PRIV not in listed.text

    async def test_non_admin_detail_never_exposes_private_key(
        self, client: AsyncClient, readonly_user, instance
    ):
        server_id = await self._seed_server_with_key(instance.id)

        token = await _login(client, "vpnreader", "vpnreaderpass")
        fetched = await client.get(
            f"/api/v1/vpn/servers/detail/{server_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert fetched.status_code == 200
        assert "private_key" not in fetched.json()
        assert VALID_WG_PRIV not in fetched.text

    async def test_admin_update_response_still_returns_private_key(
        self, client: AsyncClient, admin_user, instance
    ):
        server_id = await self._seed_server_with_key(instance.id)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        updated = await client.patch(
            f"/api/v1/vpn/servers/{server_id}",
            json={"private_key": VALID_WG_PRIV},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert updated.status_code == 200
        assert updated.json().get("private_key") == VALID_WG_PRIV


class TestStartStopDispatch:
    async def _seed_server(self, instance_id: int) -> VPNServer:
        async with TestSessionLocal() as session:
            server = VPNServer(
                instance_id=instance_id,
                name="wg-main",
                enabled=True,
                protocol="wireguard",
                tunnel_type="server",
                status="stopped",
            )
            session.add(server)
            await session.commit()
            await session.refresh(server)
            return server

    async def test_start_sends_protocol_name_body(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        server = await self._seed_server(instance.id)
        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            captured["json"] = json_data
            return {"status": "running"}

        monkeypatch.setattr(vpn_router, "agent_request", _fake_agent_request)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            f"/api/v1/vpn/servers/{server.id}/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "action": "start",
            "server_id": server.id,
        }
        assert captured["path"] == "/vpn/start"
        assert captured["service"] == "vpn"
        assert captured["json"] == {"protocol": "wireguard", "name": "wg-main"}

        async with TestSessionLocal() as session:
            refreshed = await session.get(VPNServer, server.id)
        assert refreshed.status == "running"

    async def test_stop_sends_protocol_name_body(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        server = await self._seed_server(instance.id)
        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            captured["json"] = json_data
            return {"status": "stopped"}

        monkeypatch.setattr(vpn_router, "agent_request", _fake_agent_request)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            f"/api/v1/vpn/servers/{server.id}/stop",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "action": "stop",
            "server_id": server.id,
        }
        assert captured["path"] == "/vpn/stop"
        assert captured["service"] == "vpn"
        assert captured["json"] == {"protocol": "wireguard", "name": "wg-main"}

        async with TestSessionLocal() as session:
            refreshed = await session.get(VPNServer, server.id)
        assert refreshed.status == "stopped"

    async def test_start_returns_502_when_agent_down(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        server = await self._seed_server(instance.id)

        async def _unreachable(db, instance_id, method, path, json_data=None, **kwargs):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(vpn_router, "agent_request", _unreachable)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            f"/api/v1/vpn/servers/{server.id}/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502


class TestRegenerateClientCredentials:
    async def test_regenerate_uses_agent_keys_and_no_placeholder(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async with TestSessionLocal() as session:
            server = VPNServer(
                instance_id=instance.id,
                name="wg-main",
                enabled=True,
                protocol="wireguard",
                tunnel_type="server",
                status="running",
            )
            session.add(server)
            await session.flush()
            client_row = VPNClient(
                server_id=server.id,
                name="road-warrior",
                enabled=True,
                public_key="placeholder_old_key",
                assigned_ip="10.200.0.10",
            )
            session.add(client_row)
            await session.commit()
            await session.refresh(client_row)
            client_id = client_row.id

        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            return {"public_key": VALID_WG_PUB, "private_key": VALID_WG_PRIV}

        monkeypatch.setattr(vpn_router, "agent_request", _fake_agent_request)

        token = await _login(client, "vpnadmin", "vpnadminpass")
        response = await client.post(
            f"/api/v1/vpn/clients/{client_id}/regenerate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["public_key"] == VALID_WG_PUB
        assert "placeholder" not in body["public_key"]

        assert captured["path"] == "/vpn/generate-keys"
        assert captured["service"] == "vpn"

        async with TestSessionLocal() as session:
            refreshed = await session.get(VPNClient, client_id)
        assert refreshed.public_key == VALID_WG_PUB
        assert "placeholder" not in refreshed.public_key
        assert refreshed.config_file
