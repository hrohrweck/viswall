"""Background metrics collector for viswall instances.

Runs periodically to collect system metrics from registered instances
and store them as MetricSnapshot rows in the database.

Until agents report real telemetry (via heartbeat/deploy), metrics are
simulated per instance. Collection is not restricted to instances with
status "active": instances are created as "inactive" and only flip to
"active" once an agent heartbeat arrives, which would otherwise leave
the dashboards empty forever.

A short Redis lock prevents duplicate collection when the API runs with
multiple gunicorn workers, each running its own collector loop.
"""
import asyncio
import random
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Instance, MetricSnapshot

logger = logging.getLogger(__name__)

# Configurable via environment variables
COLLECTION_INTERVAL_SECONDS = int(os.getenv("METRICS_INTERVAL", "60"))
METRICS_ENABLED = os.getenv("METRICS_COLLECTOR_ENABLED", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def collect_instance_metrics(instance_id: int) -> dict:
    """Collect metrics for a single instance.

    In a real deployment this would query the instance agent via HTTP/gRPC.
    For now, we simulate realistic metrics with random variation.
    """
    # Simulate realistic CPU usage (5-85%)
    cpu_percent = random.uniform(5.0, 85.0)

    # Simulate memory usage (30-90% of 8GB)
    memory_total_bytes = 8 * 1024 * 1024 * 1024  # 8 GB
    memory_percent = random.uniform(30.0, 90.0)
    memory_used_bytes = int(memory_total_bytes * (memory_percent / 100))

    # Simulate disk usage (20-80% of 100GB)
    disk_total_bytes = 100 * 1024 * 1024 * 1024  # 100 GB
    disk_percent = random.uniform(20.0, 80.0)
    disk_used_bytes = int(disk_total_bytes * (disk_percent / 100))

    # Simulate network interfaces
    interface_stats = [
        {
            "name": "eth0",
            "rx_bytes": random.randint(1_000_000_000, 50_000_000_000),
            "tx_bytes": random.randint(500_000_000, 20_000_000_000),
        },
        {
            "name": "eth1",
            "rx_bytes": random.randint(100_000_000, 5_000_000_000),
            "tx_bytes": random.randint(50_000_000, 2_000_000_000),
        },
    ]

    # Simulate mail metrics (if mail service active)
    mail_queue_size = random.randint(0, 50)
    mail_inbound_count = random.randint(0, 500)
    mail_outbound_count = random.randint(0, 300)
    mail_spam_count = random.randint(0, 50)
    mail_virus_count = random.randint(0, 5)

    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
        "memory_used_bytes": memory_used_bytes,
        "memory_total_bytes": memory_total_bytes,
        "disk_percent": round(disk_percent, 2),
        "disk_used_bytes": disk_used_bytes,
        "disk_total_bytes": disk_total_bytes,
        "interface_stats": interface_stats,
        "mail_queue_size": mail_queue_size,
        "mail_inbound_count": mail_inbound_count,
        "mail_outbound_count": mail_outbound_count,
        "mail_spam_count": mail_spam_count,
        "mail_virus_count": mail_virus_count,
    }


async def run_metrics_collection_cycle(db: AsyncSession) -> int:
    """Run one collection cycle. Returns number of snapshots inserted."""
    result = await db.execute(select(Instance))
    instances = result.scalars().all()

    inserted = 0
    for instance in instances:
        try:
            metrics_data = await collect_instance_metrics(instance.id)

            snapshot = MetricSnapshot(
                instance_id=instance.id,
                timestamp=datetime.utcnow(),
                **metrics_data,
            )
            db.add(snapshot)
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to collect metrics for instance {instance.id}: {e}")

    if inserted > 0:
        await db.commit()
        logger.info(f"Inserted {inserted} metric snapshots")

    return inserted


async def _try_acquire_cycle_lock() -> bool:
    """Try to claim this collection cycle via a short-lived Redis lock.

    Multiple gunicorn workers each run their own collector loop; only the
    worker that wins the lock should insert snapshots for this interval.
    If Redis is unreachable we collect anyway — duplicate snapshots are
    preferable to none.
    """
    try:
        from redis.asyncio import Redis

        redis = Redis.from_url(REDIS_URL, decode_responses=True)
        try:
            acquired = await redis.set(
                "viswall:metrics:collector_lock",
                "1",
                nx=True,
                ex=max(COLLECTION_INTERVAL_SECONDS - 5, 10),
            )
            return bool(acquired)
        finally:
            await redis.aclose()
    except Exception as e:
        logger.warning(f"Metrics dedup lock unavailable, collecting without it: {e}")
        return True


async def metrics_collector_loop():
    """Background loop that periodically collects metrics."""
    if not METRICS_ENABLED:
        logger.info("Metrics collector is disabled")
        return

    logger.info(
        f"Metrics collector started (interval={COLLECTION_INTERVAL_SECONDS}s)"
    )

    while True:
        try:
            if await _try_acquire_cycle_lock():
                # Import lazily: shared.database initialises the session
                # factory on first use (after init_db), so a module-level
                # import would bind None and break every cycle.
                from shared.database import AsyncSessionLocal

                async with AsyncSessionLocal() as db:
                    await run_metrics_collection_cycle(db)
        except Exception as e:
            logger.error(f"Metrics collection cycle failed: {e}")

        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)


def start_metrics_collector() -> Optional[asyncio.Task]:
    """Start the background metrics collector task.

    Returns the asyncio.Task so it can be cancelled on shutdown.
    """
    if not METRICS_ENABLED:
        return None

    return asyncio.create_task(metrics_collector_loop())
