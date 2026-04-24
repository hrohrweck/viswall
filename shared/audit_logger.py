"""Helper for creating audit log entries."""
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    instance_id: Optional[int] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry.

    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: One of: create, update, delete, login, logout, deploy
        resource_type: e.g. firewall_rule, instance, user, mail_domain, vpn_server
        resource_id: Optional string identifier for the resource
        instance_id: Optional instance ID if action relates to an instance
        old_value: Previous state (for updates/deletes)
        new_value: New state (for creates/updates)
        ip_address: Client IP address
    """
    log = AuditLog(
        user_id=user_id,
        instance_id=instance_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
