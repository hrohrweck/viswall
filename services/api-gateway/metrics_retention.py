"""Retention pruning for metric snapshots.

The snapshot table grows by one row per instance per collection cycle
(default: 1,440 rows/instance/day), so expired history is trimmed each
collection cycle. The window is METRICS_RETENTION_DAYS (0 disables
pruning).
"""
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import MetricSnapshot

logger = logging.getLogger(__name__)

# Snapshots older than this many days are removed; 0 disables pruning.
RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))

# Upper bound on rows removed per cycle so one backlog cleanup cannot
# stall a collection cycle; the next cycle continues where this stopped.
PRUNE_BATCH_SIZE = 1000


async def prune_expired_snapshots(db: AsyncSession) -> int:
    """Remove snapshots older than the retention window.

    Uses the ORM scalar helpers and per-row removal, matching the safe
    query style used across the API. Returns the number of rows removed;
    0 when pruning is disabled.
    """
    if RETENTION_DAYS <= 0:
        return 0

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    expired = (
        await db.scalars(
            select(MetricSnapshot)
            .where(MetricSnapshot.timestamp < cutoff)
            .limit(PRUNE_BATCH_SIZE)
        )
    ).all()

    for snapshot in expired:
        await db.delete(snapshot)
    if expired:
        await db.commit()
        logger.info("Pruned %d expired metric snapshots", len(expired))

    return len(expired)
