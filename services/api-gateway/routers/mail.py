from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from shared.database import get_db
from shared.models import MailDomain, MailUser, Instance, User, MailMessage
from shared.schemas import (
    MailDomainCreate, MailDomainUpdate, MailDomainResponse,
    MailUserCreate, MailUserUpdate, MailUserResponse,
    MailMessageCreate, MailMessageResponse, MailClassificationResult,
    MailMessageListParams, MailMessageActionRequest,
    LLMConfig
)
from shared.security import require_auth, require_admin, get_password_hash
from shared.audit_logger import log_audit
from mail_classifier import (
    classify_email,
    LLMClassificationError,
    DEFAULT_CATEGORIES,
)

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
    
    # Inject default categories if LLM is enabled but no categories provided
    llm_config = data.llm_config or {}
    if data.llm_enabled and not llm_config.get("categories"):
        llm_config["categories"] = DEFAULT_CATEGORIES

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
        llm_config=llm_config
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

@router.post("/domains/{domain_id}/classify")
async def test_classify_email(
    domain_id: int,
    test_data: dict,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test LLM classification on a sample email"""
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if not domain.llm_enabled:
        raise HTTPException(status_code=400, detail="LLM not enabled for this domain")

    try:
        classification = await classify_email(
            db=db,
            subject=test_data.get("subject", "Test email"),
            sender=test_data.get("sender", "test@example.com"),
            body_preview=test_data.get("body_preview"),
        )
        return classification
    except LLMClassificationError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/classify-inbound")
async def classify_inbound_email(
    data: MailMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint for mail agent to classify incoming email"""
    # Verify domain exists and LLM is enabled
    result = await db.execute(
        select(MailDomain).where(MailDomain.id == data.domain_id)
    )
    domain = result.scalar_one_or_none()

    if not domain or not domain.llm_enabled:
        # Store message without classification
        message = MailMessage(
            domain_id=data.domain_id,
            message_id=data.message_id,
            sender=data.sender,
            recipients=data.recipients,
            subject=data.subject,
            size_bytes=data.size_bytes,
            body_preview=data.body_preview,
            status="pending",
        )
        db.add(message)
        await db.commit()
        return {"classified": False, "reason": "LLM not enabled"}

    try:
        classification = await classify_email(
            db=db,
            subject=data.subject or "",
            sender=data.sender,
            body_preview=data.body_preview,
        )
    except LLMClassificationError as e:
        # Store message with classification error
        message = MailMessage(
            domain_id=data.domain_id,
            message_id=data.message_id,
            sender=data.sender,
            recipients=data.recipients,
            subject=data.subject,
            size_bytes=data.size_bytes,
            body_preview=data.body_preview,
            status="pending",
        )
        db.add(message)
        await db.commit()
        return {"classified": False, "reason": str(e)}

    # Store classified message
    message = MailMessage(
        domain_id=data.domain_id,
        message_id=data.message_id,
        sender=data.sender,
        recipients=data.recipients,
        subject=data.subject,
        size_bytes=data.size_bytes,
        body_preview=data.body_preview,
        llm_category=classification["category"],
        llm_confidence=classification["confidence"],
        llm_reason=classification["reason"],
        llm_provider=classification["provider"],
        llm_model=classification["model"],
        classified_at=datetime.utcnow(),
        action_taken=classification["default_action"],
        status="classified",
    )
    db.add(message)
    await db.commit()

    return {
        "classified": True,
        "category": classification["category"],
        "confidence": classification["confidence"],
        "action": classification["default_action"],
        "reason": classification["reason"],
    }


@router.get("/messages/{domain_id}", response_model=List[MailMessageResponse])
async def list_mail_messages(
    domain_id: int,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List classified emails for a domain with optional filters"""
    # Verify access
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

    # Build query
    query = select(MailMessage).where(MailMessage.domain_id == domain_id)

    if category:
        query = query.where(MailMessage.llm_category == category)
    if status:
        query = query.where(MailMessage.status == status)

    query = query.order_by(MailMessage.received_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    messages = result.scalars().all()
    return [MailMessageResponse.model_validate(m) for m in messages]


@router.get("/messages/detail/{message_id}", response_model=MailMessageResponse)
async def get_mail_message(
    message_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a classified email"""
    result = await db.execute(
        select(MailMessage, MailDomain.instance_id)
        .join(MailDomain)
        .where(MailMessage.id == message_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    message, instance_id = row

    # Verify access
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(status_code=403, detail="Access denied")

    return MailMessageResponse.model_validate(message)


@router.post("/messages/{message_id}/reclassify")
async def reclassify_message(
    message_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retry LLM classification for an existing message"""
    result = await db.execute(
        select(MailMessage, MailDomain)
        .join(MailDomain)
        .where(MailMessage.id == message_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    message, domain = row

    if not domain.llm_enabled:
        raise HTTPException(status_code=400, detail="LLM not enabled for this domain")

    try:
        classification = await classify_email(
            db=db,
            subject=message.subject or "",
            sender=message.sender,
            body_preview=message.body_preview,
        )
    except LLMClassificationError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Update message
    message.llm_category = classification["category"]
    message.llm_confidence = classification["confidence"]
    message.llm_reason = classification["reason"]
    message.llm_provider = classification["provider"]
    message.llm_model = classification["model"]
    message.classified_at = datetime.utcnow()
    message.action_taken = classification["default_action"]
    message.status = "classified"

    await db.commit()
    await db.refresh(message)

    return MailMessageResponse.model_validate(message)


@router.post("/messages/{message_id}/action")
async def message_action(
    message_id: int,
    action_data: MailMessageActionRequest,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Take admin action on a classified message (deliver, quarantine, reject)"""
    result = await db.execute(
        select(MailMessage).where(MailMessage.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.action_taken = action_data.action
    message.action_reason = action_data.reason
    message.action_taken_at = datetime.utcnow()
    message.action_taken_by = admin_id
    message.status = action_data.action

    await db.commit()
    await db.refresh(message)

    return MailMessageResponse.model_validate(message)

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
