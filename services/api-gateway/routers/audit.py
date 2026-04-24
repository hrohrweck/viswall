from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from typing import List, Optional
from datetime import datetime

from shared.database import get_db
from shared.models import AuditLog
from shared.schemas import AuditLogResponse
from shared.security import require_auth, require_admin

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id_filter: Optional[int] = None,
    instance_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with filtering (admin only)"""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp))

    if user_id_filter:
        stmt = stmt.where(AuditLog.user_id == user_id_filter)

    if instance_id:
        stmt = stmt.where(AuditLog.instance_id == instance_id)

    if action:
        stmt = stmt.where(AuditLog.action == action)

    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)

    if start_time:
        stmt = stmt.where(AuditLog.timestamp >= start_time)

    if end_time:
        stmt = stmt.where(AuditLog.timestamp <= end_time)

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/instance/{instance_id}", response_model=List[AuditLogResponse])
async def get_instance_logs(
    instance_id: int,
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs for a specific instance"""
    stmt = select(AuditLog).where(
        AuditLog.instance_id == instance_id
    ).order_by(desc(AuditLog.timestamp))

    if action:
        stmt = stmt.where(AuditLog.action == action)

    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    if start_time:
        stmt = stmt.where(AuditLog.timestamp >= start_time)

    if end_time:
        stmt = stmt.where(AuditLog.timestamp <= end_time)

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditLogResponse])
async def get_resource_logs(
    resource_type: str,
    resource_id: str,
    limit: int = 100,
    offset: int = 0,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs for a specific resource"""
    stmt = (
        select(AuditLog)
        .where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id,
            )
        )
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/summary")
async def get_audit_summary(
    days: int = 7,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log summary statistics"""
    from sqlalchemy import func

    start = datetime.utcnow() - __import__('datetime').timedelta(days=days)

    # Total actions
    total_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.timestamp >= start)
    )
    total = total_result.scalar() or 0

    # Actions by type
    action_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= start)
        .group_by(AuditLog.action)
    )
    actions_by_type = {row[0]: row[1] for row in action_result.all()}

    # Resources by type
    resource_result = await db.execute(
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= start)
        .group_by(AuditLog.resource_type)
    )
    resources_by_type = {row[0]: row[1] for row in resource_result.all()}

    return {
        "period_days": days,
        "total_logs": total,
        "actions_by_type": actions_by_type,
        "resources_by_type": resources_by_type,
    }
