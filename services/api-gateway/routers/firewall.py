from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from shared.database import get_db
from shared.schemas import (
    FirewallRuleCreate, FirewallRuleUpdate, FirewallRuleResponse
)
from shared.security import require_auth, require_admin

router = APIRouter()

@router.get("/rules/{instance_id}", response_model=List[FirewallRuleResponse])
async def get_rules(instance_id: int, user_id: int = Depends(require_auth)):
    """Get firewall rules for an instance"""
    # TODO: Implement
    return []

@router.post("/rules/{instance_id}", response_model=FirewallRuleResponse)
async def create_rule(
    instance_id: int,
    data: FirewallRuleCreate,
    user_id: int = Depends(require_admin)
):
    """Create a new firewall rule"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")

@router.patch("/rules/{rule_id}", response_model=FirewallRuleResponse)
async def update_rule(
    rule_id: int,
    data: FirewallRuleUpdate,
    user_id: int = Depends(require_admin)
):
    """Update a firewall rule"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, user_id: int = Depends(require_admin)):
    """Delete a firewall rule"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/apply/{instance_id}")
async def apply_rules(instance_id: int, user_id: int = Depends(require_admin)):
    """Apply firewall rules to an instance"""
    # TODO: Push rules to instance via agent
    return {"status": "queued"}
