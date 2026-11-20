"""Tests for the background metrics collector."""

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from shared.database import get_db
from shared.models import Base, Instance, MetricSnapshot, User
from shared.security import get_password_hash
from shared.models import VPNServer


pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Generated per test run so no static credential-shaped literal lands in the repo.
TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def inactive_instance():
    async with TestSessionLocal() as session:
        instance = Instance(
            name="collector-node",
            hostname="node1.example.local",
            api_endpoint="https://node1.example.local/api/v1",
            api_key=TEST_INSTANCE_KEY,
            status="inactive",
        )
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        yield instance


async def test_collects_for_instances_that_are_not_active(inactive_instance, monkeypatch):
    """Instances stay 'inactive' until an agent heartbeat arrives — the
    collector must still produce snapshots for them (simulated metrics)."""
    from metrics_collector import run_metrics_collection_cycle

    # This instance has no mail agent (no agent_endpoints.mail) — stub the
    # fetch as unavailable so the test makes no real network call.
    import metrics_collector

    monkeypatch.setattr(
        metrics_collector, "_mail_stats", AsyncMock(return_value=None)
    )

    async with TestSessionLocal() as db:
        inserted = await run_metrics_collection_cycle(db)

    assert inserted == 1
    async with TestSessionLocal() as db:
        result = await db.execute(
            select(MetricSnapshot).where(MetricSnapshot.instance_id == inactive_instance.id)
        )
        snapshots = result.scalars().all()
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.cpu_percent is not None
    assert snapshot.timestamp <= datetime.utcnow() + timedelta(seconds=5)
    # Real host metrics from psutil: usage counters never exceed capacity
    assert snapshot.memory_used_bytes <= snapshot.memory_total_bytes
    assert snapshot.disk_used_bytes <= snapshot.disk_total_bytes
    # Interface stats are real interfaces with byte counters (loopback and
    # container/virtual bridges are filtered out)
    assert isinstance(snapshot.interface_stats, list)
    for iface in snapshot.interface_stats:
        assert iface["name"] != "lo"
        assert iface["rx_bytes"] >= 0
        assert iface["tx_bytes"] >= 0
    # Mail fields stay NULL: the fixture instance has no agent_endpoints.mail,
    # so its mail agent is unavailable (fields absent rather than invented)
    assert snapshot.mail_queue_size is None
    assert snapshot.mail_inbound_count is None
    assert snapshot.mail_outbound_count is None
    assert snapshot.mail_spam_count is None
    assert snapshot.mail_virus_count is None


