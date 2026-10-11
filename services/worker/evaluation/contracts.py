"""Pydantic v2 data contracts for Gate 3 Gemini visual evidence extraction and feasibility evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ExtractionCertainty(str, Enum):
    """Categorical certainty level of visual evidence extraction."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CANNOT_DETERMINE = "cannot_determine"


class ImageQualityAssessment(str, Enum):
    """Visual legibility and clarity of the student worksheet."""

    CLEAR = "clear"
    FAINT_READABLE = "faint_readable"
    BLURRED = "blurred"
    LOW_CONTRAST = "low_contrast"
    UNREADABLE = "unreadable"


class HopDirection(str, Enum):
    """Direction of observed number line movement."""

    RIGHT_POSITIVE = "right_positive"
    LEFT_NEGATIVE = "left_negative"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


class VisibleFinalAnswer(BaseModel):
    """Visible written or circled numerical final answer on the worksheet."""

    value: Optional[str] = Field(
        default=None,
        description="The literal text/number written in the answer box or circled on the worksheet.",
    )
    evidence_location: Optional[str] = Field(
        default=None,
        description="Textual description of where the answer appears (e.g., 'answer box below number line').",
    )
    certainty: ExtractionCertainty = Field(
        default=ExtractionCertainty.CANNOT_DETERMINE,
        description="Categorical certainty of the extracted final answer value.",
    )


class ObservedHop(BaseModel):
    """An individual hop, arc, or displacement marked on the number line."""

    hop_index: int = Field(description="Sequential order of the hop (1-indexed).")
    start_value: Optional[float] = Field(
        default=None,
        description="Visible start coordinate on the number line. Null if ambiguous or not marked.",
    )
    end_value: Optional[float] = Field(
        default=None,
        description="Visible landing coordinate on the number line. Null if ambiguous.",
    )
    direction: HopDirection = Field(
        default=HopDirection.AMBIGUOUS,
        description="Orientation of the arc and arrowhead.",
    )
    arc_drawn: bool = Field(
        default=True,
        description="True if an overt curved arc or jump stroke is physically present.",
    )
    arrowhead_visible: bool = Field(
        default=False,
        description="True if an explicit triangular or directional arrowhead is visible.",
    )
    stated_magnitude_label: Optional[str] = Field(
        default=None,
        description="Explicit written label above/below the arc (e.g. '+12', '-4').",
    )
    evidence_description: str = Field(
        description="Objective description of the physical ink stroke without inferring intent.",
    )
    certainty: ExtractionCertainty = Field(
        default=ExtractionCertainty.MEDIUM,
        description="Categorical certainty of this hop's boundaries.",
    )


class NumberLineObservation(BaseModel):
    """Observable structural characteristics of the printed and annotated number line."""

    is_present: bool = Field(
        default=True, description="True if a 1D horizontal number line is visible."
    )
    min_visible_tick: Optional[float] = Field(
        default=None, description="Lowest printed tick label observed on the axis."
    )
    max_visible_tick: Optional[float] = Field(
        default=None, description="Highest printed tick label observed on the axis."
    )
    zero_position_visible: bool = Field(
        default=True, description="True if tick mark '0' is clearly visible and labeled."
    )
    observed_hops: List[ObservedHop] = Field(
        default_factory=list,
        description="Ordered sequence of physical hops drawn along the number line.",
    )


class VisualAmbiguity(BaseModel):
    """Documented area of uncertainty, blur, or conflicting ink marks."""

    element: Literal["number_line", "hop", "arrowhead", "final_answer", "erased_mark", "other"] = (
        Field(description="Component exhibiting ambiguity.")
    )
    description: str = Field(description="Detailed description of what is unclear.")
    severity: Literal["minor", "blocking"] = Field(
        default="minor",
        description="Blocking if ambiguity prevents verifying the mathematical step.",
    )


class GeminiVisualEvidenceSchema(BaseModel):
    """Strict structured output contract for Gate 3 Gemini visual extraction."""

    response_id: str = Field(
        description="Unique identifier of the response matching the manifest."
    )
    image_quality: ImageQualityAssessment = Field(
        description="Objective clarity classification of the image."
    )
    visible_final_answer: VisibleFinalAnswer = Field(
        description="Extracted final answer and its certainty."
    )
    number_line: NumberLineObservation = Field(
        description="Extracted number-line markings and observed hops."
    )
    ambiguities: List[VisualAmbiguity] = Field(
        default_factory=list,
        description="List of ambiguous, conflicting, or partially erased marks.",
    )
    unsupported_observations: List[str] = Field(
        default_factory=list,
        description="Any observations that cannot be definitively substantiated from ink.",
    )
    requires_teacher_review: bool = Field(
        default=False,
        description="True if image quality is degraded or blocking ambiguities exist.",
    )
    teacher_review_reason: Optional[str] = Field(
        default=None,
        description="Specific reason why human teacher inspection is required.",
    )


class VerifiedStepComparison(BaseModel):
    """Comparison of an observed hop against deterministic mathematical expectations."""

    step_number: int
    operation: str
    expected_displacement: float
    observed_displacement: Optional[float]
    is_mathematically_valid: bool
    evidence_citation: str
    discrepancy_explanation: Optional[str] = None


class EvaluationCaseResult(BaseModel):
    """Consolidated outcome of evaluating a single response case in Gate 3."""

    response_id: str
    manifest_category: Literal["canonical_correct", "procedural_error", "ambiguous_incomplete"]
    model_id: str
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    visual_extraction: GeminiVisualEvidenceSchema
    verified_steps: List[VerifiedStepComparison] = Field(default_factory=list)
    math_verification_status: Literal["valid", "arithmetic_error", "uninterpretable", "cannot_determine"]
    first_supported_error_step: Optional[int] = None
    first_supported_error_type: Optional[str] = None
    teacher_escalation_correct: bool = True
    schema_valid: bool = True
    dry_run: bool = True
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchEvaluationSummary(BaseModel):
    """Aggregated metrics and results from a batch evaluation run."""

    total_cases: int
    schema_conformant_count: int
    mathematical_accuracy_rate: float
    teacher_escalation_precision: float
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    mean_latency_ms: float = 0.0
    model_id: str = "gemini-3.8-flash"
    dry_run: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    case_results: List[EvaluationCaseResult] = Field(default_factory=list)
