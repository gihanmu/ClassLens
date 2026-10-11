"""Pydantic contracts for cohort analytics and differentiated reteaching."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MisconceptionCluster(BaseModel):
    """A cluster of student errors grouped by pedagogical taxonomy."""

    taxonomy_id: str
    title: str
    affected_count: int
    affected_percentage: float
    teacher_confirmed_count: int = 0
    ai_proposed_count: int = 0
    sample_response_ids: List[str] = Field(default_factory=list)


class CohortStatistics(BaseModel):
    """Deterministic, code-computed distribution metrics across a student cohort."""

    total_responses: int
    correct_count: int
    correct_percentage: float
    error_count: int
    error_percentage: float
    incomplete_count: int = 0
    incomplete_percentage: float = 0.0
    unreadable_count: int
    unreadable_percentage: float
    compensatory_errors_count: int = 0
    needs_teacher_review_count: int = 0
    misconception_clusters: List[MisconceptionCluster] = Field(default_factory=list)
