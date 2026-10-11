"""Tests for the background metrics collector."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.models import Base, Instance, MetricSnapshot


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


async def test_collects_for_instances_that_are_not_active(inactive_instance):
    """Instances stay 'inactive' until an agent heartbeat arrives — the
    collector must still produce snapshots for them (simulated metrics)."""
    from metrics_collector import run_metrics_collection_cycle

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