async def test_redis_lock_falls_back_to_collecting_when_unavailable(monkeypatch):
    """If Redis is down, collection must proceed rather than stall."""
    import metrics_collector

    def _boom(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr("redis.asyncio.Redis.from_url", _boom)
    assert await metrics_collector._try_acquire_cycle_lock() is True


async def test_redis_lock_deduplicates_when_held(monkeypatch):
    import metrics_collector

    redis_mock = MagicMock()
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.aclose = AsyncMock()
    monkeypatch.setattr(
        "redis.asyncio.Redis", MagicMock(from_url=MagicMock(return_value=redis_mock))
    )

    assert await metrics_collector._try_acquire_cycle_lock() is True
    redis_mock.set.assert_awaited_once()
    kwargs = redis_mock.set.await_args.kwargs
    assert kwargs.get("nx") is True
    assert kwargs.get("ex") == 55  # METRICS_INTERVAL default 60 - 5


async def test_parse_proc_net_dev_keeps_raw_rows(tmp_path):
    """Host /proc/net/dev parsing: name plus rx/tx byte counters per row."""
    from metrics_collector import _parse_proc_net_dev

    proc_net_dev = tmp_path / "dev"
    proc_net_dev.write_text(
        "Inter-|   Receive                                                "
        "|  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed "
        "multicast|bytes    packets errs drop fifo colls carrier\n"
        "    lo: 1000 10 0 0 0 0 0 0 2000 20 0 0 0 0 0\n"
        " enp6s0: 5000 50 0 0 0 0 0 0 7000 70 0 0 0 0 0\n"
        "  veth9a1b2c: 300 3 0 0 0 0 0 0 400 4 0 0 0 0 0\n"
    )

    assert _parse_proc_net_dev(proc_net_dev) == [
        {"name": "lo", "rx_bytes": 1000, "tx_bytes": 2000},
        {"name": "enp6s0", "rx_bytes": 5000, "tx_bytes": 7000},
        {"name": "veth9a1b2c", "rx_bytes": 300, "tx_bytes": 400},
    ]


async def test_interface_stats_exclude_loopback_and_virtual(monkeypatch, tmp_path):
    """Loopback and container bridges are dashboard noise; VPN tunnels stay."""
    from metrics_collector import _interface_stats

    (tmp_path / "net").mkdir()
    proc_net_dev = tmp_path / "net" / "dev"
    proc_net_dev.write_text(
        "Inter-|   Receive                                                "
        "|  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed "
        "multicast|bytes    packets errs drop fifo colls carrier\n"
        "    lo: 1 0 0 0 0 0 0 0 1 0 0 0 0 0\n"
        "  eth0: 100 0 0 0 0 0 0 0 200 0 0 0 0 0\n"
        "docker0: 5 0 0 0 0 0 0 0 5 0 0 0 0 0\n"
        "br-f00d: 6 0 0 0 0 0 0 0 6 0 0 0 0 0\n"
        "   wg0: 7 0 0 0 0 0 0 0 7 0 0 0 0 0\n"
    )
    monkeypatch.setattr("metrics_collector.HOST_PROC", tmp_path)

    names = [s["name"] for s in _interface_stats()]

    assert "lo" not in names
    assert "docker0" not in names
    assert "br-f00d" not in names
    assert "eth0" in names
    assert "wg0" in names


async def test_interface_stats_returns_empty_without_host_proc_mount(
    monkeypatch, caplog
):
    """Without the host /proc bind mount psutil would report the gateway
    container's own interfaces — it must never be consulted."""
    from metrics_collector import _interface_stats

    def _forbidden(*args, **kwargs):
        raise AssertionError(
            "psutil.net_io_counters must not be called without /host/proc"
        )

    monkeypatch.setattr(
        "metrics_collector.HOST_PROC", Path("/nonexistent-host-proc-mount")
    )
    monkeypatch.setattr("psutil.net_io_counters", _forbidden)

    with caplog.at_level(logging.WARNING):
        stats = _interface_stats()

    assert stats == []
    assert "skipping container-scoped interface collection" in caplog.text


def _cum(received, delivered, spam, virus, queue=3):
    return {
        "queue_length": queue,
        "received": received,
        "delivered": delivered,
        "rejected_spam": spam,
        "rejected_virus": virus,
    }


MAIL_DELTA_FIELDS = (
    "mail_inbound_count",
    "mail_outbound_count",
    "mail_spam_count",
    "mail_virus_count",
)


async def test_collect_instance_metrics_computes_mail_deltas(
    monkeypatch, inactive_instance
):
    """Two consecutive cycles with different cumulative counters produce the
    correct per-interval deltas; the baseline cycle only stores the queue."""
    import metrics_collector

    state = {}

    async def fake_prev(instance_id):
        return state.get(instance_id)

    async def fake_store(instance_id, cum):
        state[instance_id] = cum

    monkeypatch.setattr(metrics_collector, "_mail_prev_from_redis", fake_prev)
    monkeypatch.setattr(metrics_collector, "_store_mail_cum", fake_store)
    monkeypatch.setattr(
        metrics_collector,
        "_mail_stats",
        AsyncMock(side_effect=[_cum(100, 200, 5, 1), _cum(107, 215, 8, 2, queue=6)]),
    )

    async with TestSessionLocal() as db:
        first = await metrics_collector.collect_instance_metrics(db, inactive_instance)
        second = await metrics_collector.collect_instance_metrics(db, inactive_instance)

    assert first["mail_queue_size"] == 3
    assert "mail_inbound_count" not in first
    assert second["mail_queue_size"] == 6
    assert second["mail_inbound_count"] == 7
    assert second["mail_outbound_count"] == 15
    assert second["mail_spam_count"] == 3
    assert second["mail_virus_count"] == 1


async def test_first_mail_observation_stores_baseline_without_deltas(
    monkeypatch, inactive_instance
):
    """No prior cumulative → only the queue size lands in the snapshot dict;
    delta fields stay absent (NULL columns in the DB)."""
    import metrics_collector

    monkeypatch.setattr(
        metrics_collector, "_mail_prev_from_redis", AsyncMock(return_value=None)
    )
    store_mock = AsyncMock()
    monkeypatch.setattr(metrics_collector, "_store_mail_cum", store_mock)
    baseline = _cum(100, 200, 5, 1)
    monkeypatch.setattr(
        metrics_collector, "_mail_stats", AsyncMock(return_value=baseline)
    )

    async with TestSessionLocal() as db:
        result = await metrics_collector.collect_instance_metrics(db, inactive_instance)

    assert result["mail_queue_size"] == 3
    for field in MAIL_DELTA_FIELDS:
        assert field not in result
    store_mock.assert_awaited_once_with(inactive_instance.id, baseline)


async def test_mail_fields_absent_when_agent_unavailable(
    monkeypatch, inactive_instance
):
    """Agent unreachable → mail fields absent and system metrics unaffected."""
    import metrics_collector

    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    prev_mock = AsyncMock()
    store_mock = AsyncMock()
    monkeypatch.setattr(metrics_collector, "_mail_prev_from_redis", prev_mock)
    monkeypatch.setattr(metrics_collector, "_store_mail_cum", store_mock)

    async with TestSessionLocal() as db:
        result = await metrics_collector.collect_instance_metrics(db, inactive_instance)

    for field in ("mail_queue_size", *MAIL_DELTA_FIELDS):
        assert field not in result
    assert result["cpu_percent"] is not None
    assert result["memory_used_bytes"] <= result["memory_total_bytes"]
    assert isinstance(result["interface_stats"], list)
    prev_mock.assert_not_awaited()
    store_mock.assert_not_awaited()


async def test_mail_counter_reset_clamps_deltas_to_zero(
    monkeypatch, inactive_instance
):
    """Agent cumulative resets to a lower value → deltas clamp to 0 for one
    interval instead of going negative."""
    import metrics_collector

    monkeypatch.setattr(
        metrics_collector,
        "_mail_prev_from_redis",
        AsyncMock(return_value=_cum(500, 600, 50, 20)),
    )
    monkeypatch.setattr(metrics_collector, "_store_mail_cum", AsyncMock())
    monkeypatch.setattr(
        metrics_collector,
        "_mail_stats",
        AsyncMock(return_value=_cum(490, 580, 12, 0, queue=2)),
    )

    async with TestSessionLocal() as db:
        result = await metrics_collector.collect_instance_metrics(db, inactive_instance)

    assert result["mail_queue_size"] == 2
    assert result["mail_inbound_count"] == 0
    assert result["mail_outbound_count"] == 0
    assert result["mail_spam_count"] == 0
    assert result["mail_virus_count"] == 0


class _FakeStatsResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeStatsClient:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get(self, url):
        assert url == "http://mail-agent.internal:9000/stats"
        return _FakeStatsResponse(self._payload)


async def test_mail_stats_parses_agent_counters(monkeypatch, inactive_instance):
    """/stats contract: queue_length merged with the cumulative mail dict."""
    import httpx
    from metrics_collector import _mail_stats

    monkeypatch.setattr(
        "utils.agent_client.get_instance_endpoint",
        AsyncMock(return_value="http://mail-agent.internal:9000"),
    )
    payload = {
        "queue_length": 4,
        "mail": {"received": 10, "delivered": 9, "rejected_spam": 2, "rejected_virus": 1},
    }
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: _FakeStatsClient(payload)
    )

    async with TestSessionLocal() as db:
        assert await _mail_stats(db, inactive_instance) == _cum(10, 9, 2, 1, queue=4)


