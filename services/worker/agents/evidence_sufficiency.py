"""Deterministic evidence sufficiency assessment between visual extraction and mathematical verification.

Enforces Gate 4A.2 Core Engineering Principle:
The system must never infer a definite mathematical misconception from visual
evidence that is insufficient to establish the student's intended steps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from services.worker.agents.contracts import (
    QualityStatus,
    VisualEvidenceOutput,
    VisualObservation,
)


class StepEvidenceEvaluation(BaseModel):
    """Detailed evidence sufficiency evaluation for an individual observed step."""

    step_number: int
    is_supported: bool
    evidence_status: Literal["supported", "partially_supported", "insufficient_evidence"]
    start_pos: Optional[float]
    end_pos: Optional[float]
    direction: Optional[str]
    has_endpoints: bool
    has_arrowhead: bool
    confidence: float
    issues: List[str] = Field(default_factory=list)


class ResponseEvidenceSufficiency(BaseModel):
    """Holistic evidence sufficiency verdict for a student response."""

    overall_sufficiency: Literal["sufficient", "partial", "insufficient"]
    can_evaluate_reasoning: bool
    can_diagnose_misconception: bool
    step_evaluations: List[StepEvidenceEvaluation] = Field(default_factory=list)
    supported_step_count: int = 0
    unverifiable_step_count: int = 0
    is_final_answer_present: bool = False
    unresolved_ambiguities: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class EvidenceSufficiencyEvaluator:
    """Deterministically assesses whether visual evidence supports mathematical evaluation."""

    CONFIDENCE_THRESHOLD_SUPPORTED = 0.70

    @classmethod
    def evaluate_step(
        cls,
        obs: VisualObservation,
        step_number: int,
        global_ambiguities: Optional[List[str]] = None,
    ) -> StepEvidenceEvaluation:
        """Evaluates evidence grounding for a single number line move."""
        issues: List[str] = []

        has_start = obs.start_pos is not None
        has_end = obs.end_pos is not None
        has_endpoints = has_start and has_end

        if not has_start:
            issues.append("missing_starting_coordinate")
        if not has_end:
            issues.append("missing_terminal_coordinate")

        # Arrowhead / direction check
        has_arrowhead = obs.direction in ("left", "right")
        if not has_arrowhead:
            issues.append("missing_or_ambiguous_arrowhead")

        # Confidence check
        if obs.confidence < cls.CONFIDENCE_THRESHOLD_SUPPORTED:
            issues.append(f"low_visual_confidence_{obs.confidence:.2f}")

        # Check for textual ambiguity markers in observation value or global ambiguities
        obs_text = (obs.value or "").lower()
        if "faint" in obs_text or "incomplete" in obs_text or "undetermined" in obs_text:
            issues.append("faint_or_incomplete_stroke")

        if global_ambiguities:
            for amb in global_ambiguities:
                amb_lower = amb.lower()
                if f"hop {step_number}" in amb_lower or f"hop #{step_number}" in amb_lower:
                    issues.append(f"flagged_ambiguity: {amb}")

        # Determine evidence status
        if has_endpoints and has_arrowhead and obs.confidence >= cls.CONFIDENCE_THRESHOLD_SUPPORTED:
            evidence_status = "supported"
            is_supported = True
        elif has_endpoints and (obs.stated_magnitude is not None or obs.confidence >= 0.50):
            evidence_status = "partially_supported"
            is_supported = False
        else:
            evidence_status = "insufficient_evidence"
            is_supported = False

        return StepEvidenceEvaluation(
            step_number=step_number,
            is_supported=is_supported,
            evidence_status=evidence_status,
            start_pos=obs.start_pos,
            end_pos=obs.end_pos,
            direction=obs.direction,
            has_endpoints=has_endpoints,
            has_arrowhead=has_arrowhead,
            confidence=obs.confidence,
            issues=issues,
        )

    @classmethod
    def evaluate(cls, visual: VisualEvidenceOutput) -> ResponseEvidenceSufficiency:
        """Performs comprehensive evidence-sufficiency assessment over VisualEvidenceOutput."""
        reasons: List[str] = []
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]

        # 1. Unreadable or low quality image
        if visual.quality_status in (QualityStatus.UNREADABLE, QualityStatus.BLURRED):
            return ResponseEvidenceSufficiency(
                overall_sufficiency="insufficient",
                can_evaluate_reasoning=False,
                can_diagnose_misconception=False,
                step_evaluations=[],
                supported_step_count=0,
                unverifiable_step_count=len(hops),
                is_final_answer_present=visual.final_answer_marked is not None,
                unresolved_ambiguities=visual.ambiguities,
                reasons=[f"Image quality is {visual.quality_status.value}; handwriting cannot be reliably transcribed."],
            )

        # 2. Number line presence
        if not visual.has_number_line:
            return ResponseEvidenceSufficiency(
                overall_sufficiency="insufficient",
                can_evaluate_reasoning=False,
                can_diagnose_misconception=False,
                step_evaluations=[],
                supported_step_count=0,
                unverifiable_step_count=0,
                is_final_answer_present=visual.final_answer_marked is not None,
                unresolved_ambiguities=visual.ambiguities,
                reasons=["No number line visible in student submission."],
            )

        # 3. Evaluate each hop
        step_evals: List[StepEvidenceEvaluation] = []
        for idx, h in enumerate(hops, start=1):
            eval_res = cls.evaluate_step(h, step_number=idx, global_ambiguities=visual.ambiguities)
            step_evals.append(eval_res)

        supported_count = sum(1 for e in step_evals if e.is_supported)
        unverifiable_count = len(step_evals) - supported_count
        has_final_answer = bool(visual.final_answer_marked and visual.final_answer_marked.strip())

        # Check visual review flags and ambiguities
        has_blocking_ambiguity = visual.requires_teacher_review or (
            len(visual.ambiguities) > 0 and visual.confidence < 0.75
        )

        if has_blocking_ambiguity:
            reasons.append("Visual extraction flagged blocking perceptual ambiguities requiring educator review.")

        for e in step_evals:
            if not e.is_supported:
                reasons.append(f"Step {e.step_number} has insufficient evidence: {', '.join(e.issues)}.")

        # 4. Overall classification
        if supported_count >= 2 and unverifiable_count == 0 and not has_blocking_ambiguity:
            overall = "sufficient"
            can_eval = True
            can_diag = True
        elif supported_count >= 1:
            overall = "partial"
            can_eval = True
            # Misconceptions can only be diagnosed if the error step itself is strictly supported
            can_diag = False
            reasons.append("Partial evidence only: some steps are missing coordinates or arrowheads.")
        else:
            overall = "insufficient"
            can_eval = False
            can_diag = False
            reasons.append("Insufficient visual evidence to reconstruct student's mathematical steps.")

        return ResponseEvidenceSufficiency(
            overall_sufficiency=overall,
            can_evaluate_reasoning=can_eval,
            can_diagnose_misconception=can_diag,
            step_evaluations=step_evals,
            supported_step_count=supported_count,
            unverifiable_step_count=unverifiable_count,
            is_final_answer_present=has_final_answer,
            unresolved_ambiguities=visual.ambiguities,
            reasons=reasons,
        )
