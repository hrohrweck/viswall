from fastapi import APIRouter, Depends, HTTPException
from typing import List

from shared.schemas import AuditLogResponse
from shared.security import require_auth, require_admin

router = APIRouter()

@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: int = Depends(require_admin)
):
    """List audit logs (admin only)"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/instance/{instance_id}", response_model=List[AuditLogResponse])
async def get_instance_logs(
    instance_id: int,
    limit: int = 100,
    user_id: int = Depends(require_auth)
):
    """Get audit logs for a specific instance"""
    raise HTTPException(status_code=501, detail="Not implemented")
