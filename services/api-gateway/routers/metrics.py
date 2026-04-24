from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict, Any
from datetime import datetime, timedelta

from shared.database import get_db
from shared.models import (
    MetricSnapshot,
    FirewallRule,
    MailDomain,
    VPNServer,
    Instance,
)
from shared.schemas import (
    MetricSnapshotResponse,
    MetricsQuery,
    MetricsSummary,
)
from shared.security import require_auth

router = APIRouter()


@router.get("/latest/{instance_id}", response_model=MetricSnapshotResponse)
async def get_latest_metrics(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get latest metrics snapshot for an instance"""
    result = await db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.instance_id == instance_id)
        .order_by(MetricSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        # Return a placeholder snapshot if no metrics collected yet
        return MetricSnapshotResponse(
            id=0,
            instance_id=instance_id,
            timestamp=datetime.utcnow(),
        )

    return MetricSnapshotResponse.model_validate(snapshot)


@router.post("/query", response_model=List[MetricSnapshotResponse])
async def query_metrics(
    query: MetricsQuery,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Query historical metrics snapshots"""
    stmt = select(MetricSnapshot)

    if query.instance_ids:
        stmt = stmt.where(MetricSnapshot.instance_id.in_(query.instance_ids))

    if query.start_time:
        stmt = stmt.where(MetricSnapshot.timestamp >= query.start_time)

    if query.end_time:
        stmt = stmt.where(MetricSnapshot.timestamp <= query.end_time)

    stmt = stmt.order_by(MetricSnapshot.timestamp.desc())

    result = await db.execute(stmt)
    snapshots = result.scalars().all()

    return [MetricSnapshotResponse.model_validate(s) for s in snapshots]


@router.post("/summary", response_model=List[MetricsSummary])
async def get_metrics_summary(
    query: MetricsQuery,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated metrics summary per instance"""
    instance_ids = query.instance_ids or []

    if not instance_ids:
        # Get all instances if none specified
        result = await db.execute(select(Instance.id))
        instance_ids = [r[0] for r in result.all()]

    summaries = []
    for inst_id in instance_ids:
        stmt = select(MetricSnapshot).where(
            and_(
                MetricSnapshot.instance_id == inst_id,
                MetricSnapshot.timestamp >= query.start_time if query.start_time else True,
                MetricSnapshot.timestamp <= query.end_time if query.end_time else True,
            )
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        if not snapshots:
            summaries.append(
                MetricsSummary(
                    instance_id=inst_id,
                    cpu_avg=0.0,
                    cpu_max=0.0,
                    memory_avg=0.0,
                    memory_max=0.0,
                    disk_avg=0.0,
                    disk_max=0.0,
                    network_in_total=0,
                    network_out_total=0,
                    mail_total_inbound=0,
                    mail_total_outbound=0,
                    period_start=query.start_time or datetime.utcnow() - timedelta(days=1),
                    period_end=query.end_time or datetime.utcnow(),
                )
            )
            continue

        cpu_values = [s.cpu_percent for s in snapshots if s.cpu_percent is not None]
        memory_values = [s.memory_percent for s in snapshots if s.memory_percent is not None]
        disk_values = [s.disk_percent for s in snapshots if s.disk_percent is not None]

        network_in = sum(
            iface.get("rx_bytes", 0)
            for s in snapshots
            if s.interface_stats
            for iface in s.interface_stats
        )
        network_out = sum(
            iface.get("tx_bytes", 0)
            for s in snapshots
            if s.interface_stats
            for iface in s.interface_stats
        )

        mail_inbound = sum(
            s.mail_inbound_count or 0 for s in snapshots
        )
        mail_outbound = sum(
            s.mail_outbound_count or 0 for s in snapshots
        )

        summaries.append(
            MetricsSummary(
                instance_id=inst_id,
                cpu_avg=sum(cpu_values) / len(cpu_values) if cpu_values else 0.0,
                cpu_max=max(cpu_values) if cpu_values else 0.0,
                memory_avg=sum(memory_values) / len(memory_values) if memory_values else 0.0,
                memory_max=max(memory_values) if memory_values else 0.0,
                disk_avg=sum(disk_values) / len(disk_values) if disk_values else 0.0,
                disk_max=max(disk_values) if disk_values else 0.0,
                network_in_total=network_in,
                network_out_total=network_out,
                mail_total_inbound=mail_inbound,
                mail_total_outbound=mail_outbound,
                period_start=min(s.timestamp for s in snapshots),
                period_end=max(s.timestamp for s in snapshots),
            )
        )

    return summaries


@router.get("/dashboard/{instance_id}")
async def get_dashboard_data(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get all metrics needed for the dashboard"""
    # Get latest metric snapshot
    result = await db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.instance_id == instance_id)
        .order_by(MetricSnapshot.timestamp.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    # Get counts
    fw_result = await db.execute(
        select(func.count(FirewallRule.id)).where(
            FirewallRule.instance_id == instance_id
        )
    )
    firewall_rule_count = fw_result.scalar() or 0

    mail_result = await db.execute(
        select(func.count(MailDomain.id)).where(
            MailDomain.instance_id == instance_id
        )
    )
    mail_domain_count = mail_result.scalar() or 0

    vpn_result = await db.execute(
        select(func.count(VPNServer.id)).where(
            VPNServer.instance_id == instance_id
        )
    )
    vpn_server_count = vpn_result.scalar() or 0

    # Build system metrics
    system = {}
    if latest:
        system = {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_used_bytes": latest.memory_used_bytes,
            "memory_total_bytes": latest.memory_total_bytes,
            "disk_percent": latest.disk_percent,
            "disk_used_bytes": latest.disk_used_bytes,
            "disk_total_bytes": latest.disk_total_bytes,
        }

    # Build network metrics
    network = {}
    if latest and latest.interface_stats:
        network = {
            "interfaces": latest.interface_stats,
        }

    # Build mail metrics
    mail = {}
    if latest:
        mail = {
            "queue_size": latest.mail_queue_size,
            "inbound_count": latest.mail_inbound_count,
            "outbound_count": latest.mail_outbound_count,
            "spam_count": latest.mail_spam_count,
            "virus_count": latest.mail_virus_count,
        }

    return {
        "instance_id": instance_id,
        "firewall_rule_count": firewall_rule_count,
        "mail_domain_count": mail_domain_count,
        "vpn_server_count": vpn_server_count,
        "system": system,
        "network": network,
        "mail": mail,
    }


@router.get("/overview")
async def get_global_overview(
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get global overview counts for the main dashboard"""
    fw_result = await db.execute(select(func.count(FirewallRule.id)))
    firewall_rule_count = fw_result.scalar() or 0

    mail_result = await db.execute(select(func.count(MailDomain.id)))
    mail_domain_count = mail_result.scalar() or 0

    vpn_result = await db.execute(select(func.count(VPNServer.id)))
    vpn_server_count = vpn_result.scalar() or 0

    instance_result = await db.execute(select(func.count(Instance.id)))
    instance_count = instance_result.scalar() or 0

    active_instance_result = await db.execute(
        select(func.count(Instance.id)).where(Instance.status == "active")
    )
    active_instance_count = active_instance_result.scalar() or 0

    return {
        "instances": instance_count,
        "active_instances": active_instance_count,
        "firewall_rules": firewall_rule_count,
        "mail_domains": mail_domain_count,
        "vpn_servers": vpn_server_count,
    }
