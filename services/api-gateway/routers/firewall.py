from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from shared.database import get_db
from shared.models import FirewallRule, NATRule, RoutingRule, Instance, NetworkInterface
from shared.schemas import (
    FirewallRuleCreate, FirewallRuleUpdate, FirewallRuleResponse,
    NATRuleCreate, NATRuleResponse,
    RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleResponse
)
from shared.security import require_auth, require_admin

router = APIRouter()

# ============================================================================
# FIREWALL RULE ENDPOINTS
# ============================================================================

@router.get("/rules/{instance_id}", response_model=List[FirewallRuleResponse])
async def list_firewall_rules(
    instance_id: int,
    chain: Optional[str] = None,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List firewall rules for an instance"""
    query = select(FirewallRule).where(FirewallRule.instance_id == instance_id)
    
    if chain:
        query = query.where(FirewallRule.chain == chain)
    
    result = await db.execute(query.order_by(FirewallRule.order_index))
    rules = result.scalars().all()
    return [FirewallRuleResponse.model_validate(r) for r in rules]

@router.post("/rules/{instance_id}", response_model=FirewallRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_firewall_rule(
    instance_id: int,
    data: FirewallRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new firewall rule"""
    # Verify instance exists
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Get next order index if not specified
    if data.order_index is None:
        result = await db.execute(
            select(FirewallRule).where(FirewallRule.instance_id == instance_id)
        )
        max_order = max([r.order_index for r in result.scalars().all()] + [0])
        data.order_index = max_order + 10
    
    rule = FirewallRule(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        chain=data.chain,
        source_type=data.source_type,
        source_value=data.source_value,
        dest_type=data.dest_type,
        dest_value=data.dest_value,
        service_protocol=data.service_protocol,
        service_ports=data.service_ports,
        action=data.action.value,
        log_enabled=data.log_enabled,
        order_index=data.order_index
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    # Trigger firewall reload
    background_tasks.add_task(reload_firewall, instance_id)
    
    return FirewallRuleResponse.model_validate(rule)

@router.get("/rules/detail/{rule_id}", response_model=FirewallRuleResponse)
async def get_firewall_rule(
    rule_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get firewall rule details"""
    result = await db.execute(
        select(FirewallRule).where(FirewallRule.id == rule_id)
    )
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
    await db.refresh(rule)
    
    background_tasks.add_task(reload_firewall, rule.instance_id)
    
    return FirewallRuleResponse.model_validate(rule)

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_firewall_rule(
    rule_id: int,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a firewall rule"""
    result = await db.execute(
        select(FirewallRule).where(FirewallRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    instance_id = rule.instance_id
    await db.delete(rule)
    await db.commit()
    
    background_tasks.add_task(reload_firewall, instance_id)
    
    return None

@router.post("/rules/{rule_id}/move")
async def move_rule(
    rule_id: int,
    direction: str,  # up, down, top, bottom
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Move a rule in the order"""
    result = await db.execute(
        select(FirewallRule).where(FirewallRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Reorder logic
    if direction == "up":
        # Find rule above
        result = await db.execute(
            select(FirewallRule).where(
                and_(
                    FirewallRule.instance_id == rule.instance_id,
                    FirewallRule.order_index < rule.order_index
                )
            ).order_by(FirewallRule.order_index.desc())
        )
        above = result.scalars().first()
        if above:
            rule.order_index, above.order_index = above.order_index, rule.order_index
    
    elif direction == "down":
        # Find rule below
        result = await db.execute(
            select(FirewallRule).where(
                and_(
                    FirewallRule.instance_id == rule.instance_id,
                    FirewallRule.order_index > rule.order_index
                )
            ).order_by(FirewallRule.order_index)
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
    admin_id: int = Depends(require_admin)
):
    """Apply firewall configuration to instance"""
    background_tasks.add_task(reload_firewall, instance_id)
    return {"status": "queued"}

# ============================================================================
# NAT ENDPOINTS
# ============================================================================

@router.get("/nat/{instance_id}", response_model=List[NATRuleResponse])
async def list_nat_rules(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List NAT rules for an instance"""
    result = await db.execute(
        select(NATRule).where(NATRule.instance_id == instance_id)
    )
    rules = result.scalars().all()
    return [NATRuleResponse.model_validate(r) for r in rules]

@router.post("/nat/{instance_id}", response_model=NATRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_nat_rule(
    instance_id: int,
    data: NATRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
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
        service_ports=data.service_ports
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
    db: AsyncSession = Depends(get_db)
):
    """List policy routing rules"""
    result = await db.execute(
        select(RoutingRule).where(RoutingRule.instance_id == instance_id)
        .order_by(RoutingRule.order_index)
    )
    rules = result.scalars().all()
    return [RoutingRuleResponse.model_validate(r) for r in rules]

@router.post("/routing/{instance_id}", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    instance_id: int,
    data: RoutingRuleCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
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
        order_index=data.order_index or 100
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    background_tasks.add_task(reload_firewall, instance_id)
    
    return RoutingRuleResponse.model_validate(rule)

# ============================================================================
# TRAFFIC SHAPING ENDPOINTS
# ============================================================================

@router.get("/qos/{instance_id}")
async def get_qos_status(
    instance_id: int,
    user_id: int = Depends(require_auth)
):
    """Get QoS status for an instance"""
    return {
        "instance_id": instance_id,
        "interfaces": [],
        "status": "not_implemented"
    }

@router.post("/qos/{instance_id}/interface/{interface}")
async def configure_qos(
    instance_id: int,
    interface: str,
    download_rate: int,  # kbps
    upload_rate: int,
    algorithm: str = "cake",  # cake, fq_codel, htb
    admin_id: int = Depends(require_admin)
):
    """Configure QoS on an interface"""
    return {
        "status": "queued",
        "interface": interface,
        "download_rate": download_rate,
        "upload_rate": upload_rate,
        "algorithm": algorithm
    }

# ============================================================================
# BLOCKLIST ENDPOINTS
# ============================================================================

@router.post("/block/{instance_id}")
async def block_ip(
    instance_id: int,
    ip: str,
    reason: Optional[str] = "manual",
    duration: Optional[str] = "1h",
    admin_id: int = Depends(require_admin)
):
    """Block an IP address"""
    return {
        "status": "queued",
        "action": "block",
        "ip": ip,
        "duration": duration
    }

@router.post("/unblock/{instance_id}")
async def unblock_ip(
    instance_id: int,
    ip: str,
    admin_id: int = Depends(require_admin)
):
    """Unblock an IP address"""
    return {
        "status": "queued",
        "action": "unblock",
        "ip": ip
    }

@router.get("/stats/{instance_id}")
async def get_firewall_stats(
    instance_id: int,
    user_id: int = Depends(require_auth)
):
    """Get firewall statistics"""
    return {
        "instance_id": instance_id,
        "connections": 0,
        "packets_accepted": 0,
        "packets_dropped": 0,
        "blacklist_size": 0,
        "top_blocked_ips": []
    }

# Background task
async def reload_firewall(instance_id: int):
    """Reload firewall configuration on an instance"""
    # Would call firewall agent via message queue or API
    pass
