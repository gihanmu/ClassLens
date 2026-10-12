"""Pydantic v2 data contracts for Google ADK agents and multi-agent pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class QualityStatus(str, Enum):
    """Visual clarity status of the analyzed student work."""

    CLEAR = "clear"
    FAINT_READABLE = "faint_readable"
    BLURRED = "blurred"
    LOW_CONTRAST = "low_contrast"
    ROTATED = "rotated"
    UNREADABLE = "unreadable"


class AnswerStatus(str, Enum):
    """Correctness of the final stated/inferred numerical answer."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNDETERMINED = "undetermined"


class ReasoningStatus(str, Enum):
    """Mathematical validity of the visible step reasoning."""

    SUPPORTED_CORRECT = "supported_correct"
    SUPPORTED_ERROR = "supported_error"
    INCOMPLETE = "incomplete"
    UNDETERMINED = "undetermined"


class VisualObservation(BaseModel):
    """An atomic physical mark observed on the student response image."""

    kind: Literal[
        "number_line",
        "equation",
        "arrow_jump",
        "bracket_curve",
        "circled_result",
        "text_label",
    ] = Field(description="Classification of visible mark")
    value: str = Field(description="Transcribed value, label, or coordinate string")
    confidence: float = Field(ge=0.0, le=1.0, description="Visual detection confidence")
    start_pos: Optional[float] = Field(
        default=None, description="Starting coordinate if kind is arrow_jump or bracket_curve"
    )
    end_pos: Optional[float] = Field(
        default=None, description="Ending coordinate if kind is arrow_jump or bracket_curve"
    )
    direction: Optional[Literal["left", "right", "none"]] = Field(
        default=None, description="Arrow head orientation"
    )
    stated_magnitude: Optional[float] = Field(
        default=None, description="Written step magnitude label (e.g. '+12') if present"
    )
    bounding_box: Optional[List[float]] = Field(
        default=None, description="Normalized coordinates [ymin, xmin, ymax, xmax]"
    )


class VisualEvidenceOutput(BaseModel):
    """Output contract for Agent 1: VisualEvidenceAgent."""

    quality_status: QualityStatus = Field(description="Perceived image quality")
    observations: List[VisualObservation] = Field(
        default_factory=list, description="List of physical marks transcribed from image"
    )
    has_number_line: bool = Field(description="Whether a 1D horizontal number line is present")
    final_answer_marked: Optional[str] = Field(
        default=None, description="Explicit circled or written answer if present"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall perceptual transcription confidence"
    )
    provenance: str = Field(
        default="synthetic_mock_fixture",
        description="Source tracking (e.g. 'gemini-3.8-flash' or 'synthetic_mock_fixture')",
    )
    resolution_mode: Literal["standard_768px", "high_res_evaluation"] = Field(
        default="standard_768px", description="Image resolution mode used for inference"
    )
    ambiguities: List[str] = Field(
        default_factory=list,
        description="Visual ambiguities identified during extraction",
    )
    requires_teacher_review: bool = Field(
        default=False,
        description="Whether perceptual ambiguities require teacher review",
    )
    teacher_review_reason: Optional[str] = Field(
        default=None,
        description="Explanation if teacher review is requested by visual extraction",
    )
    raw_extraction: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw structured schema dictionary from upstream multimodal model",
    )


class CandidateHypothesis(BaseModel):
    """A plausible mathematical strategy interpreting the observed student marks."""

    hypothesis_id: str
    starting_point: float
    strategy_description: str
    step_sequence: List[str]
    is_valid_alternative_path: bool
    confidence: float = Field(ge=0.0, le=1.0)


class CandidateHypothesesOutput(BaseModel):
    """Output contract for Agent 2: MathInterpretationAgent."""

    hypotheses: List[CandidateHypothesis] = Field(
        default_factory=list, description="Competing mathematical solution paths"
    )
    detected_strategy: str = Field(description="Identified primary pedagogical strategy")
    reasoning_completeness: Literal["complete", "partial", "incomplete"] = Field(
        description="Whether steps account for the full expression"
    )
    confidence: float = Field(ge=0.0, le=1.0)


class VerifiedStep(BaseModel):
    """Individual step verified by deterministic mathematical tools."""

    step_number: int
    operation: str
    expected_result: float
    observed_result: Optional[float]
    is_correct: bool
    evidence_citation: str


class FirstSupportedError(BaseModel):
    """Localized first failure point grounded in observed evidence."""

    step_number: int
    error_type: Literal[
        "directional_sign", "magnitude_miscount", "arithmetic_slip", "misread_problem", "other"
    ]
    observed_behavior: str
    expected_behavior: str
    explanation: str


class DiagnosticOutput(BaseModel):
    """Output contract for Agent 3: DiagnosticAgent."""

    answer_status: AnswerStatus
    reasoning_status: ReasoningStatus
    inferred_final_answer: Optional[str] = None
    verified_steps: List[VerifiedStep] = Field(default_factory=list)
    first_supported_error: Optional[FirstSupportedError] = None
    misconception_taxonomy_id: Optional[str] = None
    taxonomy_title: Optional[str] = None
    is_compensatory_error: bool = False
    confidence: float = Field(ge=0.0, le=1.0)


class CriticAuditOutput(BaseModel):
    """Output contract for Agent 4: IndependentCriticAgent."""

    approved: bool = Field(description="True if diagnosis is grounded without hallucinations")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_grounded: bool
    contradiction_detected: bool
    reinterpretation_needed: bool
    discrepancy_notes: List[str] = Field(default_factory=list)
    requires_teacher_review: bool
    teacher_review_reason: Optional[str] = None
    critic_attempt_number: int = Field(default=1, le=2)


class DifferentiatedAction(BaseModel):
    """Targeted pedagogical intervention for a specific misconception cluster."""

    target_misconception_id: str
    action_type: Literal["concrete_manipulative", "worked_example", "guided_inquiry"]
    title: str
    instructional_steps: List[str]
    student_count_affected: int


class ExitTicketItem(BaseModel):
    """Formative assessment item generated for post-lesson check."""

    question_number: int
    prompt: str
    target_misconception: str
    expected_answer: str
    sympy_verified: bool = True


class CohortIntelligenceOutput(BaseModel):
    """Output contract for Agent 5: CohortIntelligenceAgent."""

    executive_narrative: str
    dominant_misconceptions: List[str]
    differentiated_actions: List[DifferentiatedAction]
    formative_exit_ticket: List[ExitTicketItem]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentResponseAnalysis(BaseModel):
    """Complete synthesized output of per-response multi-agent analysis."""

    response_id: str
    quality_status: QualityStatus
    visual_evidence: VisualEvidenceOutput
    candidate_hypotheses: CandidateHypothesesOutput
    diagnosis: DiagnosticOutput
    critic_audit: CriticAuditOutput
    answer_status: AnswerStatus
    reasoning_status: ReasoningStatus
    is_compensatory_error: bool = False
    needs_teacher_review: bool
    teacher_review_reason: Optional[str] = None
    reinterpretation_attempted: bool = False
    execution_latency_ms: int = 0
    tokens_consumed: int = 0
    is_mock: bool = Field(
        default=True,
        description="Strict provenance guardrail: True if produced via offline mock adapter",
    )
    model_version: str = Field(
        default="mock-offline-fixture",
        description="Model identifier or mock fixture version label",
    )
    cost_estimate_usd: Optional[float] = Field(
        default=None,
        description="Estimated inference cost in USD for this analysis",
    )
    live_telemetry: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Live telemetry details including token counts and model location",
    )
