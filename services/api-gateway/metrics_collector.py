"""Background metrics collector for viswall instances.

Runs periodically to collect system metrics from registered instances
and store them as MetricSnapshot rows in the database.

System and network metrics are read from the local host via psutil. The
api-gateway shares the host kernel, so CPU and memory reflect the whole
appliance; with the host /proc bind-mounted read-only at /host/proc
(see docker-compose.yml) the appliance's real network interfaces are
reported instead of the container's virtual eth0.

Mail metrics still have no collection source (the mail agent does not
report telemetry yet), so they remain simulated until then.

Collection is not restricted to instances with status "active":
instances are created as "inactive" and only flip to "active" once an
agent heartbeat arrives, which would otherwise leave the dashboards
empty forever.

A short Redis lock prevents duplicate collection when the API runs with
multiple gunicorn workers, each running its own collector loop.
"""
import asyncio
import random
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Instance, MetricSnapshot

logger = logging.getLogger(__name__)

# Configurable via environment variables
COLLECTION_INTERVAL_SECONDS = int(os.getenv("METRICS_INTERVAL", "60"))
METRICS_ENABLED = os.getenv("METRICS_COLLECTOR_ENABLED", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Host /proc bind mount (docker-compose.yml mounts /proc here read-only)
HOST_PROC = Path(os.getenv("HOST_PROC", "/host/proc"))

# Container/virtual interfaces that are noise on the appliance dashboards
# (VPN tun/tap/wg interfaces are deliberately NOT filtered — they are real)
_VIRTUAL_IFACE_PREFIXES = ("veth", "br-", "docker", "virbr", "lxcbr", "podman", "cni")


def _is_reported_interface(name: str) -> bool:
    return name != "lo" and not name.startswith(_VIRTUAL_IFACE_PREFIXES)


def _parse_proc_net_dev(path: Path) -> list:
    """Parse /proc/net/dev into per-interface byte counters (host netns)."""
    stats = []
    for line in path.read_text().splitlines()[2:]:  # first two lines are headers
        if ":" not in line:
            continue
        name, raw = line.split(":", 1)
        fields = raw.split()
        if len(fields) < 9:
            continue
        stats.append(
            {
                "name": name.strip(),
                "rx_bytes": int(fields[0]),
                "tx_bytes": int(fields[8]),
            }
        )
    return stats


def _interface_stats() -> list:
    """Byte counters per interface, preferring the host network namespace.

    Inside a container psutil only sees the container's virtual
    interfaces, so the host /proc bind mount is read when present.
    """
    try:
        proc_net_dev = HOST_PROC / "net" / "dev"
        if proc_net_dev.exists():
            stats = _parse_proc_net_dev(proc_net_dev)
        else:
            counters = psutil.net_io_counters(pernic=True)
            stats = [
                {"name": name, "rx_bytes": nic.bytes_recv, "tx_bytes": nic.bytes_sent}
                for name, nic in counters.items()
            ]
        return [s for s in stats if _is_reported_interface(s["name"])]
    except Exception as e:
        logger.warning("Failed to read interface stats: %s", e)
        return []


def _system_stats() -> dict:
    """CPU, memory and disk usage of the appliance (host) as seen via /proc."""
    mem = psutil.virtual_memory()

    # /app/shared is a bind-mount from the host filesystem in the compose
    # deployment, so statfs-ing it reports the appliance's real disk
    # rather than the container's overlay layer.
    disk = None
    for path in ("/app/shared", "/"):
        try:
            disk = psutil.disk_usage(path)
            break
        except OSError:
            continue

    return {
        "cpu_percent": round(psutil.cpu_percent(interval=None), 2),
        "memory_percent": round(mem.percent, 2),
        "memory_used_bytes": mem.used,
        "memory_total_bytes": mem.total,
        "disk_percent": round(disk.percent, 2) if disk else None,
        "disk_used_bytes": disk.used if disk else None,
        "disk_total_bytes": disk.total if disk else None,
    }


def _simulated_mail_stats() -> dict:
    # No mail agent telemetry yet — keep dashboard charts populated with
    # simulated values until the mail service reports real counts.
    return {
        "mail_queue_size": random.randint(0, 50),
        "mail_inbound_count": random.randint(0, 500),
        "mail_outbound_count": random.randint(0, 300),
        "mail_spam_count": random.randint(0, 50),
        "mail_virus_count": random.randint(0, 5),
    }


async def collect_instance_metrics(instance_id: int) -> dict:
    """Collect metrics for a single instance.

    Returns the metric fields for one MetricSnapshot row.
    """
    metrics = _system_stats()
    metrics["interface_stats"] = _interface_stats()
    metrics.update(_simulated_mail_stats())
    return metrics


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
            logger.warning(
                "Failed to collect metrics for instance %s: %s", instance.id, e
            )

    if inserted > 0:
        await db.commit()
        logger.info("Inserted %d metric snapshots", inserted)

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
        logger.warning("Metrics dedup lock unavailable, collecting without it: %s", e)
        return True


async def metrics_collector_loop():
    """Background loop that periodically collects metrics."""
    if not METRICS_ENABLED:
        logger.info("Metrics collector is disabled")
        return

    logger.info(
        "Metrics collector started (interval=%ds)", COLLECTION_INTERVAL_SECONDS
    )

    # The first psutil.cpu_percent(interval=None) call has no previous
    # sample to diff against and would report 0.0 — prime it so the first
    # cycle already reads a real usage delta.
    psutil.cpu_percent(interval=None)

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
            logger.error("Metrics collection cycle failed: %s", e)

        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)


def start_metrics_collector() -> Optional[asyncio.Task]:
    """Start the background metrics collector task.

    Returns the asyncio.Task so it can be cancelled on shutdown.
    """
    if not METRICS_ENABLED:
        return None

    return asyncio.create_task(metrics_collector_loop())