async def test_mail_stats_returns_none_when_agent_log_unreadable(
    monkeypatch, inactive_instance
):
    """/stats answering {"queue_length": N, "mail": null} → None, not garbage."""
    import httpx
    from metrics_collector import _mail_stats

    monkeypatch.setattr(
        "utils.agent_client.get_instance_endpoint",
        AsyncMock(return_value="http://mail-agent.internal:9000"),
    )
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: _FakeStatsClient({"queue_length": 4, "mail": None}),
    )

    async with TestSessionLocal() as db:
        assert await _mail_stats(db, inactive_instance) is None


@pytest_asyncio.fixture
async def node_instance():
    """Instance WITH a node agent configured (config.agent_endpoints.node)."""
    async with TestSessionLocal() as session:
        instance = Instance(
            name="collector-node-agent",
            hostname="nodeagent.example.local",
            api_endpoint="https://nodeagent.example.local/api/v1",
            api_key=TEST_INSTANCE_KEY,
            status="inactive",
            config={"agent_endpoints": {"node": "http://127.0.0.1:8085"}},
        )
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        yield instance


class _FakeNodeStatsClient:
    """Captures each node /stats request so URL and auth header are
    assertable without a real network call."""

    def __init__(self, payload):
        self._payload = payload
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get(self, url, headers=None):
        self.requests.append({"url": url, "headers": headers or {}})
        return _FakeStatsResponse(self._payload)


