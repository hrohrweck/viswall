from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from shared.database import get_db
from shared.models import (
    FirewallRule,
    NATRule,
    RoutingRule,
    Instance,
    NetworkInterface,
    QoSPolicy,
    QoSClass,
)
from shared.schemas import (
    FirewallRuleCreate,
    FirewallRuleUpdate,
    FirewallRuleResponse,
    NATRuleCreate,
    NATRuleResponse,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    RoutingRuleResponse,
    NetworkInterfaceCreate,
    NetworkInterfaceResponse,
    QoSPolicyCreate,
    QoSPolicyUpdate,
    QoSPolicyResponse,
    QoSClassCreate,
    QoSClassUpdate,
    QoSClassResponse,
    QoSStatsResponse,
    QoSQueueStats,
)
from shared.security import require_auth, require_admin
from shared.audit_logger import log_audit
from utils.agent_client import agent_request, AgentClientError

router = APIRouter()

# ============================================================================
# FIREWALL RULE ENDPOINTS
# ============================================================================


@router.get("/rules/{instance_id}", response_model=List[FirewallRuleResponse])
async def list_firewall_rules(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List firewall rules for an instance"""
    query = select(FirewallRule).where(FirewallRule.instance_id == instance_id)

    result = await db.execute(query.order_by(FirewallRule.order_index))
    rules = result.scalars().all()
    return [FirewallRuleResponse.model_validate(r) for r in rules]


@router.post(
    "/rules/{instance_id}",
    response_model=FirewallRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_firewall_rule(
    instance_id: int,
    data: FirewallRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new firewall rule"""
    # Verify instance exists
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Instance not found")

    result = await db.execute(
        select(FirewallRule).where(FirewallRule.instance_id == instance_id)
    )
    max_order = max([r.order_index for r in result.scalars().all()] + [0])

    rule = FirewallRule(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        source_type=data.source_type,
        source_value=data.source_value,
        dest_type=data.dest_type,
        dest_value=data.dest_value,
        service_protocol=data.service_protocol,
        service_ports=data.service_ports,
        action=data.action.value,
        log_enabled=data.log_enabled,
        order_index=max_order + 10
    )

    db.add(rule)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="create", resource_type="firewall_rule", resource_id=rule.id, instance_id=rule.instance_id)

    await db.refresh(rule)

    # Trigger firewall reload
    background_tasks.add_task(reload_firewall, instance_id)

    return FirewallRuleResponse.model_validate(rule)


@router.get("/rules/detail/{rule_id}", response_model=FirewallRuleResponse)
async def get_firewall_rule(
    rule_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get firewall rule details"""
    result = await db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return FirewallRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=FirewallRuleResponse)
async def update_firewall_rule(
    rule_id: int,
    data: FirewallRuleUpdate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FirewallRule).where(FirewallRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "action" and value:
            value = value.value
        setattr(rule, field, value)

    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="update", resource_type="firewall_rule", resource_id=rule.id, instance_id=rule.instance_id)

    await db.refresh(rule)

    background_tasks.add_task(reload_firewall, rule.instance_id)

    return FirewallRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_firewall_rule(
    rule_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a firewall rule"""
    result = await db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    instance_id = rule.instance_id
    await db.delete(rule)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="delete", resource_type="firewall_rule", resource_id=rule_id, instance_id=instance_id)


    background_tasks.add_task(reload_firewall, instance_id)

    return None


