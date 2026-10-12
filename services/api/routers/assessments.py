"""Assessment management and batch analysis routes."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
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
from services.worker.intake.quality_service import ImageQualityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["assessments"])


class CreateAssessmentRequest(BaseModel):
    title: str = "Integers on Number Line: Checkpoint 1"
    class_id: str = "cls_sec1_math"
    math_topic: str = "Integer operations on number lines"
    grade_level: str = "Secondary 1"
    question_text: Optional[str] = None
    latex_formula: Optional[str] = None
    expected_answer: Optional[str] = None
    question: Optional[QuestionConfig] = None


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
    q_cfg = req.question or QuestionConfig(
        problem_reference_id=uuid.uuid4().hex[:6],
        question_text=req.question_text or "Use the number line to evaluate -6 + 12 - 4",
        latex_formula=req.latex_formula or "-6 + 12 - 4",
        expected_answer=req.expected_answer or "2",
    )
    if req.question_text:
        q_cfg.question_text = req.question_text
    if req.latex_formula:
        q_cfg.latex_formula = req.latex_formula
    if req.expected_answer:
        q_cfg.expected_answer = req.expected_answer

    asm = AssessmentDoc(
        id=f"asm_{uuid.uuid4().hex[:8]}",
        class_id=req.class_id,
        organization_id=user.organization_id,
        title=req.title,
        math_topic=req.math_topic,
        grade_level=req.grade_level,
        status="ready",
        question=q_cfg,
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


@router.post(
    "/{assessment_id}/upload",
    response_model=ResponseDoc,
    status_code=status.HTTP_201_CREATED,
)
async def upload_student_worksheet(
    assessment_id: str,
    file: UploadFile = File(...),
    student_id: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None),
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Securely validates and stores an uploaded handwritten student worksheet."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access denied",
        )

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # 1. Quarantine validation & quality scoring
    validation_result, sanitized_bytes = ImageQualityService.process_image_bytes(raw_bytes)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result.error_message or "Invalid or malicious image file",
        )

    # 2. Secure file persistence in local-data/uploads/{org_id}/{assessment_id}/
    safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", user.organization_id)
    safe_asm = re.sub(r"[^a-zA-Z0-9_-]", "_", assessment_id)
    upload_dir = Path("local-data/uploads") / safe_org / safe_asm
    upload_dir.mkdir(parents=True, exist_ok=True)

    clean_orig_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", file.filename or "worksheet.jpg")
    unique_file_name = f"{uuid.uuid4().hex[:8]}_{clean_orig_name}"
    target_path = upload_dir / unique_file_name

    payload_to_write = sanitized_bytes if sanitized_bytes is not None else raw_bytes
    with open(target_path, "wb") as f_out:
        f_out.write(payload_to_write)

    # 3. Create student response document
    existing_responses = memory_repo.list_responses(assessment_id)
    next_idx = len(existing_responses) + 1
    resp_id = f"resp_{uuid.uuid4().hex[:8]}"
    stu_id = student_id.strip() if student_id and student_id.strip() else f"stu_{next_idx:02d}"
    stu_label = student_name.strip() if student_name and student_name.strip() else f"Student-{next_idx:02d}"

    doc = ResponseDoc(
        id=resp_id,
        assessment_id=assessment_id,
        pseudonymous_student_id=stu_id,
        pseudonym_label=stu_label,
        source_filename=unique_file_name,
        image_mime_type=validation_result.mime_type,
        sha256_hash=validation_result.sha256_hash,
        upload_status="validated",
        task_status="AWAITING_LIVE_ANALYSIS",
        answer_status="not_assessed",
        reasoning_status="not_assessed",
        teacher_review_status="unreviewed",
        is_mock=True,
        model_version="uploaded-unseen",
        analysis_data={
            "offline_status_message": (
                "Image uploaded successfully. Live visual analysis is required to interpret this new worksheet."
            ),
            "quality_status": validation_result.quality_status.value,
            "sharpness_score": validation_result.sharpness_score,
            "contrast_score": validation_result.contrast_score,
            "original_dimensions": list(validation_result.original_dimensions),
            "normalized_dimensions": list(validation_result.normalized_dimensions),
        },
    )

    return memory_repo.create_response(doc)


@router.post(
    "/{assessment_id}/upload-batch",
    response_model=List[ResponseDoc],
    status_code=status.HTTP_201_CREATED,
)
async def upload_batch_student_worksheets(
    assessment_id: str,
    files: List[UploadFile] = File(...),
    mappings_json: Optional[str] = Form(None),
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Securely uploads and validates multiple handwritten student worksheets."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access denied",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for batch upload",
        )

    mappings = {}
    if mappings_json:
        try:
            mappings = json.loads(mappings_json)
        except Exception:
            mappings = {}

    safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", user.organization_id)
    safe_asm = re.sub(r"[^a-zA-Z0-9_-]", "_", assessment_id)
    upload_dir = Path("local-data/uploads") / safe_org / safe_asm
    upload_dir.mkdir(parents=True, exist_ok=True)

    created_docs: List[ResponseDoc] = []
    existing_count = len(memory_repo.list_responses(assessment_id))

    for idx, f in enumerate(files, start=1):
        raw_bytes = await f.read()
        if not raw_bytes:
            continue

        validation_result, sanitized_bytes = ImageQualityService.process_image_bytes(raw_bytes)
        if not validation_result.is_valid:
            logger.warning(
                f"Batch upload skipped invalid file {f.filename}: {validation_result.error_message}"
            )
            continue

        clean_orig_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", f.filename or f"worksheet_{idx}.jpg")
        unique_file_name = f"{uuid.uuid4().hex[:8]}_{clean_orig_name}"
        target_path = upload_dir / unique_file_name

        payload_to_write = sanitized_bytes if sanitized_bytes is not None else raw_bytes
        with open(target_path, "wb") as out_f:
            out_f.write(payload_to_write)

        file_meta = mappings.get(f.filename, {}) if isinstance(mappings, dict) else {}
        student_idx = existing_count + len(created_docs) + 1
        stu_id = file_meta.get("student_id") or f"stu_{student_idx:02d}"
        stu_name = file_meta.get("student_name") or f"Student-{student_idx:02d}"

        doc = ResponseDoc(
            id=f"resp_{uuid.uuid4().hex[:8]}",
            assessment_id=assessment_id,
            pseudonymous_student_id=stu_id,
            pseudonym_label=stu_name,
            source_filename=unique_file_name,
            image_mime_type=validation_result.mime_type,
            sha256_hash=validation_result.sha256_hash,
            upload_status="validated",
            task_status="AWAITING_LIVE_ANALYSIS",
            answer_status="not_assessed",
            reasoning_status="not_assessed",
            teacher_review_status="unreviewed",
            is_mock=True,
            model_version="uploaded-unseen",
            analysis_data={
                "offline_status_message": (
                    "Image uploaded successfully. Live visual analysis is required to interpret this new worksheet."
                ),
                "quality_status": validation_result.quality_status.value,
                "sharpness_score": validation_result.sharpness_score,
                "contrast_score": validation_result.contrast_score,
                "original_dimensions": list(validation_result.original_dimensions),
                "normalized_dimensions": list(validation_result.normalized_dimensions),
            },
        )
        created = memory_repo.create_response(doc)
        created_docs.append(created)

    if not created_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="None of the uploaded files were valid images.",
        )

    return created_docs


@router.delete("/{assessment_id}/responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment_response(
    assessment_id: str,
    response_id: str,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Deletes an unassessed response from an assessment."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    deleted = memory_repo.delete_response(response_id, assessment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return None