async def test_node_stats_configured_stores_per_instance_counters(
    monkeypatch, node_instance
):
    """agent_endpoints.node configured → interface counters come from that
    instance's node-agent /stats (X-Instance-Key auth), with loopback and
    container interfaces filtered out, and land in the stored snapshot."""
    import httpx
    import metrics_collector

    fake_client = _FakeNodeStatsClient(
        {
            "interfaces": [
                {"name": "lo", "rx_bytes": 11, "tx_bytes": 22},
                {"name": "veth0", "rx_bytes": 33, "tx_bytes": 44},
                {"name": "enp0s31f6", "rx_bytes": 123, "tx_bytes": 456},
            ]
        }
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))

    async with TestSessionLocal() as db:
        inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    assert fake_client.requests == [
        {
            "url": "http://127.0.0.1:8085/stats",
            "headers": {"X-Instance-Key": TEST_INSTANCE_KEY},
        }
    ]
    async with TestSessionLocal() as db:
        result = await db.execute(
            select(MetricSnapshot).where(
                MetricSnapshot.instance_id == node_instance.id
            )
        )
        snapshot = result.scalars().one()
    assert snapshot.interface_stats == [
        {"name": "enp0s31f6", "rx_bytes": 123, "tx_bytes": 456}
    ]


async def test_node_stats_agent_unreachable_stores_null_and_keeps_system_mail(
    monkeypatch, node_instance, caplog
):
    """Node agent down → interface_stats stays None (never gateway-local
    data, so the instance's series stays pure), system fields are unaffected
    and the miss is logged as a warning."""
    import logging

    import httpx
    import metrics_collector

    class _UnreachableClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def get(self, url, headers=None):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _UnreachableClient())
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))

    with caplog.at_level(logging.WARNING, logger="metrics_collector"):
        async with TestSessionLocal() as db:
            result = await metrics_collector.collect_instance_metrics(db, node_instance)

    assert result["interface_stats"] is None
    assert result["cpu_percent"] is not None
    assert result["memory_used_bytes"] <= result["memory_total_bytes"]
    # Mail fields follow the existing unavailable-agent semantics: absent
    # rather than invented.
    assert "mail_queue_size" not in result
    assert "node /stats fetch failed" in caplog.text


async def test_node_stats_unconfigured_falls_back_to_gateway_local(
    monkeypatch, inactive_instance
):
    """No agent_endpoints.node → the legacy gateway-local interface read
    stays the source (the fixture instance has no config at all)."""
    import metrics_collector

    sentinel = [{"name": "gwlocal0", "rx_bytes": 7, "tx_bytes": 9}]
    monkeypatch.setattr(metrics_collector, "_interface_stats", lambda: sentinel)

    async with TestSessionLocal() as db:
        result = await metrics_collector.collect_instance_metrics(db, inactive_instance)

    assert result["interface_stats"] is sentinel


