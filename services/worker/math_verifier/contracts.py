"""Typed data contracts for deterministic mathematical verification."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HopDirection(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


class NumberLineHop(BaseModel):
    """Represents a single continuous directed movement on a 1D number line."""

    step_number: int = Field(ge=1, description="1-indexed sequence number of the hop")
    start: float = Field(description="Starting coordinate of the hop on the number line")
    end: float = Field(description="Terminal coordinate of the hop on the number line")
    direction: Literal["left", "right", "none"] = Field(
        description="Observed arrow head direction"
    )
    stated_magnitude: Optional[float] = Field(
        default=None, description="Explicit magnitude label written by student if present"
    )
    evidence_status: Literal["supported", "partially_supported", "insufficient_evidence"] = Field(
        default="supported",
        description="Visual evidence grounding supporting this hop",
    )

    @property
    def displacement(self) -> float:
        """Signed coordinate change: end - start."""
        return self.end - self.start

    @property
    def magnitude(self) -> float:
        """Absolute geometric length."""
        return abs(self.displacement)


class QuestionRule(BaseModel):
    """Specification of target arithmetic problem and pedagogical rules."""

    problem_id: str = Field(description="Unique question identifier")
    expression: str = Field(description="Original arithmetic formula (e.g. '-6 + 12 - 4')")
    target_value: Optional[float] = Field(
        default=None,
        description="Expected final numerical answer. If None, evaluated via SymPy.",
    )
    expected_addends: List[float] = Field(
        description="Ordered sequence of signed addends comprising the expression"
    )
    allow_direct_start: bool = Field(
        default=True,
        description="Whether a student may start directly at term 1 without a hop from 0",
    )
    allow_commutative: bool = Field(
        default=True,
        description="Whether addends may appear in valid commutative permutations",
    )
    tolerance: float = Field(
        default=1e-4,
        description="Floating point numerical comparison tolerance",
    )


class StepVerificationResult(BaseModel):
    """Verification outcome of a single student hop transition."""

    step_number: int
    start_pos: float
    end_pos: float
    expected_displacement: float
    observed_displacement: float
    is_correct: bool
    deviation: float = Field(
        description="observed_displacement - expected_displacement"
    )
    error_taxonomy: Optional[str] = Field(
        default=None, description="Classified misconception taxonomy code if step is erroneous"
    )
    evidence_notes: str = Field(description="Human-readable explanation of the step check")
    evidence_status: Literal["supported", "partially_supported", "insufficient_evidence"] = Field(
        default="supported",
        description="Grounding level of visual marks supporting this step",
    )
    verification_status: Literal["verified_valid", "verified_error", "unverifiable"] = Field(
        default="verified_valid",
        description="Verification state: valid calculation, verified error, or unverifiable due to insufficient evidence",
    )


class MathVerificationVerdict(BaseModel):
    """Comprehensive evaluation verdict decoupling answer correctness from reasoning correctness."""

    is_reasoning_valid: bool = Field(
        description="True if all observed number line hops are mathematically valid"
    )
    is_final_answer_valid: bool = Field(
        description="True if student's final indicated answer matches target value"
    )
    detected_method: Literal["hop_from_zero", "direct_start", "commutative", "unrecognized", "insufficient_evidence"] = Field(
        description="Identified pedagogical number line strategy"
    )
    starting_point: Optional[float] = Field(
        default=None, description="Initial coordinate of the student's hop chain"
    )
    terminal_position: Optional[float] = Field(
        default=None, description="Final endpoint coordinate reached on the number line"
    )
    evidence_sufficiency: Literal["sufficient", "partial", "insufficient"] = Field(
        default="sufficient",
        description="Assessment of overall visual evidence grounding",
    )
    verified_steps: List[StepVerificationResult] = Field(
        default_factory=list, description="Step-by-step verification results"
    )
    first_error_step: Optional[int] = Field(
        default=None, description="1-indexed step number where the first deviation occurred"
    )
    first_error_taxonomy: Optional[str] = Field(
        default=None, description="Taxonomy ID of the first supported error"
    )
    is_compensatory_error: bool = Field(
        default=False,
        description="True if student arrived at correct target despite erroneous intermediate steps",
    )
    needs_teacher_review: bool = Field(
        default=False,
        description="True if step reasoning is ambiguous, unreadable, or contradictory",
    )
    teacher_review_reason: Optional[str] = Field(
        default=None, description="Explanation for routing to educator review"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, default=1.0, description="Mathematical certainty score"
    )
