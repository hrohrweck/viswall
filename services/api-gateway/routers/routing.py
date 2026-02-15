from fastapi import APIRouter, Depends, HTTPException
from typing import List

from shared.schemas import (
    RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleResponse
)
from shared.security import require_auth, require_admin

router = APIRouter()

@router.get("/rules/{instance_id}", response_model=List[RoutingRuleResponse])
async def get_routing_rules(instance_id: int, user_id: int = Depends(require_auth)):
    """Get routing rules for an instance"""
    return []

@router.post("/rules/{instance_id}", response_model=RoutingRuleResponse)
async def create_routing_rule(
    instance_id: int,
    data: RoutingRuleCreate,
    user_id: int = Depends(require_admin)
):
    """Create a new routing rule"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.patch("/rules/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: int,
    data: RoutingRuleUpdate,
    user_id: int = Depends(require_admin)
):
    """Update a routing rule"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/rules/{rule_id}")
async def delete_routing_rule(rule_id: int, user_id: int = Depends(require_admin)):
    """Delete a routing rule"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/apply/{instance_id}")
async def apply_routing(instance_id: int, user_id: int = Depends(require_admin)):
    """Apply routing rules to an instance"""
    return {"status": "queued"}