async def test_mail_cumulative_round_trips_through_redis(monkeypatch):
    """The cumulative counters JSON round-trip through the Redis state key."""
    import metrics_collector

    stored = {}
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(side_effect=lambda key: stored.get(key))
    redis_mock.set = AsyncMock(
        side_effect=lambda key, value: stored.__setitem__(key, value)
    )
    redis_mock.aclose = AsyncMock()
    monkeypatch.setattr(
        "redis.asyncio.Redis", MagicMock(from_url=MagicMock(return_value=redis_mock))
    )

    assert await metrics_collector._mail_prev_from_redis(42) is None

    cum = _cum(10, 9, 2, 1, queue=3)
    await metrics_collector._store_mail_cum(42, cum)

    assert stored["viswall:metrics:mail_cum:42"] == json.dumps(cum)
    assert await metrics_collector._mail_prev_from_redis(42) == cum


async def test_mail_cumulative_redis_failure_returns_none(monkeypatch):
    """Redis down → previous cumulative reads as None (baseline mode for one
    interval) instead of raising."""
    import metrics_collector

    def _boom(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr("redis.asyncio.Redis.from_url", _boom)
    assert await metrics_collector._mail_prev_from_redis(1) is None


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def dashboard_client(client: AsyncClient):
    """App client with get_db pointed at this file's SQLite engine."""
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield client
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


@pytest_asyncio.fixture
async def dashboard_user():
    async with TestSessionLocal() as session:
        user = User(
            username="metricsadmin",
            email="metricsadmin@example.com",
            password_hash=get_password_hash("metricsadminpass"),
            auth_backend="local",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest_asyncio.fixture
async def mail_snapshot(inactive_instance):
    async with TestSessionLocal() as session:
        snapshot = MetricSnapshot(
            instance_id=inactive_instance.id,
            mail_queue_size=3,
            mail_inbound_count=7,
            mail_outbound_count=15,
            mail_spam_count=3,
            mail_virus_count=1,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        yield snapshot


async def _dashboard(dashboard_client: AsyncClient, instance_id: int):
    login = await dashboard_client.post(
        "/api/v1/auth/login",
        json={"username": "metricsadmin", "password": "metricsadminpass"},
    )
    assert login.status_code == 200
    return await dashboard_client.get(
        f"/api/v1/metrics/dashboard/{instance_id}",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )


def _redis_mock(monkeypatch, raw_value):
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=raw_value)
    redis_mock.aclose = AsyncMock()
    monkeypatch.setattr(
        "redis.asyncio.Redis", MagicMock(from_url=MagicMock(return_value=redis_mock))
    )


async def test_dashboard_mail_totals_read_from_redis(
    dashboard_client, dashboard_user, inactive_instance, mail_snapshot, monkeypatch
):
    """Redis holds the collector's cumulative key → the dashboard mail dict
    gains the lifetime totals alongside the unchanged snapshot fields."""
    _redis_mock(monkeypatch, json.dumps(_cum(826, 833, 44, 4, queue=5)))

    response = await _dashboard(dashboard_client, inactive_instance.id)

    assert response.status_code == 200
    mail = response.json()["mail"]
    assert mail["queue_size"] == 3
    assert mail["inbound_count"] == 7
    assert mail["outbound_count"] == 15
    assert mail["spam_count"] == 3
    assert mail["virus_count"] == 1
    assert mail["total_received"] == 826
    assert mail["total_delivered"] == 833
    assert mail["total_spam"] == 44
    assert mail["total_virus"] == 4
    assert mail["totals_available"] is True


async def test_dashboard_mail_totals_none_when_redis_down(
    dashboard_client, dashboard_user, inactive_instance, monkeypatch
):
    """Redis unreachable → the endpoint still returns 200 with None totals."""

    def _boom(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr("redis.asyncio.Redis.from_url", _boom)

    response = await _dashboard(dashboard_client, inactive_instance.id)

    assert response.status_code == 200
    mail = response.json()["mail"]
    assert mail["total_received"] is None
    assert mail["total_delivered"] is None
    assert mail["total_spam"] is None
    assert mail["total_virus"] is None
    assert mail["totals_available"] is False


async def test_dashboard_mail_totals_none_without_redis_key(
    dashboard_client, dashboard_user, inactive_instance, monkeypatch
):
    """No cumulative key stored yet → totals None, flag False, still 200."""
    _redis_mock(monkeypatch, None)

    response = await _dashboard(dashboard_client, inactive_instance.id)

    assert response.status_code == 200
    mail = response.json()["mail"]
    assert mail["total_received"] is None
    assert mail["total_delivered"] is None
    assert mail["total_spam"] is None
    assert mail["total_virus"] is None
    assert mail["totals_available"] is False


@pytest.mark.parametrize(
    "raw_value", ["{not json", "[1, 2, 3]", '"just-a-string"']
)
async def test_dashboard_mail_totals_none_on_malformed_redis_value(
    raw_value, dashboard_client, dashboard_user, inactive_instance, monkeypatch
):
    """Corrupt or wrong-shape Redis value → no 500, totals degrade to None."""
    _redis_mock(monkeypatch, raw_value)

    response = await _dashboard(dashboard_client, inactive_instance.id)

    assert response.status_code == 200
    mail = response.json()["mail"]
    assert mail["total_received"] is None
    assert mail["total_delivered"] is None
    assert mail["total_spam"] is None
    assert mail["total_virus"] is None
    assert mail["totals_available"] is False


@pytest_asyncio.fixture
async def vpn_instance():
    """Instance with a VPN agent endpoint configured (agent_endpoints.vpn).

    The trailing slash pins the rstrip in the endpoint helper."""
    async with TestSessionLocal() as session:
        instance = Instance(
            name="collector-vpn-agent",
            hostname="vpnagent.example.local",
            api_endpoint="https://vpnagent.example.local/api/v1",
            api_key=TEST_INSTANCE_KEY,
            status="inactive",
            config={"agent_endpoints": {"vpn": "http://127.0.0.1:8086/"}},
        )
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        yield instance


def _vpn_agent_payload(rx: int, tx: int, up: bool = True) -> dict:
    return {
        "up": up,
        "interface": "client",
        "transfer_rx": rx,
        "transfer_tx": tx,
        "latest_handshake_sec": 30,
        "peer_public_key": "pubkey-placeholder",
        "endpoint": "base0.example:51820",
    }


async def _seed_vpn_row(instance_id: int, **fields) -> VPNServer:
    defaults = {
        "name": "tunnel",
        "protocol": "wireguard",
        "tunnel_type": "site-to-site",
        "enabled": True,
        "bytes_received": 0,
        "bytes_sent": 0,
        "status": "stopped",
    }
    defaults.update(fields)
    async with TestSessionLocal() as session:
        row = VPNServer(instance_id=instance_id, **defaults)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def _get_vpn_row(row_id: int) -> VPNServer:
    async with TestSessionLocal() as session:
        return await session.get(VPNServer, row_id)


def _vpn_redis_fakes(monkeypatch, prev):
    """In-memory prev/store stand-ins (mail delta-test pattern); returns
    the list of stored baselines."""
    import metrics_collector

    stored = []

    async def fake_prev(instance_id):
        return prev

    async def fake_store(instance_id, cum):
        stored.append((instance_id, cum))

    monkeypatch.setattr(metrics_collector, "_vpn_prev_from_redis", fake_prev)
    monkeypatch.setattr(metrics_collector, "_store_vpn_cum", fake_store)
    return stored


async def test_vpn_traffic_first_observation_stores_baseline_row_bytes_untouched(
    monkeypatch, vpn_instance
):
    """No prior cumulative → baseline stored in Redis, zero deltas applied;
    the row's lifetime bytes stay untouched (status is still reconciled)."""
    import httpx
    import metrics_collector

    stored = _vpn_redis_fakes(monkeypatch, prev=None)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(vpn_instance.id)
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(1000, 500, up=True))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    assert stored == [
        (vpn_instance.id, {"transfer_rx": 1000, "transfer_tx": 500})
    ]
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 0
    assert row.bytes_sent == 0
    assert row.status == "running"


async def test_vpn_traffic_second_observation_accumulates_exact_deltas(
    monkeypatch, vpn_instance
):
    """Deltas = current cumulative − previous baseline, added onto whatever
    lifetime totals the row already carries."""
    import httpx
    import metrics_collector

    _vpn_redis_fakes(
        monkeypatch, prev={"transfer_rx": 1000, "transfer_tx": 500}
    )
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(vpn_instance.id, bytes_received=700, bytes_sent=300)
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(3500, 1500, up=True))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        await metrics_collector.run_metrics_collection_cycle(db)

    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 700 + 2500
    assert row.bytes_sent == 300 + 1000
    assert row.status == "running"


async def test_vpn_traffic_counter_reset_clamps_deltas_to_zero_and_status_stopped(
    monkeypatch, vpn_instance
):
    """Agent cumulative reset (current < previous) → deltas clamp to 0 and
    the reset value becomes the new baseline; up=false reconciles the row
    status to stopped."""
    import httpx
    import metrics_collector

    stored = _vpn_redis_fakes(
        monkeypatch, prev={"transfer_rx": 5000, "transfer_tx": 2000}
    )
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(
        vpn_instance.id, bytes_received=100, bytes_sent=50, status="running"
    )
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(2000, 900, up=False))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        await metrics_collector.run_metrics_collection_cycle(db)

    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 100
    assert row.bytes_sent == 50
    assert row.status == "stopped"
    assert stored == [
        (vpn_instance.id, {"transfer_rx": 2000, "transfer_tx": 900})
    ]


