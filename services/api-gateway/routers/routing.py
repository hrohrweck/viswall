from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from shared.database import get_db, AsyncSessionLocal
from shared.models import RoutingRule
from shared.schemas import (
    RoutingRuleCreate,
    RoutingRuleUpdate,
    RoutingRuleResponse,
)
from shared.security import require_auth, require_admin
from shared.audit_logger import log_audit
from utils.agent_client import AgentClientError
from utils.firewall_dispatch import apply_firewall_config
from routers.firewall import reload_firewall

router = APIRouter()


@router.get("/rules/{instance_id}", response_model=List[RoutingRuleResponse])
async def get_routing_rules(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get routing rules for an instance"""
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.instance_id == instance_id)
        .order_by(RoutingRule.order_index)
    )
    rules = result.scalars().all()
    return [RoutingRuleResponse.model_validate(r) for r in rules]


@router.post("/rules/{instance_id}", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    instance_id: int,
    data: RoutingRuleCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new routing rule"""
    # Get next order index
    result = await db.execute(
        select(func.count(RoutingRule.id)).where(
            RoutingRule.instance_id == instance_id
        )
    )
    order_index = data.order_index or ((result.scalar() or 0) * 10)

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
        order_index=order_index,
    )

    db.add(rule)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="create", resource_type="routing_rule", resource_id=rule.id, instance_id=instance_id)

    await db.refresh(rule)

    # Policy routing rides in the firewall dispatch payload (mirrors routers.firewall NAT/routing wiring).
    background_tasks.add_task(reload_firewall, instance_id)

    return RoutingRuleResponse.model_validate(rule)


@router.get("/rules/detail/{rule_id}", response_model=RoutingRuleResponse)
async def get_routing_rule(
    rule_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get a single routing rule"""
    result = await db.execute(
        select(RoutingRule).where(RoutingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )

    return RoutingRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: int,
    data: RoutingRuleUpdate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a routing rule"""
    result = await db.execute(
        select(RoutingRule).where(RoutingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="update", resource_type="routing_rule", resource_id=rule.id, instance_id=rule.instance_id)

    await db.refresh(rule)

    background_tasks.add_task(reload_firewall, rule.instance_id)

    return RoutingRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routing_rule(
    rule_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a routing rule"""
    result = await db.execute(
        select(RoutingRule).where(RoutingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )

    instance_id = rule.instance_id
    await db.delete(rule)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="delete", resource_type="routing_rule", resource_id=rule_id, instance_id=rule.instance_id)

    background_tasks.add_task(reload_firewall, instance_id)



@router.post("/apply/{instance_id}")
async def apply_routing(
    instance_id: int,
    admin_id: int = Depends(require_admin),
):
    """Apply routing rules to an instance"""
    # Policy routing rides in the firewall dispatch payload (RoutingRule rows).
    try:
        async with AsyncSessionLocal() as db:
            await apply_firewall_config(db, instance_id, user_id=admin_id)
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")

    return {"status": "applied", "instance_id": instance_id}
