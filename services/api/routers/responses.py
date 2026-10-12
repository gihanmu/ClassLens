"""Student response inspection, override, and image delivery routes."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.api.auth.dependencies import get_current_user, require_csrf
from services.api.repository.memory_repo import (
    AuditEventDoc,
    ResponseDoc,
    UserDoc,
    memory_repo,
)

router = APIRouter(prefix="/responses", tags=["responses"])


class TeacherOverrideRequest(BaseModel):
    action: str  # approved_as_is, overridden, marked_unreadable
    override_taxonomy_id: Optional[str] = None
    notes: Optional[str] = None


def _get_verified_response(response_id: str, org_id: str) -> ResponseDoc:
    """Retrieves response only if it belongs to the authenticated user's organization."""
    resp = memory_repo.get_response(response_id)
    if not resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response {response_id} not found",
        )
    asm = memory_repo.get_assessment(resp.assessment_id, org_id=org_id)
    if not asm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found or cross-tenant access denied",
        )
    return resp


@router.get("/{response_id}")
async def get_response_detail(
    response_id: str,
    raw_doc: bool = Query(default=False),
    user: UserDoc = Depends(get_current_user),
):
    """Retrieves response analysis detail or underlying document with tenant isolation."""
    resp = _get_verified_response(response_id, user.organization_id)

    # Normalize to base response identifier (e.g. resp_80545ef3)
    base_id = "resp_" + resp.id.split("_resp_")[-1] if "_resp_" in resp.id else resp.id

    # If raw_doc is requested or analysis_data is not yet populated, return ResponseDoc with response_id alias
    if raw_doc or not resp.analysis_data:
        doc_data = resp.model_dump()
        doc_data["response_id"] = base_id
        doc_data["doc_id"] = resp.id
        return doc_data

    # Return full StudentResponseAnalysis structure with top-level metadata attached
    data = dict(resp.analysis_data)
    data["response_id"] = base_id
    data["doc_id"] = resp.id
    data["pseudonym_label"] = resp.pseudonym_label
    data["task_status"] = resp.task_status
    data["upload_status"] = resp.upload_status
    data["needs_teacher_review"] = resp.needs_teacher_review
    data["teacher_review_status"] = resp.teacher_review_status
    data["teacher_override_taxonomy_id"] = resp.teacher_override_taxonomy_id
    data["teacher_notes"] = resp.teacher_notes
    if "intake_quality" in resp.analysis_data:
        data["intake_quality"] = resp.analysis_data["intake_quality"]
    return data


@router.post("/{response_id}/analyze")
async def analyze_single_response(
    response_id: str,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Triggers multi-agent evaluation for a single student response."""
    from services.api.dispatch.inline_dispatcher import inline_dispatcher
    import uuid

    resp = _get_verified_response(response_id, user.organization_id)
    await inline_dispatcher._process_single_response(
        job_id=f"job_single_{uuid.uuid4().hex[:6]}",
        assessment_id=resp.assessment_id,
        resp_id=resp.id,
    )
    return memory_repo.get_response(resp.id)


class TeacherReviewAction(BaseModel):
    decision: str  # approved_as_is, overridden, marked_unreadable
    override_misconception_id: Optional[str] = None
    notes: Optional[str] = None


class TeacherReviewResponse(BaseModel):
    response_id: str
    teacher_review_status: str
    reviewed_by: str
    reviewed_at: Any


@router.put("/{response_id}/review", response_model=TeacherReviewResponse)
async def submit_teacher_review(
    response_id: str,
    req: TeacherReviewAction,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Submits a teacher review decision, updating review status and logging audit event."""
    resp = _get_verified_response(response_id, user.organization_id)

    # Normalize review decision
    raw_action = req.decision.strip().lower()
    if raw_action in ("confirm", "approved_as_is"):
        norm_action = "approved_as_is"
    elif raw_action in ("override", "overridden"):
        norm_action = "overridden"
    elif raw_action in ("marked_unreadable", "unreadable"):
        norm_action = "marked_unreadable"
    elif raw_action in ("insufficient_evidence", "insufficient"):
        norm_action = "insufficient_evidence"
    else:
        norm_action = req.decision

    try:
        updated = memory_repo.record_teacher_override(
            assessment_id=resp.assessment_id,
            response_id=response_id,
            teacher_id=user.id,
            action=norm_action,
            override_taxonomy=req.override_misconception_id,
            notes=req.notes,
        )
        return TeacherReviewResponse(
            response_id=response_id,
            teacher_review_status=updated.teacher_review_status,
            reviewed_by=user.id,
            reviewed_at=updated.updated_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{response_id}/override", response_model=ResponseDoc)
async def submit_teacher_override(
    response_id: str,
    req: TeacherOverrideRequest,
    user: UserDoc = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Submits a teacher review decision, updating review status and logging audit event."""
    resp = _get_verified_response(response_id, user.organization_id)

    try:
        updated = memory_repo.record_teacher_override(
            assessment_id=resp.assessment_id,
            response_id=response_id,
            teacher_id=user.id,
            action=req.action,
            override_taxonomy=req.override_taxonomy_id,
            notes=req.notes,
        )
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{response_id}/audit-trail", response_model=List[AuditEventDoc])
async def get_response_audit_trail(
    response_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Returns the immutable audit event log for the student response."""
    resp = _get_verified_response(response_id, user.organization_id)
    return memory_repo.get_audit_events_for_response(response_id)


@router.get("/{response_id}/image")
async def get_response_image(
    response_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Serves the student response handwritten image file read-only."""
    resp = _get_verified_response(response_id, user.organization_id)

    from services.worker.security.provenance_guard import TRUSTED_SYNTHETIC_DIR

    # Check local uploads directory first
    uploads_dir = os.path.realpath(os.path.join(os.getcwd(), "local-data", "uploads"))
    upload_candidates = [
        os.path.join(uploads_dir, user.organization_id, resp.assessment_id, resp.source_filename),
        os.path.join(uploads_dir, user.organization_id, resp.source_filename),
        os.path.join(uploads_dir, resp.source_filename),
    ]
    for cand in upload_candidates:
        real_cand = os.path.realpath(cand)
        if real_cand.startswith(uploads_dir) and os.path.isfile(real_cand):
            return FileResponse(
                path=real_cand,
                media_type=resp.image_mime_type,
                filename=os.path.basename(real_cand),
            )

    dataset_dir = os.path.join(os.getcwd(), "dataset", "problem_1065658")
    file_path = os.path.join(dataset_dir, resp.source_filename)

    if not os.path.isfile(file_path):
        synthetic_path = TRUSTED_SYNTHETIC_DIR / resp.source_filename
        if synthetic_path.is_file():
            file_path = str(synthetic_path)
        else:
            # Try searching by prefix if source_filename was fallback
            prefix = response_id.replace("resp_", "")
            found = False
            if os.path.isdir(dataset_dir):
                for f in os.listdir(dataset_dir):
                    if f.startswith(prefix):
                        file_path = os.path.join(dataset_dir, f)
                        found = True
                        break
            if not found and TRUSTED_SYNTHETIC_DIR.is_dir():
                for f in os.listdir(TRUSTED_SYNTHETIC_DIR):
                    if prefix in f or f.startswith(prefix):
                        file_path = str(TRUSTED_SYNTHETIC_DIR / f)
                        found = True
                        break
            if not found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image file for {response_id} not found on disk",
                )

    return FileResponse(
        path=file_path,
        media_type=resp.image_mime_type,
        filename=os.path.basename(file_path),
    )
