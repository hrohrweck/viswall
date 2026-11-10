"""Tests for the background metrics collector."""

import json
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


async def test_interface_stats_exclude_loopback_and_virtual(monkeypatch):
    """Loopback and container bridges are dashboard noise; VPN tunnels stay."""
    from metrics_collector import _interface_stats

    class _Nic:
        def __init__(self, rx, tx):
            self.bytes_recv = rx
            self.bytes_sent = tx

    monkeypatch.setattr(
        "metrics_collector.HOST_PROC", Path("/nonexistent-host-proc")
    )
    monkeypatch.setattr(
        "psutil.net_io_counters",
        lambda pernic=False: {
            "lo": _Nic(1, 1),
            "eth0": _Nic(100, 200),
            "docker0": _Nic(5, 5),
            "br-f00d": _Nic(6, 6),
            "wg0": _Nic(7, 7),
        },
    )

    names = [s["name"] for s in _interface_stats()]

    assert "lo" not in names
    assert "docker0" not in names
    assert "br-f00d" not in names
    assert "eth0" in names
    assert "wg0" in names


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
