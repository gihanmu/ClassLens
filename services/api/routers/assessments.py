"""Assessment management and batch analysis routes."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.api.auth.dependencies import get_current_user, require_csrf
from services.api.dispatch.inline_dispatcher import inline_dispatcher
from services.api.repository.memory_repo import (
    AssessmentDoc,
    QuestionConfig,
    ResponseDoc,
    UserDoc,
    memory_repo,
    utc_now,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


class CreateAssessmentRequest(BaseModel):
    title: str = "Integers on Number Line: Checkpoint 1"
    class_id: str = "cls_sec1_math"
    question: QuestionConfig = Field(default_factory=QuestionConfig)


class AnalyzeRequest(BaseModel):
    idempotency_key: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    assessment_id: str
    job_id: Optional[str] = None
    status: str
    total_items: int
    completed_items: int
    failed_items: int


@router.get("", response_model=List[AssessmentDoc])
async def list_assessments(user: UserDoc = Depends(get_current_user)):
    """Lists all assessments in the authenticated user's organization."""
    return memory_repo.list_assessments(user.organization_id)


@router.post("", response_model=AssessmentDoc, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    req: CreateAssessmentRequest,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Creates a new assessment record."""
    asm = AssessmentDoc(
        id=f"asm_{uuid.uuid4().hex[:8]}",
        class_id=req.class_id,
        organization_id=user.organization_id,
        title=req.title,
        status="ready",
        question=req.question,
        total_responses=0,
        reviewed_responses=0,
    )
    return memory_repo.create_assessment(asm)


@router.get("/{assessment_id}", response_model=AssessmentDoc)
async def get_assessment(
    assessment_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Retrieves assessment details with organization tenancy check."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access denied",
        )
    return asm


@router.post("/{assessment_id}/demo-import")
async def import_demo_responses(
    assessment_id: str,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Imports student responses for the assessment."""
    try:
        if assessment_id == "asm_synthetic_cases":
            imported = memory_repo.import_synthetic_demo_cases(assessment_id, user.organization_id)
        else:
            imported = memory_repo.import_demo_responses(assessment_id, user.organization_id)
        return {
            "assessment_id": assessment_id,
            "imported_count": len(imported),
            "responses": imported,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{assessment_id}/responses", response_model=List[ResponseDoc])
async def list_assessment_responses(
    assessment_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Lists all student responses registered for the assessment."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return memory_repo.list_responses(assessment_id)


@router.post(
    "/{assessment_id}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_batch_analysis(
    assessment_id: str,
    background_tasks: BackgroundTasks,
    req: Optional[AnalyzeRequest] = None,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Launches batch multi-agent analysis for all responses in the assessment."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    responses = memory_repo.list_responses(assessment_id)
    if not responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot analyze: No student responses found. Import responses first.",
        )

    idempotency_key = req.idempotency_key if req else None

    # Check if job already exists for this idempotency key
    if idempotency_key and idempotency_key in memory_repo.idempotency_keys:
        existing_job_id = memory_repo.idempotency_keys[idempotency_key]
        job = memory_repo.analysis_jobs[existing_job_id]
        return {
            "job_id": job.id,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "idempotent_replay": True,
        }

    job = memory_repo.create_or_get_analysis_job(
        assessment_id=assessment_id,
        idempotency_key=idempotency_key,
        total_items=len(responses),
    )

    # Launch background inline processing via FastAPI BackgroundTasks
    response_ids = [r.id for r in responses]
    background_tasks.add_task(
        inline_dispatcher.dispatch_analysis_batch,
        job.id,
        assessment_id,
        response_ids,
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "failed_items": job.failed_items,
        "idempotent_replay": False,
    }


@router.get("/{assessment_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    assessment_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Polls batch analysis progress for an assessment."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Find the most recent job for this assessment
    jobs = [j for j in memory_repo.analysis_jobs.values() if j.assessment_id == assessment_id]
    if not jobs:
        # Check if responses are already completed
        resps = memory_repo.list_responses(assessment_id)
        completed = sum(1 for r in resps if r.task_status == "COMPLETED")
        return AnalysisStatusResponse(
            assessment_id=assessment_id,
            job_id=None,
            status="completed" if completed == len(resps) and len(resps) > 0 else "idle",
            total_items=len(resps),
            completed_items=completed,
            failed_items=0,
        )

    # Return latest job
    latest_job = sorted(jobs, key=lambda j: j.created_at, reverse=True)[0]
    return AnalysisStatusResponse(
        assessment_id=assessment_id,
        job_id=latest_job.id,
        status=latest_job.status,
        total_items=latest_job.total_items,
        completed_items=latest_job.completed_items,
        failed_items=latest_job.failed_items,
    )
