"""Cohort intelligence and class insights routes."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from services.api.auth.dependencies import get_current_user
from services.api.repository.memory_repo import UserDoc, memory_repo
from services.worker.cohort.contracts import CohortStatistics
from services.worker.cohort.statistics_calculator import CohortStatisticsCalculator
from services.worker.cohort.synthesizer import CohortSynthesizer

router = APIRouter(prefix="/assessments", tags=["cohort"])


@router.get("/{assessment_id}/insights")
async def get_assessment_insights(
    assessment_id: str,
    user: UserDoc = Depends(get_current_user),
):
    """Computes deterministic cohort distribution and synthesizes reteaching interventions."""
    asm = memory_repo.get_assessment(assessment_id, org_id=user.organization_id)
    if not asm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access denied",
        )

    responses = memory_repo.list_responses(assessment_id)
    if not responses:
        stats = CohortStatisticsCalculator.calculate([])
        intelligence = CohortSynthesizer.synthesize_insights(
            stats,
            assessment=asm,
            assessment_id=assessment_id,
        )
        return {
            "assessment_id": assessment_id,
            "statistics": stats,
            "intelligence": intelligence,
        }

    # Pass response documents (with analysis_data and any teacher overrides) to statistics calculator
    response_payloads = []
    for r in responses:
        if r.analysis_data:
            payload = dict(r.analysis_data)
            payload["teacher_review_status"] = r.teacher_review_status
            payload["teacher_override_taxonomy_id"] = r.teacher_override_taxonomy_id
            payload["teacher_notes"] = r.teacher_notes
            payload["pseudonym_label"] = r.pseudonym_label
            response_payloads.append(payload)
        else:
            payload = r.model_dump()
            response_payloads.append(payload)

    stats = CohortStatisticsCalculator.calculate(response_payloads)
    intelligence = CohortSynthesizer.synthesize_insights(
        stats,
        assessment=asm,
        assessment_id=assessment_id,
        responses=response_payloads,
    )

    return {
        "assessment_id": assessment_id,
        "statistics": stats,
        "intelligence": intelligence,
    }