async def test_vpn_stats_agent_unreachable_row_untouched_snapshot_kept(
    monkeypatch, vpn_instance, caplog
):
    """VPN agent down (ConnectError) → no VPN write at all, but the
    instance's system/mail snapshot is still inserted."""
    import logging

    import httpx
    import metrics_collector

    class _UnreachableClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def get(self, url, headers=None):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _UnreachableClient())
    monkeypatch.setattr(
        metrics_collector, "_mail_stats", AsyncMock(return_value=_cum(100, 200, 5, 1))
    )
    monkeypatch.setattr(
        metrics_collector, "_mail_prev_from_redis", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(metrics_collector, "_store_mail_cum", AsyncMock())
    row = await _seed_vpn_row(vpn_instance.id, status="error")

    with caplog.at_level(logging.WARNING, logger="metrics_collector"):
        async with TestSessionLocal() as db:
            inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 0
    assert row.bytes_sent == 0
    assert row.status == "error"
    async with TestSessionLocal() as db:
        snapshot = (
            await db.execute(
                select(MetricSnapshot).where(
                    MetricSnapshot.instance_id == vpn_instance.id
                )
            )
        ).scalars().one()
    assert snapshot.cpu_percent is not None
    assert snapshot.mail_queue_size == 3
    assert "vpn /stats fetch failed" in caplog.text


async def test_vpn_stats_no_endpoint_makes_no_http_call(
    monkeypatch, inactive_instance
):
    """agent_endpoints.vpn unset → no HTTP call at all. The fixture has a
    non-null api_endpoint and no vpn key: an implementation wrongly using
    get_instance_endpoint() would fall back to it and GET the gateway's
    own /stats — the zero-call assert pins that trap."""
    import httpx
    import metrics_collector

    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(1, 1))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(inactive_instance.id)

    async with TestSessionLocal() as db:
        inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    assert fake_client.requests == []
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 0
    assert row.bytes_sent == 0
    assert row.status == "stopped"


