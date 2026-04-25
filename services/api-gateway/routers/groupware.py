from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any

from shared.database import get_db
from shared.models import MailDomain
from shared.schemas import MailDomainResponse
from shared.security import require_auth, require_admin
from shared.audit_logger import log_audit

router = APIRouter()


@router.get("/status/{domain_id}")
async def get_groupware_status(
    domain_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get groupware status for a mail domain"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    return {
        "domain_id": domain_id,
        "domain": domain.domain,
        "groupware_enabled": domain.groupware_enabled,
        "sogo_url": "/sogo" if domain.groupware_enabled else None,
    }


@router.post("/enable/{domain_id}", response_model=MailDomainResponse)
async def enable_groupware(
    domain_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable groupware (SOGo) for a mail domain"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain.groupware_enabled = True
    await db.commit()
    await db.refresh(domain)

    await log_audit(
        db=db,
        user_id=admin_id,
        action="enable_groupware",
        resource_type="mail_domain",
        resource_id=domain_id,
        instance_id=domain.instance_id,
    )

    return MailDomainResponse.model_validate(domain)


@router.post("/disable/{domain_id}", response_model=MailDomainResponse)
async def disable_groupware(
    domain_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Disable groupware (SOGo) for a mail domain"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain.groupware_enabled = False
    await db.commit()
    await db.refresh(domain)

    await log_audit(
        db=db,
        user_id=admin_id,
        action="disable_groupware",
        resource_type="mail_domain",
        resource_id=domain_id,
        instance_id=domain.instance_id,
    )

    return MailDomainResponse.model_validate(domain)


@router.get("/stats/{domain_id}")
async def get_groupware_stats(
    domain_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get groupware usage statistics for a domain

    Note: In a full implementation, this would query SOGo's database tables.
    For now, returns basic domain status.
    """
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if not domain.groupware_enabled:
        return {
            "domain_id": domain_id,
            "groupware_enabled": False,
            "message": "Groupware is not enabled for this domain",
        }

    # In a production implementation, query SOGo's sogo_user_profile,
    # sogo_folder_info tables to get actual stats
    return {
        "domain_id": domain_id,
        "domain": domain.domain,
        "groupware_enabled": True,
        "sogo_url": "/sogo",
        "calendars": 0,  # Would query sogo_folder_info
        "contacts": 0,   # Would query sogo_folder_info
        "active_users": 0,  # Would query sogo_user_profile
    }
