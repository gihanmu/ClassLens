"""Evaluation harness schemas and data contracts for ClassLens Gate 4C."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GroundTruthHop(BaseModel):
    """Represents a visible ground-truth hop stroke on a number line."""
    step_number: int
    start_pos: float
    end_pos: float
    stated_magnitude: Optional[float] = None
    actual_displacement: float
    direction: str  # "left" | "right"
    is_valid_hop: bool
    error_type: Optional[str] = None


class BenchmarkCase(BaseModel):
    """Specification of an independently authored benchmark case."""
    case_id: str
    version: str = "1.0.0"
    category: str  # e.g., "canonical_correct", "procedural_error", "off_by_one", "ambiguous_insufficient", "compensatory", "arithmetic_slip", "sign_error"
    topic: str = "Integers & Number Lines"
    grade_level: str = "Secondary 1 / Grade 7"
    problem_statement: str = "Evaluate -6 + 12 - 4 on the number line"
    target_canonical_value: str = "2"
    image_reference: str
    source_type: str = "synthetic_curated"  # "synthetic_curated", "synthetic_procedural", "manually_authored", "consented_sample"

    # Ground truth expectations
    expected_answer: Optional[str] = None
    expected_answer_status: str  # "correct", "incorrect", "undetermined"
    expected_reasoning_status: str  # "supported_correct", "supported_error", "incomplete", "unverifiable"
    expected_error_step_index: Optional[int] = None
    expected_misconception_id: Optional[str] = None
    expected_is_compensatory: bool = False
    expected_evidence_sufficiency: str = "sufficient"  # "sufficient", "partial", "insufficient"
    expected_requires_teacher_review: bool = False
    expected_critic_verdict: str = "audit_passed"  # "audit_passed", "review_required", "audit_rejected"

    # Verification bounds
    allowed_alternative_taxonomies: List[str] = Field(default_factory=list)
    ground_truth_hops: List[GroundTruthHop] = Field(default_factory=list)
    annotation_notes: str = ""
    provenance: str = "ClassLens Assessment Evaluation Benchmark v1"


class BenchmarkDataset(BaseModel):
    """Versioned collection of benchmark cases."""
    dataset_name: str = "ClassLens Number-Line Reliability Benchmark"
    version: str = "1.0.0"
    created_at: str
    description: str
    target_problem_reference: str = "problem_1065658"
    cases: List[BenchmarkCase]


class CaseEvaluationResult(BaseModel):
    """Detailed result of running one benchmark case against the pipeline."""
    case_id: str
    category: str
    passed: bool

    # Metric-level matches
    answer_status_match: bool
    final_answer_match: bool
    reasoning_status_match: bool
    error_step_match: bool
    misconception_match: bool
    evidence_sufficiency_match: bool
    teacher_review_match: bool
    critic_verdict_match: bool

    # Safety checks
    false_positive_misconception: bool = False
    unsupported_claim_detected: bool = False
    contradiction_detected: bool = False

    expected_values: Dict[str, Any]
    actual_values: Dict[str, Any]
    failure_reasons: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class MetricFraction(BaseModel):
    """Strictly specified metric with numerator, denominator, and human-readable formatting."""
    name: str
    numerator: int
    denominator: int
    percentage: Optional[float] = None
    display_value: str
    description: str
    target_threshold_pct: Optional[float] = None
    status: str = "PASS"  # "PASS", "FAIL", "N/A"


class EvaluationMetricsSummary(BaseModel):
    """Comprehensive reliability metrics across Categories A through G."""
    # A. Outcome Accuracy
    answer_status_accuracy: MetricFraction
    final_answer_agreement: MetricFraction

    # B. Reasoning Verification Accuracy
    reasoning_status_accuracy: MetricFraction
    procedural_error_detection_recall: MetricFraction
    error_step_localization_accuracy: MetricFraction

    # C. Misconception Detection
    misconception_precision: MetricFraction
    misconception_recall: MetricFraction
    exact_taxonomy_match_rate: MetricFraction
    false_positive_misconception_rate: MetricFraction

    # D. Evidence Grounding & Abstention
    evidence_sufficiency_accuracy: MetricFraction
    appropriate_abstention_rate: MetricFraction
    unsupported_claim_rate: MetricFraction
    contradiction_rate: MetricFraction

    # E. Teacher Review Routing
    review_routing_precision: MetricFraction
    review_routing_recall: MetricFraction
    missed_critical_review_count: int = 0

    # F. Critic Effectiveness
    critic_verdict_accuracy: MetricFraction
    critic_challenge_precision: MetricFraction

    # G. Performance
    avg_latency_ms: float
    total_eval_duration_sec: float


class CategoryBreakdownItem(BaseModel):
    category: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_pct: float


class BenchmarkReport(BaseModel):
    """Top-level serialized evaluation report."""
    run_id: str
    dataset_version: str
    timestamp: str
    git_commit: str
    pipeline_mode: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_pass_rate_pct: float
    overall_status: str  # "PASS" | "FAIL"
    metrics: EvaluationMetricsSummary
    category_breakdown: List[CategoryBreakdownItem]
    case_results: List[CaseEvaluationResult]