async def test_vpn_stats_request_uses_stats_path_and_instance_key(
    monkeypatch, vpn_instance
):
    """The agent call is GET {vpn endpoint}/stats with X-Instance-Key auth."""
    import httpx
    import metrics_collector

    _vpn_redis_fakes(monkeypatch, prev=None)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(10, 5))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        await metrics_collector.run_metrics_collection_cycle(db)

    assert fake_client.requests == [
        {
            "url": "http://127.0.0.1:8086/stats",
            "headers": {"X-Instance-Key": TEST_INSTANCE_KEY},
        }
    ]


async def test_vpn_traffic_selects_first_enabled_wireguard_tunnel(
    monkeypatch, vpn_instance
):
    """Bytes land on the first enabled WG client/site-to-site row; an
    earlier enabled non-WireGuard row, a later WG row and a disabled WG
    row are all left alone."""
    import httpx
    import metrics_collector

    _vpn_redis_fakes(
        monkeypatch, prev={"transfer_rx": 1000, "transfer_tx": 500}
    )
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    non_wg = await _seed_vpn_row(
        vpn_instance.id,
        name="ipsec-tunnel",
        protocol="ipsec",
        bytes_received=9999,
        bytes_sent=9999,
    )
    target = await _seed_vpn_row(
        vpn_instance.id, name="wg-client", tunnel_type="client"
    )
    later = await _seed_vpn_row(
        vpn_instance.id, name="wg-later", bytes_received=5, bytes_sent=5
    )
    disabled = await _seed_vpn_row(
        vpn_instance.id, name="wg-disabled", tunnel_type="client", enabled=False
    )
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(2000, 700, up=True))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        await metrics_collector.run_metrics_collection_cycle(db)

    assert (await _get_vpn_row(target.id)).bytes_received == 1000
    assert (await _get_vpn_row(target.id)).bytes_sent == 200
    for untouched in (non_wg, later, disabled):
        fresh = await _get_vpn_row(untouched.id)
        assert fresh.bytes_received == untouched.bytes_received
        assert fresh.bytes_sent == untouched.bytes_sent
        assert fresh.status == "stopped"


