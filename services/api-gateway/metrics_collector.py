"""Background metrics collector for viswall instances.

Runs periodically to collect system metrics from registered instances
and store them as MetricSnapshot rows in the database.

System and network metrics are read from the local host via psutil. The
api-gateway shares the host kernel, so CPU and memory reflect the whole
appliance; with the host /proc bind-mounted read-only at /host/proc
(see docker-compose.yml) the appliance's real network interfaces are
reported instead of the container's virtual eth0.

Mail metrics come from the instance's mail agent (/stats endpoint), which
reports cumulative counters derived from the Exim mainlog. Per-interval
deltas are computed against the previous cumulative, persisted in Redis so
they survive gunicorn worker handoffs and gateway restarts. The first
observation stores only a baseline (queue size); if the mail agent is
unreachable the mail fields stay NULL and system metrics are unaffected.

Each cycle also prunes snapshots older than METRICS_RETENTION_DAYS so
the table does not grow unbounded (0 disables pruning).

Collection is not restricted to instances with status "active":
instances are created as "inactive" and only flip to "active" once an
agent heartbeat arrives, which would otherwise leave the dashboards
empty forever.

A short Redis lock prevents duplicate collection when the API runs with
multiple gunicorn workers, each running its own collector loop.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from metrics_retention import prune_expired_snapshots
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


async def _mail_stats(db: AsyncSession, instance: Instance) -> dict | None:
    """Fetch cumulative mail counters from the instance's mail agent.

    Returns {"queue_length": int, "received": int, "delivered": int,
    "rejected_spam": int, "rejected_virus": int} or None if unavailable.
    NOTE: received/delivered count all arrivals/deliveries, not a true
    inbound/outbound split (see the agent-side docstring note).
    """
    from utils.agent_client import get_instance_endpoint
    import httpx
    try:
        # Pass the AsyncSession through explicitly — do NOT use
        # instance._sa_instance_state.session: on SQLAlchemy 2.0 async that
        # attribute is the SYNC Session, and awaiting its .execute() raises
        # TypeError (silently swallowed below → mail stats never collected).
        endpoint = await get_instance_endpoint(db, instance.id, service="mail")
    except Exception:
        return None
    if not endpoint:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{endpoint}/stats")
            resp.raise_for_status()
            data = resp.json()
            mail = data.get("mail")
            if not mail:
                return None
            return {"queue_length": data.get("queue_length"), **mail}
    except Exception:
        return None


async def collect_instance_metrics(db: AsyncSession, instance: Instance) -> dict:
    """Collect metrics for a single instance.

    Returns the metric fields for one MetricSnapshot row. Mail fields are
    included when the instance's mail agent reports cumulative counters:
    inbound/outbound/spam/virus are per-interval deltas against the previous
    cumulative (persisted in Redis); without a previous observation only the
    queue size is stored and the delta fields stay NULL.
    """
    metrics = _system_stats()
    metrics["interface_stats"] = _interface_stats()
    mail_raw = await _mail_stats(db, instance)
    mail_fields = {}
    if mail_raw:
        prev = await _mail_prev_from_redis(instance.id)
        if prev:
            mail_fields = {
                "mail_queue_size": mail_raw.get("queue_length"),
                "mail_inbound_count": max(0, mail_raw["received"] - prev["received"]),
                "mail_outbound_count": max(0, mail_raw["delivered"] - prev["delivered"]),
                "mail_spam_count": max(0, mail_raw["rejected_spam"] - prev["rejected_spam"]),
                "mail_virus_count": max(0, mail_raw["rejected_virus"] - prev["rejected_virus"]),
            }
        else:
            # First observation: store baseline (queue only), delta = NULL
            mail_fields = {"mail_queue_size": mail_raw.get("queue_length")}
        await _store_mail_cum(instance.id, mail_raw)
    metrics.update(mail_fields)
    return metrics


async def _mail_prev_from_redis(instance_id: int) -> dict | None:
    """Last cumulative counters, or None. Redis failure → None (baseline mode:
    deltas NULL for one interval — same graceful philosophy as the lock)."""
    try:
        from redis.asyncio import Redis
        redis = Redis.from_url(REDIS_URL, decode_responses=True)
        try:
            raw = await redis.get(f"viswall:metrics:mail_cum:{instance_id}")
            return json.loads(raw) if raw else None
        finally:
            await redis.aclose()
    except Exception:
        return None


async def _store_mail_cum(instance_id: int, cum: dict) -> None:
    try:
        from redis.asyncio import Redis
        redis = Redis.from_url(REDIS_URL, decode_responses=True)
        try:
            await redis.set(f"viswall:metrics:mail_cum:{instance_id}", json.dumps(cum))
        finally:
            await redis.aclose()
    except Exception:
        pass  # next cycle re-stores; worst case deltas stay NULL one interval


async def run_metrics_collection_cycle(db: AsyncSession) -> int:
    """Run one collection cycle. Returns number of snapshots inserted."""
    result = await db.execute(select(Instance))
    instances = result.scalars().all()

    inserted = 0
    for instance in instances:
        try:
            metrics_data = await collect_instance_metrics(db, instance)

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
                    await prune_expired_snapshots(db)
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
