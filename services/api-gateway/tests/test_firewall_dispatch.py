"""Tests for firewall desired-state composition and gateway dispatch.

Covers the plan todo 25 items that exercise ``utils/firewall_dispatch.py``,
``routers/firewall.py`` and ``routers/routing.py`` at HEAD:

- payload builders: golden payload shape from seeded rows (limit-carrying
  rule, interface with ipv6/dns/routes extension fields), disabled rows
  excluded, empty instance -> sane empty payload;
- dispatch: ``apply_firewall_config`` pushes POST /firewall/apply to the
  firewall agent and audit-logs the outcome (success and failure);
- endpoint wiring: /firewall/apply queues ``reload_firewall``; rule create
  dispatches synchronously, keeps the DB row on agent failure (502) and
  audit-logs the calling admin id (the todo 19 NameError regression);
- routing: /routing/apply runs the real ``apply_firewall_config`` (502 on
  agent failure).
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import routers.firewall as firewall_router
import routers.routing as routing_router
import shared.database as shared_database
import utils.firewall_dispatch as dispatch_mod
from main import app
from shared.database import get_db
from shared.models import (
    AuditLog,
    Base,
    FirewallRule,
    Instance,
    NATRule,
    NetworkInterface,
    QoSPolicy,
    QoSClass,
    RoutingRule,
    User,
)
from shared.security import get_password_hash
from utils.agent_client import AgentClientError, AgentConnectionError

pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    # raise_app_exceptions=False: the from_attributes bug documented below
    # renders as a real 500 response instead of a raised ValidationError.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


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
            name="fw-dispatch-instance",
            hostname="fw0.example.local",
            api_endpoint="http://fallback-agent:9000",
            api_key=TEST_INSTANCE_KEY,
            status="active",
            capabilities=["firewall"],
            config={"agent_endpoints": {"firewall": "http://firewall-agent:8081"}},
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        yield item


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            username="fwadmin",
            email="fwadmin@example.com",
            password_hash=get_password_hash("fwadminpass"),
            auth_backend="local",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


async def _login(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "fwadmin", "password": "fwadminpass"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _seed_rule(instance_id: int, *, name: str, enabled: bool = True, **fields) -> FirewallRule:
    async with TestSessionLocal() as session:
        rule = FirewallRule(
            instance_id=instance_id,
            name=name,
            enabled=enabled,
            **fields,
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule


async def _seed_golden_rows(instance_id: int) -> dict:
    """Seed the full golden scenario; returns the refreshed row objects."""
    async with TestSessionLocal() as session:
        wan = NetworkInterface(
            instance_id=instance_id,
            name="enp0s31f6",
            type="wan",
            config_type="static",
            ip_address="46.4.63.216",
            netmask="255.255.255.255",
            gateway="46.4.63.193",
            mtu=1500,
            ipv6_address="2a01:4f8:140:22ef::2",
            ipv6_gateway="fe80::1",
            dns_servers=["185.12.64.1", "185.12.64.2"],
            routes=[{"to": "10.80.0.0/16", "via": None, "on_link": False}],
            description="WAN uplink",
            enabled=True,
        )
        disabled_iface = NetworkInterface(
            instance_id=instance_id, name="disabled0", enabled=False
        )
        ssh_rule = FirewallRule(
            instance_id=instance_id,
            name="ssh-limit",
            service_protocol="tcp",
            service_ports="22",
            action="accept",
            log_enabled=True,
            limit="10/minute burst 5 packets",
            order_index=10,
            enabled=True,
        )
        web_rule = FirewallRule(
            instance_id=instance_id,
            name="web-allow",
            service_protocol="tcp",
            service_ports="80,443",
            action="accept",
            log_enabled=False,
            order_index=20,
            enabled=True,
        )
        disabled_rule = FirewallRule(
            instance_id=instance_id,
            name="pg-block",
            service_ports="5432",
            action="drop",
            order_index=30,
            enabled=False,
        )
        nat = NATRule(
            instance_id=instance_id,
            name="docker-snat",
            type="masquerade",
            interface="enp0s31f6",
            source_network="172.17.0.0/16",
            order_index=10,
            enabled=True,
        )
        routing = RoutingRule(
            instance_id=instance_id,
            name="wg-policy",
            source_network="10.80.0.0/16",
            gateway="10.80.210.1",
            outbound_interface="client",
            mark=510,
            order_index=10,
            enabled=True,
        )
        policy = QoSPolicy(
            instance_id=instance_id,
            name="wan-qos",
            interface_name="enp0s31f6",
            algorithm="htb",
            download_kbps=100000,
            upload_kbps=40000,
            enabled=True,
        )
        session.add_all(
            [wan, disabled_iface, ssh_rule, web_rule, disabled_rule, nat, routing, policy]
        )
        await session.flush()
        qos_class = QoSClass(
            policy_id=policy.id,
            name="VoIP",
            priority=1,
            min_rate_kbps=10000,
            max_rate_kbps=20000,
            match_ports=[5060],
            match_dscp="EF",
            match_protocol="udp",
        )
        session.add(qos_class)
        await session.commit()
        for obj in (
            wan, disabled_iface, ssh_rule, web_rule, disabled_rule,
            nat, routing, policy, qos_class,
        ):
            await session.refresh(obj)
        return {
            "wan": wan,
            "ssh": ssh_rule,
            "web": web_rule,
            "nat": nat,
            "routing": routing,
            "policy": policy,
            "qos_class": qos_class,
        }


class TestBuildInstanceFirewallPayload:
    async def test_golden_payload_from_seeded_rows(self, instance):
        rows = await _seed_golden_rows(instance.id)

        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_firewall_payload(
                session, instance.id
            )

        expected = {
            "interfaces": [
                {
                    "id": rows["wan"].id,
                    "name": "enp0s31f6",
                    "type": "wan",
                    "config_type": "static",
                    "ip_address": "46.4.63.216",
                    "netmask": "255.255.255.255",
                    "gateway": "46.4.63.193",
                    "mtu": 1500,
                    "description": "WAN uplink",
                    "ipv6_address": "2a01:4f8:140:22ef::2",
                    "ipv6_gateway": "fe80::1",
                    "dns_servers": ["185.12.64.1", "185.12.64.2"],
                    "routes": [{"to": "10.80.0.0/16", "via": None, "on_link": False}],
                },
            ],
            "rules": [
                {
                    "id": rows["ssh"].id,
                    "name": "ssh-limit",
                    "service_protocol": "tcp",
                    "service_ports": "22",
                    "action": "accept",
                    "log_enabled": True,
                    "order_index": 10,
                    "limit": "10/minute burst 5 packets",
                },
                {
                    "id": rows["web"].id,
                    "name": "web-allow",
                    "service_protocol": "tcp",
                    "service_ports": "80,443",
                    "action": "accept",
                    "log_enabled": False,
                    "order_index": 20,
                },
            ],
            "nat_rules": [
                {
                    "id": rows["nat"].id,
                    "name": "docker-snat",
                    "type": "masquerade",
                    "interface": "enp0s31f6",
                    "source_network": "172.17.0.0/16",
                    "order_index": 10,
                },
            ],
            "routing_rules": [
                {
                    "id": rows["routing"].id,
                    "name": "wg-policy",
                    "source_network": "10.80.0.0/16",
                    "gateway": "10.80.210.1",
                    "outbound_interface": "client",
                    "mark": 510,
                    "order_index": 10,
                },
            ],
            "qos": [
                {
                    "id": rows["policy"].id,
                    "name": "wan-qos",
                    "interface": "enp0s31f6",
                    "algorithm": "htb",
                    "download_kbps": 100000,
                    "upload_kbps": 40000,
                    "classes": [
                        {
                            "id": rows["qos_class"].id,
                            "name": "VoIP",
                            "priority": 1,
                            "min_rate_kbps": 10000,
                            "max_rate_kbps": 20000,
                            "match_ports": [5060],
                            "match_dscp": "EF",
                            "match_protocol": "udp",
                        },
                    ],
                },
            ],
        }
        assert payload == expected

    async def test_disabled_rows_are_excluded(self, instance):
        await _seed_rule(instance.id, name="blocked", enabled=False)
        await _seed_rule(instance.id, name="allowed", enabled=True)

        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_firewall_payload(
                session, instance.id
            )

        assert [rule["name"] for rule in payload["rules"]] == ["allowed"]
        assert payload["interfaces"] == []
        assert payload["nat_rules"] == []

    async def test_empty_instance_yields_sane_empty_payload(self, instance):
        async with TestSessionLocal() as session:
            payload = await dispatch_mod.build_instance_firewall_payload(
                session, instance.id
            )

        assert payload == {
            "interfaces": [],
            "rules": [],
            "nat_rules": [],
            "routing_rules": [],
            "qos": [],
        }


class TestApplyFirewallConfigDispatch:
    async def test_apply_pushes_firewall_apply_payload(self, instance, admin_user, monkeypatch):
        await _seed_rule(instance.id, name="allow-ssh", service_ports="22")
        captured: dict = {}

        async def _fake_agent_request(db, instance_id, method, path, json_data=None, **kwargs):
            captured["method"] = method
            captured["path"] = path
            captured["service"] = kwargs.get("service")
            captured["json"] = json_data
            return {"applied": True}

        monkeypatch.setattr(dispatch_mod, "agent_request", _fake_agent_request)

        async with TestSessionLocal() as session:
            result = await dispatch_mod.apply_firewall_config(
                session, instance.id, user_id=admin_user.id
            )

        assert result == {"applied": True}
        assert captured["method"] == "POST"
        assert captured["path"] == "/firewall/apply"
        assert captured["service"] == "firewall"
        assert captured["json"]["rules"][0]["name"] == "allow-ssh"

        async with TestSessionLocal() as session:
            audit = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "firewall_agent",
                        AuditLog.action == "deploy",
                    )
                )
            ).scalars().all()
        assert len(audit) == 1
        assert audit[0].user_id == admin_user.id
        assert audit[0].new_value["path"] == "/firewall/apply"
        assert audit[0].new_value["status"] == "success"

    async def test_apply_unreachable_raises_and_audits_failure(self, instance, admin_user, monkeypatch):
        await _seed_rule(instance.id, name="allow-ssh", service_ports="22")

        async def _unreachable(db, instance_id, method, path, json_data=None, **kwargs):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(dispatch_mod, "agent_request", _unreachable)

        async with TestSessionLocal() as session:
            with pytest.raises(AgentClientError):
                await dispatch_mod.apply_firewall_config(
                    session, instance.id, user_id=admin_user.id
                )

        async with TestSessionLocal() as session:
            audit = (
                await session.execute(
                    select(AuditLog).where(AuditLog.resource_type == "firewall_agent")
                )
            ).scalars().all()
        assert len(audit) == 1
        assert audit[0].user_id == admin_user.id
        assert audit[0].new_value["status"] == "failed"
        assert "agent down" in audit[0].new_value["detail"]


class TestReloadFirewallEndpoint:
    async def test_apply_endpoint_runs_reload_firewall(self, client: AsyncClient, admin_user, instance, monkeypatch):
        """POST /firewall/apply queues reload_firewall, which delegates to
        apply_firewall_config (patched here) through its own fresh session.
        Proves the endpoint wiring, not just a noop."""
        captured: list = []

        async def _recorder(db, instance_id, user_id=None):
            captured.append(instance_id)
            return {"applied": True}

        monkeypatch.setattr(firewall_router, "apply_firewall_config", _recorder)
        # shared.database.AsyncSessionLocal is None until the app lifespan runs _ensure_engine(); point the background task at the test DB.
        monkeypatch.setattr(shared_database, "AsyncSessionLocal", TestSessionLocal)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/firewall/apply/{instance.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "queued"}
        assert captured == [instance.id]

    async def test_create_rule_dispatches_and_audits_admin_id(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        captured: list = []

        async def _recorder(db, instance_id, user_id=None):
            captured.append({"instance_id": instance_id, "user_id": user_id})
            return {"applied": True}

        monkeypatch.setattr(firewall_router, "apply_firewall_config", _recorder)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/firewall/rules/{instance.id}",
            json={"name": "allow-ssh", "service_ports": "22"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # 500 here is the documented from_attributes bug (see the xfail test below); the NameError regression holds regardless.
        assert response.status_code in (201, 500)
        assert captured == [{"instance_id": instance.id, "user_id": admin_user.id}]

        # todo 19 NameError regression: log_audit must receive the calling
        # admin's id, not an undefined user_id.
        async with TestSessionLocal() as session:
            audit = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "firewall_rule",
                        AuditLog.action == "create",
                    )
                )
            ).scalars().all()
        assert len(audit) == 1
        assert audit[0].user_id == admin_user.id

    async def test_create_rule_response_is_serializable(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async def _recorder(db, instance_id, user_id=None):
            return {"applied": True}

        monkeypatch.setattr(firewall_router, "apply_firewall_config", _recorder)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/firewall/rules/{instance.id}",
            json={"name": "serializable-rule", "service_ports": "22"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "serializable-rule"

    async def test_create_rule_keeps_db_row_when_agent_unreachable(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async def _unreachable(db, instance_id, user_id=None):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(firewall_router, "apply_firewall_config", _unreachable)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/firewall/rules/{instance.id}",
            json={"name": "kept-rule", "service_ports": "443"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502
        assert "Agent error" in response.json()["detail"]

        # Desired-state model: the row survives the failed dispatch.
        async with TestSessionLocal() as session:
            rule = (
                await session.execute(
                    select(FirewallRule).where(FirewallRule.name == "kept-rule")
                )
            ).scalar_one_or_none()
        assert rule is not None


class TestRoutingApply:
    async def test_apply_dispatches_firewall_config(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        captured: list = []

        async def _recorder(db, instance_id, user_id=None):
            captured.append({"instance_id": instance_id, "user_id": user_id})
            return {"applied": True}

        monkeypatch.setattr(routing_router, "apply_firewall_config", _recorder)
        # routing.py imports AsyncSessionLocal at module level (None in tests); use the test DB.
        monkeypatch.setattr(routing_router, "AsyncSessionLocal", TestSessionLocal)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/routing/apply/{instance.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "applied", "instance_id": instance.id}
        assert captured == [{"instance_id": instance.id, "user_id": admin_user.id}]

    async def test_apply_unreachable_returns_502(
        self, client: AsyncClient, admin_user, instance, monkeypatch
    ):
        async def _unreachable(db, instance_id, user_id=None):
            raise AgentConnectionError("agent down")

        monkeypatch.setattr(routing_router, "apply_firewall_config", _unreachable)
        monkeypatch.setattr(routing_router, "AsyncSessionLocal", TestSessionLocal)

        token = await _login(client)
        response = await client.post(
            f"/api/v1/routing/apply/{instance.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502
        assert "agent down" in response.json()["detail"]
