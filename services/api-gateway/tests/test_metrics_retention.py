"""Tests for metrics snapshot retention pruning."""

import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.models import Base, Instance, MetricSnapshot


pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_INSTANCE_KEY = "vw-test-" + uuid.uuid4().hex


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def instance():
    async with TestSessionLocal() as session:
        instance = Instance(
            name="retention-node",
            hostname="node1.example.local",
            api_endpoint="https://node1.example.local/api/v1",
            api_key=TEST_INSTANCE_KEY,
            status="active",
        )
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        yield instance


async def add_snapshot(instance_id: int, age_days: float) -> int:
    async with TestSessionLocal() as session:
        snapshot = MetricSnapshot(
            instance_id=instance_id,
            timestamp=datetime.utcnow() - timedelta(days=age_days),
            cpu_percent=10.0,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return snapshot.id


async def remaining_snapshot_ids() -> list:
    async with TestSessionLocal() as db:
        snapshots = (await db.scalars(select(MetricSnapshot))).all()
        return sorted(s.id for s in snapshots)


async def test_prunes_only_snapshots_older_than_retention(instance, monkeypatch):
    import metrics_retention

    monkeypatch.setattr(metrics_retention, "RETENTION_DAYS", 7)

    expired_id = await add_snapshot(instance.id, age_days=30)
    fresh_id = await add_snapshot(instance.id, age_days=1)

    async with TestSessionLocal() as db:
        pruned = await metrics_retention.prune_expired_snapshots(db)

    assert pruned == 1
    assert await remaining_snapshot_ids() == [fresh_id]
    assert expired_id not in await remaining_snapshot_ids()


async def test_pruning_disabled_with_zero_retention(instance, monkeypatch):
    import metrics_retention

    monkeypatch.setattr(metrics_retention, "RETENTION_DAYS", 0)

    old_id = await add_snapshot(instance.id, age_days=365)

    async with TestSessionLocal() as db:
        pruned = await metrics_retention.prune_expired_snapshots(db)

    assert pruned == 0
    assert await remaining_snapshot_ids() == [old_id]


async def test_pruning_respects_batch_limit(instance, monkeypatch):
    import metrics_retention

    monkeypatch.setattr(metrics_retention, "RETENTION_DAYS", 7)
    monkeypatch.setattr(metrics_retention, "PRUNE_BATCH_SIZE", 2)

    for _ in range(5):
        await add_snapshot(instance.id, age_days=30)

    async with TestSessionLocal() as db:
        pruned = await metrics_retention.prune_expired_snapshots(db)

    assert pruned == 2
    assert len(await remaining_snapshot_ids()) == 3
