from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from shared.database import get_db
from shared.models import MailDomain, MailUser, Instance, User
from shared.schemas import (
    MailDomainCreate, MailDomainUpdate, MailDomainResponse,
    MailUserCreate, MailUserUpdate, MailUserResponse,
    LLMConfig
)
from shared.security import require_auth, require_admin, get_password_hash
from shared.audit_logger import log_audit

router = APIRouter()

# ============================================================================
# MAIL DOMAIN ENDPOINTS
# ============================================================================

@router.get("/domains/{instance_id}", response_model=List[MailDomainResponse])
async def get_domains(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get all mail domains for an instance"""
    # Verify user has access to this instance
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(status_code=403, detail="Access denied to this instance")
    
    result = await db.execute(
        select(MailDomain).where(MailDomain.instance_id == instance_id)
    )
    domains = result.scalars().all()
    return [MailDomainResponse.model_validate(d) for d in domains]

@router.post("/domains/{instance_id}", response_model=MailDomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    instance_id: int,
    data: MailDomainCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mail domain with optional DKIM generation"""
    
    # Verify instance exists
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Check for duplicate domain
    result = await db.execute(
        select(MailDomain).where(
            and_(
                MailDomain.instance_id == instance_id,
                MailDomain.domain == data.domain
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already exists on this instance")
    
    domain = MailDomain(
        instance_id=instance_id,
        domain=data.domain,
        enabled=data.enabled,
        spam_filter_enabled=data.spam_filter_enabled,
        virus_scan_enabled=data.virus_scan_enabled,
        dkim_enabled=data.dkim_enabled,
        dmarc_enabled=data.dmarc_enabled,
        spf_enabled=data.spf_enabled,
        llm_enabled=data.llm_enabled,
        llm_config=data.llm_config or {}
    )
    
    db.add(domain)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="create", resource_type="mail_domain", resource_id=domain.id, instance_id=instance_id)

    await db.refresh(domain)
    
    # Trigger DKIM generation if enabled
    if data.dkim_enabled:
        background_tasks.add_task(generate_dkim_keys, domain.id, data.domain)
    
    # Trigger Exim config reload on instance
    background_tasks.add_task(reload_mail_config, instance_id)
    
    return MailDomainResponse.model_validate(domain)

@router.get("/domains/detail/{domain_id}", response_model=MailDomainResponse)
async def get_domain(
    domain_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get mail domain details"""
    result = await db.execute(
        select(MailDomain, MailDomain.instance_id).where(MailDomain.id == domain_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    domain, instance_id = row
    
    # Verify access
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return MailDomainResponse.model_validate(domain)

@router.patch("/domains/{domain_id}", response_model=MailDomainResponse)
async def update_domain(
    domain_id: int,
    data: MailDomainUpdate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update mail domain settings"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle LLM config specially
    if "llm_config" in update_data:
        domain.llm_config.update(update_data.pop("llm_config"))
    
    for field, value in update_data.items():
        setattr(domain, field, value)
    
    domain.updated_at = datetime.utcnow()
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="update", resource_type="mail_domain", resource_id=domain_id, instance_id=instance_id)

    await db.refresh(domain)
    
    # Reload mail config
    background_tasks.add_task(reload_mail_config, domain.instance_id)
    
    return MailDomainResponse.model_validate(domain)

@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a mail domain and all its users"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    instance_id = domain.instance_id
    
    await db.delete(domain)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="delete", resource_type="mail_domain", resource_id=domain_id, instance_id=instance_id)

    
    # Reload mail config
    background_tasks.add_task(reload_mail_config, instance_id)
    
    return None

@router.post("/domains/{domain_id}/dkim/regenerate")
async def regenerate_dkim(
    domain_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate DKIM keys for a domain"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not domain.dkim_enabled:
        raise HTTPException(status_code=400, detail="DKIM is not enabled for this domain")
    
    background_tasks.add_task(generate_dkim_keys, domain_id, domain.domain)
    
    return {"status": "queued", "message": "DKIM key generation started"}

@router.get("/domains/{domain_id}/dns-records")
async def get_dns_records(
    domain_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get DNS records needed for mail domain (SPF, DKIM, DMARC)"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    records = {
        "mx": {
            "type": "MX",
            "name": domain.domain,
            "value": f"10 mail.{domain.domain}.",
            "priority": 10
        },
        "spf": None,
        "dkim": None,
        "dmarc": None
    }
    
    if domain.spf_enabled:
        records["spf"] = {
            "type": "TXT",
            "name": domain.domain,
            "value": f'"v=spf1 mx a:mail.{domain.domain} ~all"'
        }
    
    if domain.dkim_enabled:
        # In real implementation, fetch actual DKIM public key
        records["dkim"] = {
            "type": "TXT",
            "name": f"default._domainkey.{domain.domain}",
            "value": "[DKIM key - generate to see actual value]",
            "note": "Use POST /dkim/regenerate to create keys"
        }
    
    if domain.dmarc_enabled:
        records["dmarc"] = {
            "type": "TXT",
            "name": f"_dmarc.{domain.domain}",
            "value": f'"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain.domain}"'
        }
    
    return records

# ============================================================================
# MAIL USER ENDPOINTS
# ============================================================================

@router.get("/users/{domain_id}", response_model=List[MailUserResponse])
async def get_users(
    domain_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get all mail users for a domain"""
    # Verify domain access
    result = await db.execute(
        select(MailDomain.instance_id).where(MailDomain.id == domain_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    instance_id = row[0]
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(MailUser).where(MailUser.domain_id == domain_id)
    )
    users = result.scalars().all()
    return [MailUserResponse.model_validate(u) for u in users]

@router.post("/users/{domain_id}", response_model=MailUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    domain_id: int,
    data: MailUserCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mail user"""
    # Verify domain exists
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Check for duplicate username
    result = await db.execute(
        select(MailUser).where(
            and_(
                MailUser.domain_id == domain_id,
                MailUser.username == data.username
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"User {data.username} already exists in this domain"
        )
    
    # Hash password if provided
    password_hash = None
    if data.password:
        password_hash = get_password_hash(data.password)
    
    user = MailUser(
        domain_id=domain_id,
        username=data.username,
        password_hash=password_hash,
        full_name=data.full_name,
        quota_bytes=data.quota_bytes,
        enabled=data.enabled,
        forward_to=data.forward_to,
        vacation_enabled=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create maildir
    background_tasks.add_task(create_maildir, domain.domain, data.username)
    
    return MailUserResponse.model_validate(user)

@router.get("/users/detail/{user_id}", response_model=MailUserResponse)
async def get_user(
    user_id: int,
    auth_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get mail user details"""
    result = await db.execute(
        select(MailUser, MailDomain.instance_id)
        .join(MailDomain)
        .where(MailUser.id == user_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    user, instance_id = row
    
    # Verify access
    result = await db.execute(select(User).where(User.id == auth_id))
    auth_user = result.scalar_one()
    if auth_user.role != "superadmin" and instance_id not in (auth_user.instances or []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return MailUserResponse.model_validate(user)

@router.patch("/users/{user_id}", response_model=MailUserResponse)
async def update_user(
    user_id: int,
    data: MailUserUpdate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update mail user settings"""
    result = await db.execute(
        select(MailUser).where(MailUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle password specially
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            user.password_hash = get_password_hash(password)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return MailUserResponse.model_validate(user)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a mail user"""
    result = await db.execute(
        select(MailUser).where(MailUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return None

# ============================================================================
# MAIL QUEUE AND STATUS ENDPOINTS
# ============================================================================

@router.get("/queue/{instance_id}")
async def get_mail_queue(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get current mail queue status for an instance"""
    # This would fetch from the mail service agent
    return {
        "instance_id": instance_id,
        "queue_size": 0,
        "deferred": 0,
        "frozen": 0,
        "recent_activity": []
    }

@router.post("/queue/{instance_id}/flush")
async def flush_mail_queue(
    instance_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Force immediate delivery attempt for queued messages"""
    return {"status": "queued", "action": "flush_queue"}

@router.get("/stats/{instance_id}")
async def get_mail_stats(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive mail statistics"""
    return {
        "instance_id": instance_id,
        "domains": 0,
        "users": 0,
        "messages_today": 0,
        "spam_blocked": 0,
        "viruses_blocked": 0,
        "queue_size": 0,
        "storage_used": 0
    }

# ============================================================================
# LLM CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/domains/{domain_id}/llm/test")
async def test_llm_classification(
    domain_id: int,
    test_email: dict,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Test LLM classification on sample email"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not domain.llm_enabled or not domain.llm_config:
        raise HTTPException(status_code=400, detail="LLM not configured for this domain")
    
    # In real implementation, call LLM service
    return {
        "classified": True,
        "category": "test",
        "confidence": 0.95,
        "action": "deliver",
        "reason": "LLM classification test"
    }

# ============================================================================
# BACKGROUND TASKS (These would be actual async tasks in production)
# ============================================================================

async def generate_dkim_keys(domain_id: int, domain_name: str):
    """Generate DKIM keys for a domain"""
    # Would call mail agent to generate keys
    pass

async def reload_mail_config(instance_id: int):
    """Reload Exim configuration on an instance"""
    # Would notify mail agent to reload
    pass

async def create_maildir(domain: str, username: str):
    """Create Maildir for a new user"""
    # Would call mail agent to create directories
    pass
