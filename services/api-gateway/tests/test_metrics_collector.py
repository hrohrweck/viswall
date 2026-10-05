"""Tests for the background metrics collector."""

from datetime import datetime, timedelta
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
            api_key="vis_testkey",
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
    assert snapshots[0].cpu_percent is not None
    assert snapshots[0].timestamp <= datetime.utcnow() + timedelta(seconds=5)


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
