"""Teacher dashboard summary, recent assessments, and attention queue routes."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from services.api.auth.dependencies import get_current_user
from services.api.repository.memory_repo import UserDoc, memory_repo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(user: UserDoc = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieves teacher-level summary metrics, recent assessments, attention items, and activity."""
    return memory_repo.get_dashboard_summary(org_id=user.organization_id)


@router.get("/recent-activity")
async def get_dashboard_recent_activity(user: UserDoc = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Retrieves chronological activity feed of analyses and reviews."""
    summary = memory_repo.get_dashboard_summary(org_id=user.organization_id)
    return summary.get("recent_activity", [])


@router.get("/attention-queue")
async def get_dashboard_attention_queue(user: UserDoc = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Retrieves queue of submissions and assessments requiring teacher attention."""
    summary = memory_repo.get_dashboard_summary(org_id=user.organization_id)
    return summary.get("attention_items", [])
