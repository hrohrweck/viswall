from fastapi import APIRouter, Depends, HTTPException
from typing import List

from shared.schemas import (
    MetricSnapshotResponse, MetricsQuery, MetricsSummary
)
from shared.security import require_auth

router = APIRouter()

@router.get("/latest/{instance_id}", response_model=MetricSnapshotResponse)
async def get_latest_metrics(instance_id: int, user_id: int = Depends(require_auth)):
    """Get latest metrics for an instance"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/query", response_model=List[MetricSnapshotResponse])
async def query_metrics(query: MetricsQuery, user_id: int = Depends(require_auth)):
    """Query historical metrics"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/summary", response_model=List[MetricsSummary])
async def get_metrics_summary(query: MetricsQuery, user_id: int = Depends(require_auth)):
    """Get aggregated metrics summary"""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/dashboard/{instance_id}")
async def get_dashboard_data(instance_id: int, user_id: int = Depends(require_auth)):
    """Get all metrics needed for dashboard"""
    # TODO: Implement comprehensive dashboard data
    return {
        "instance_id": instance_id,
        "system": {},
        "network": {},
        "mail": {}
    }