@router.post("/rules/{rule_id}/move")
async def move_rule(
    rule_id: int,
    direction: str,  # up, down, top, bottom
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Move a rule in the order"""
    result = await db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Reorder logic
    if direction == "up":
        # Find rule above
        result = await db.execute(
            select(FirewallRule)
            .where(
                and_(
                    FirewallRule.instance_id == rule.instance_id,
                    FirewallRule.order_index < rule.order_index,
                )
            )
            .order_by(FirewallRule.order_index.desc())
        )
        above = result.scalars().first()
        if above:
            rule.order_index, above.order_index = above.order_index, rule.order_index

    elif direction == "down":
        # Find rule below
        result = await db.execute(
            select(FirewallRule)
            .where(
                and_(
                    FirewallRule.instance_id == rule.instance_id,
                    FirewallRule.order_index > rule.order_index,
                )
            )
            .order_by(FirewallRule.order_index)
        )
        below = result.scalars().first()
        if below:
            rule.order_index, below.order_index = below.order_index, rule.order_index

    await db.commit()

    return {"status": "moved", "direction": direction}


@router.post("/apply/{instance_id}")
async def apply_firewall(
    instance_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
):
    """Apply firewall configuration to instance"""
    background_tasks.add_task(reload_firewall, instance_id)
    return {"status": "queued"}


# ============================================================================
# NETWORK INTERFACE ENDPOINTS
# ============================================================================


@router.get("/interfaces/{instance_id}", response_model=List[NetworkInterfaceResponse])
async def list_network_interfaces(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List network interfaces for an instance"""
    result = await db.execute(
        select(NetworkInterface).where(NetworkInterface.instance_id == instance_id)
    )
    interfaces = result.scalars().all()
    return [NetworkInterfaceResponse.model_validate(i) for i in interfaces]


# ============================================================================
# NAT ENDPOINTS
# ============================================================================


@router.get("/nat/{instance_id}", response_model=List[NATRuleResponse])
async def list_nat_rules(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List NAT rules for an instance"""
    result = await db.execute(select(NATRule).where(NATRule.instance_id == instance_id))
    rules = result.scalars().all()
    return [NATRuleResponse.model_validate(r) for r in rules]


@router.post(
    "/nat/{instance_id}",
    response_model=NATRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_nat_rule(
    instance_id: int,
    data: NATRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a NAT rule"""
    rule = NATRule(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        type=data.type,
        interface=data.interface,
        source_network=data.source_network,
        dest_network=data.dest_network,
        to_source=data.to_source,
        to_destination=data.to_destination,
        service_protocol=data.service_protocol,
        service_ports=data.service_ports,
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    background_tasks.add_task(reload_firewall, instance_id)

    return NATRuleResponse.model_validate(rule)


# ============================================================================
# ROUTING ENDPOINTS
# ============================================================================


@router.get("/routing/{instance_id}", response_model=List[RoutingRuleResponse])
async def list_routing_rules(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List policy routing rules"""
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.instance_id == instance_id)
        .order_by(RoutingRule.order_index)
    )
    rules = result.scalars().all()
    return [RoutingRuleResponse.model_validate(r) for r in rules]


@router.post(
    "/routing/{instance_id}",
    response_model=RoutingRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_routing_rule(
    instance_id: int,
    data: RoutingRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a policy routing rule"""
    rule = RoutingRule(
        instance_id=instance_id,
        name=data.name,
        enabled=data.enabled,
        source_network=data.source_network,
        dest_network=data.dest_network,
        service=data.service,
        inbound_interface=data.inbound_interface,
        gateway=data.gateway,
        outbound_interface=data.outbound_interface,
        mark=data.mark,
        order_index=data.order_index or 100,
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    background_tasks.add_task(reload_firewall, instance_id)

    return RoutingRuleResponse.model_validate(rule)


# ============================================================================
# TRAFFIC SHAPING / QoS ENDPOINTS
# ============================================================================


@router.get("/qos/{instance_id}", response_model=List[QoSPolicyResponse])
async def list_qos_policies(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy)
        .where(QoSPolicy.instance_id == instance_id)
        .options(selectinload(QoSPolicy.classes))
        .order_by(QoSPolicy.interface_name)
    )
    policies = result.scalars().unique().all()
    return [QoSPolicyResponse.model_validate(p) for p in policies]


@router.post(
    "/qos/{instance_id}",
    response_model=QoSPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_qos_policy(
    instance_id: int,
    data: QoSPolicyCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Instance not found")

    existing = await db.execute(
        select(QoSPolicy).where(
            and_(
                QoSPolicy.instance_id == instance_id,
                QoSPolicy.interface_name == data.interface_name,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A QoS policy already exists for interface '{data.interface_name}'",
        )

    policy = QoSPolicy(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        interface_name=data.interface_name,
        interface_id=data.interface_id,
        algorithm=data.algorithm.value,
        download_kbps=data.download_kbps,
        upload_kbps=data.upload_kbps,
        created_by=admin_id,
    )
    db.add(policy)
    await db.flush()

    if data.algorithm.value == "htb":
        classes_to_add = (
            data.classes
            if data.classes
            else _default_htb_classes(data.download_kbps, data.upload_kbps)
        )
        for cls_data in classes_to_add:
            qos_class = QoSClass(
                policy_id=policy.id,
                name=cls_data.name,
                priority=cls_data.priority,
                min_rate_kbps=cls_data.min_rate_kbps,
                max_rate_kbps=cls_data.max_rate_kbps,
                match_ports=cls_data.match_ports,
                match_dscp=cls_data.match_dscp,
                match_protocol=cls_data.match_protocol,
            )
            db.add(qos_class)

    await db.commit()
    await db.refresh(policy)

    if policy.enabled:
        background_tasks.add_task(apply_qos_policy, instance_id, policy.id)

    result = await db.execute(
        select(QoSPolicy)
        .where(QoSPolicy.id == policy.id)
        .options(selectinload(QoSPolicy.classes))
    )
    return QoSPolicyResponse.model_validate(result.scalar_one())


@router.get("/qos/{instance_id}/{policy_id}", response_model=QoSPolicyResponse)
async def get_qos_policy(
    instance_id: int,
    policy_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy)
        .where(and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id))
        .options(selectinload(QoSPolicy.classes))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return QoSPolicyResponse.model_validate(policy)


@router.patch("/qos/{instance_id}/{policy_id}", response_model=QoSPolicyResponse)
async def update_qos_policy(
    instance_id: int,
    policy_id: int,
    data: QoSPolicyUpdate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy).where(
            and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "algorithm" and value:
            value = value.value
        setattr(policy, field, value)

    await db.commit()
    await db.refresh(policy)

    if policy.enabled:
        background_tasks.add_task(apply_qos_policy, instance_id, policy.id)

    result = await db.execute(
        select(QoSPolicy)
        .where(QoSPolicy.id == policy.id)
        .options(selectinload(QoSPolicy.classes))
    )
    return QoSPolicyResponse.model_validate(result.scalar_one())


@router.delete("/qos/{instance_id}/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qos_policy(
    instance_id: int,
    policy_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy).where(
            and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    interface_name = policy.interface_name
    await db.delete(policy)
    await db.commit()

    background_tasks.add_task(clear_qos_on_interface, instance_id, interface_name)

    return None


@router.post("/qos/{instance_id}/{policy_id}/apply")
async def apply_qos_now(
    instance_id: int,
    policy_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy).where(
            and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    background_tasks.add_task(apply_qos_policy, instance_id, policy.id)
    return {"status": "queued", "policy_id": policy_id}


@router.get("/qos/{instance_id}/{policy_id}/stats", response_model=QoSStatsResponse)
async def get_qos_stats(
    instance_id: int,
    policy_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy).where(
            and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    stats = await fetch_qos_stats_from_agent(instance_id, policy.interface_name)
    return QoSStatsResponse(
        policy_id=policy_id,
        interface=policy.interface_name,
        algorithm=policy.algorithm,
        download_kbps=policy.download_kbps,
        upload_kbps=policy.upload_kbps,
        queues=stats.get("queues", []),
        raw=stats.get("raw"),
        collected_at=datetime.utcnow(),
    )


# --- QoS Class endpoints (for HTB) ---


@router.post(
    "/qos/{instance_id}/{policy_id}/classes",
    response_model=QoSClassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_qos_class(
    instance_id: int,
    policy_id: int,
    data: QoSClassCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSPolicy).where(
            and_(QoSPolicy.id == policy_id, QoSPolicy.instance_id == instance_id)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if policy.algorithm != "htb":
        raise HTTPException(
            status_code=400,
            detail="Traffic classes are only supported for HTB algorithm",
        )

    qos_class = QoSClass(
        policy_id=policy_id,
        name=data.name,
        priority=data.priority,
        min_rate_kbps=data.min_rate_kbps,
        max_rate_kbps=data.max_rate_kbps,
        match_ports=data.match_ports,
        match_dscp=data.match_dscp,
        match_protocol=data.match_protocol,
    )
    db.add(qos_class)
    await db.commit()
    await db.refresh(qos_class)

    if policy.enabled:
        background_tasks.add_task(apply_qos_policy, instance_id, policy_id)

    return QoSClassResponse.model_validate(qos_class)


@router.patch(
    "/qos/{instance_id}/{policy_id}/classes/{class_id}",
    response_model=QoSClassResponse,
)
async def update_qos_class(
    instance_id: int,
    policy_id: int,
    class_id: int,
    data: QoSClassUpdate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSClass).where(
            and_(QoSClass.id == class_id, QoSClass.policy_id == policy_id)
        )
    )
    qos_class = result.scalar_one_or_none()
    if not qos_class:
        raise HTTPException(status_code=404, detail="Class not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(qos_class, field, value)

    await db.commit()
    await db.refresh(qos_class)

    policy_result = await db.execute(select(QoSPolicy).where(QoSPolicy.id == policy_id))
    policy = policy_result.scalar_one_or_none()
    if policy and policy.enabled:
        background_tasks.add_task(apply_qos_policy, instance_id, policy_id)

    return QoSClassResponse.model_validate(qos_class)


@router.delete(
    "/qos/{instance_id}/{policy_id}/classes/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_qos_class(
    instance_id: int,
    policy_id: int,
    class_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QoSClass).where(
            and_(QoSClass.id == class_id, QoSClass.policy_id == policy_id)
        )
    )
    qos_class = result.scalar_one_or_none()
    if not qos_class:
        raise HTTPException(status_code=404, detail="Class not found")

    await db.delete(qos_class)
    await db.commit()

    policy_result = await db.execute(select(QoSPolicy).where(QoSPolicy.id == policy_id))
    policy = policy_result.scalar_one_or_none()
    if policy and policy.enabled:
        background_tasks.add_task(apply_qos_policy, instance_id, policy_id)

    return None


# --- Helper functions ---


def _default_htb_classes(download_kbps: int, upload_kbps: int) -> List[QoSClassCreate]:
    return [
        QoSClassCreate(
            name="High Priority (VoIP/SSH/DNS)",
            priority=1,
            min_rate_kbps=int(download_kbps * 0.30),
            max_rate_kbps=download_kbps,
            match_ports=[22, 53, 5060, 5061],
            match_protocol="any",
        ),
        QoSClassCreate(
            name="General Traffic",
            priority=2,
            min_rate_kbps=int(download_kbps * 0.40),
            max_rate_kbps=download_kbps,
            match_ports=[],
            match_protocol="any",
        ),
        QoSClassCreate(
            name="Bulk/Background",
            priority=3,
            min_rate_kbps=int(download_kbps * 0.30),
            max_rate_kbps=download_kbps,
            match_ports=[],
            match_protocol="any",
        ),
    ]


async def apply_qos_policy(instance_id: int, policy_id: int):
    from shared.database import AsyncSessionLocal
    from shared.models import QoSPolicy
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(QoSPolicy).where(QoSPolicy.id == policy_id)
            )
            policy = result.scalar_one_or_none()
            if not policy:
                return

            await agent_request(
                db=db,
                instance_id=instance_id,
                method="POST",
                path="/qos/apply",
                json_data={
                    "interface": policy.interface_name,
                    "algorithm": policy.algorithm,
                    "download_kbps": policy.download_kbps,
                    "upload_kbps": policy.upload_kbps,
                    "classes": [],
                },
            )
        except AgentClientError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to apply QoS policy {policy_id} to instance {instance_id}: {e}")


async def clear_qos_on_interface(instance_id: int, interface_name: str):
    from shared.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await agent_request(
                db=db,
                instance_id=instance_id,
                method="POST",
                path="/qos/clear",
                json_data={"interface": interface_name},
            )
        except AgentClientError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to clear QoS on {interface_name} for instance {instance_id}: {e}")


async def fetch_qos_stats_from_agent(instance_id: int, interface_name: str) -> dict:
    from shared.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await agent_request(
                db=db,
                instance_id=instance_id,
                method="GET",
                path=f"/qos/stats/{interface_name}",
            )
            return result.get("stats", {"queues": [], "raw": None})
        except AgentClientError:
            return {"queues": [], "raw": None}


# ============================================================================
# BLOCKLIST ENDPOINTS
# ============================================================================


@router.post("/block/{instance_id}")
async def block_ip(
    instance_id: int,
    ip: str,
    reason: Optional[str] = "manual",
    duration: Optional[str] = "1h",
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Block an IP address"""
    try:
        await agent_request(
            db=db,
            instance_id=instance_id,
            method="POST",
            path="/block",
            json_data={"ip": ip, "reason": reason},
        )
        return {"status": "success", "action": "block", "ip": ip, "duration": duration}
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")


@router.post("/unblock/{instance_id}")
async def unblock_ip(
    instance_id: int,
    ip: str,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unblock an IP address"""
    try:
        await agent_request(
            db=db,
            instance_id=instance_id,
            method="POST",
            path="/unblock",
            json_data={"ip": ip},
        )
        return {"status": "success", "action": "unblock", "ip": ip}
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")


@router.get("/stats/{instance_id}")
async def get_firewall_stats(instance_id: int, user_id: int = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    """Get firewall statistics"""
    try:
        result = await agent_request(
            db=db,
            instance_id=instance_id,
            method="GET",
            path="/stats",
        )
        return result
    except AgentClientError:
        return {
            "instance_id": instance_id,
            "connections": 0,
            "packets_accepted": 0,
            "packets_dropped": 0,
            "blacklist_size": 0,
            "top_blocked_ips": [],
        }


async def reload_firewall(instance_id: int):
    """Reload firewall configuration on an instance"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Firewall reload requested for instance {instance_id} (agent endpoint not yet implemented)")