async def test_vpn_traffic_no_qualifying_row_stores_baseline_without_write(
    monkeypatch, vpn_instance
):
    """Only a non-WireGuard tunnel configured → no row write, but the Redis
    baseline is still stored so the series resumes cleanly once a WG row
    is added."""
    import httpx
    import metrics_collector

    stored = _vpn_redis_fakes(monkeypatch, prev=None)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(
        vpn_instance.id, protocol="openvpn", tunnel_type="client", status="error"
    )
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(42, 17, up=True))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    assert stored == [
        (vpn_instance.id, {"transfer_rx": 42, "transfer_tx": 17})
    ]
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 0
    assert row.bytes_sent == 0
    assert row.status == "error"


async def test_vpn_traffic_failure_does_not_skip_instance_snapshot(
    monkeypatch, vpn_instance, caplog
):
    """_apply_vpn_traffic raising must not cost the instance its snapshot:
    the inner guard catches it and the cycle still inserts and commits."""
    import logging

    import metrics_collector

    row = await _seed_vpn_row(vpn_instance.id)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    monkeypatch.setattr(
        metrics_collector,
        "_apply_vpn_traffic",
        AsyncMock(side_effect=RuntimeError("vpn collector bug")),
    )

    with caplog.at_level(logging.WARNING, logger="metrics_collector"):
        async with TestSessionLocal() as db:
            inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    assert "VPN traffic accumulation failed" in caplog.text
    # The cycle-level handler did not fire — the dedicated guard caught it.
    assert "Failed to collect metrics" not in caplog.text
    async with TestSessionLocal() as db:
        snapshots = (
            await db.execute(
                select(MetricSnapshot).where(
                    MetricSnapshot.instance_id == vpn_instance.id
                )
            )
        ).scalars().all()
    assert len(snapshots) == 1
    assert snapshots[0].cpu_percent is not None
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 0
    assert row.bytes_sent == 0


async def test_vpn_traffic_redis_failure_baseline_mode_zero_deltas(
    monkeypatch, vpn_instance
):
    """Redis get/set raising → baseline mode: deltas 0 so the row's bytes
    are unchanged (no garbage from a failed read), status reconciliation
    is Redis-independent, the snapshot is unaffected, nothing raises."""

    def _boom(*args, **kwargs):
        raise ConnectionError("redis down")

    import httpx
    import metrics_collector

    monkeypatch.setattr("redis.asyncio.Redis.from_url", _boom)
    monkeypatch.setattr(metrics_collector, "_mail_stats", AsyncMock(return_value=None))
    row = await _seed_vpn_row(
        vpn_instance.id, bytes_received=500, bytes_sent=300, status="stopped"
    )
    fake_client = _FakeNodeStatsClient(_vpn_agent_payload(9000, 8000, up=True))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake_client)

    async with TestSessionLocal() as db:
        inserted = await metrics_collector.run_metrics_collection_cycle(db)

    assert inserted == 1
    row = await _get_vpn_row(row.id)
    assert row.bytes_received == 500
    assert row.bytes_sent == 300
    assert row.status == "running"
    async with TestSessionLocal() as db:
        snapshot = (
            await db.execute(
                select(MetricSnapshot).where(
                    MetricSnapshot.instance_id == vpn_instance.id
                )
            )
        ).scalars().one()
    assert snapshot.cpu_percent is not None
