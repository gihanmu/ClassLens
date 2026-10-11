"""Connector linking Gemini visual extraction outputs to deterministic SymPy mathematical verification."""

from __future__ import annotations

from typing import List, Optional, Tuple
from services.worker.evaluation.contracts import (
    GeminiVisualEvidenceSchema,
    VerifiedStepComparison,
    EvaluationCaseResult,
    ExtractionCertainty,
    ImageQualityAssessment,
    HopDirection,
)
from services.worker.math_verifier.contracts import (
    NumberLineHop,
    QuestionRule,
    MathVerificationVerdict,
)
from services.worker.math_verifier.verifier import verify_student_math_reasoning
from services.worker.math_verifier.sympy_checker import SymPyChecker


def get_canonical_problem_1065658_rule() -> QuestionRule:
    """Returns QuestionRule for Problem #1065658 (-6 + 12 - 4)."""
    return QuestionRule(
        problem_id="problem_1065658",
        expression="-6 + 12 - 4",
        target_value=2.0,
        expected_addends=[-6.0, 12.0, -4.0],
        allow_direct_start=True,
        allow_commutative=True,
        tolerance=0.01,
    )


class VerificationConnector:
    """Bridges Gemini visual evidence extraction with deterministic SymPy verification."""

    @staticmethod
    def parse_float_safe(val_str: Optional[str]) -> Optional[float]:
        """Safely parses a numerical string into a float, stripping extraneous characters."""
        if val_str is None:
            return None
        cleaned = val_str.strip().replace(" ", "").replace("=", "")
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            # Attempt SymPy evaluation if it is a simple expression string (e.g. "+2")
            try:
                return SymPyChecker.eval_arithmetic(cleaned)
            except Exception:
                return None

    @classmethod
    def connect_and_verify(
        cls,
        extraction: GeminiVisualEvidenceSchema,
        rule: Optional[QuestionRule] = None,
        manifest_category: str = "canonical_correct",
        model_id: str = "gemini-3.8-flash",
        latency_ms: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
        dry_run: bool = True,
    ) -> EvaluationCaseResult:
        """Runs deterministic mathematical verification on Gemini extracted visual evidence.

        Args:
            extraction: The structured visual extraction output from Gemini.
            rule: Target QuestionRule specification (defaults to Problem #1065658).
            manifest_category: The ground truth classification from the evaluation manifest.
            model_id: Model used for the evaluation.
            latency_ms: Inference roundtrip latency.
            input_tokens: Count of prompt + image tokens.
            output_tokens: Count of structured output tokens.
            estimated_cost_usd: Estimated cost of the inference call.
            dry_run: Whether this was a dry-run or live call.

        Returns:
            EvaluationCaseResult: Consolidated evaluation record.
        """
        active_rule = rule or get_canonical_problem_1065658_rule()

        # 1. Check for unreadable / degraded image quality or blocking ambiguity
        has_blocking_ambiguity = any(
            amb.severity == "blocking" for amb in extraction.ambiguities
        )
        is_unreadable = extraction.image_quality == ImageQualityAssessment.UNREADABLE

        # 2. Extract final answer safely
        parsed_final_ans = None
        if extraction.visible_final_answer.value is not None:
            parsed_final_ans = cls.parse_float_safe(extraction.visible_final_answer.value)

        # 3. Convert observed hops to deterministic NumberLineHop objects
        valid_hops: List[NumberLineHop] = []
        hop_conversion_failures = 0

        for idx, obs_hop in enumerate(extraction.number_line.observed_hops, 1):
            if obs_hop.start_value is not None and obs_hop.end_value is not None:
                # Map direction enum to literal
                dir_val: Literal["left", "right", "none"] = "none"
                if obs_hop.direction == HopDirection.RIGHT_POSITIVE:
                    dir_val = "right"
                elif obs_hop.direction == HopDirection.LEFT_NEGATIVE:
                    dir_val = "left"

                stated_mag = None
                if obs_hop.stated_magnitude_label:
                    stated_mag = cls.parse_float_safe(obs_hop.stated_magnitude_label)

                valid_hops.append(
                    NumberLineHop(
                        step_number=idx,
                        start=float(obs_hop.start_value),
                        end=float(obs_hop.end_value),
                        direction=dir_val,
                        stated_magnitude=stated_mag,
                    )
                )
            else:
                hop_conversion_failures += 1

        # 4. Handle cases where hops or response cannot be interpreted
        if (
            is_unreadable
            or has_blocking_ambiguity
            or (not valid_hops and not parsed_final_ans)
            or (hop_conversion_failures > 0 and parsed_final_ans is None)
        ):
            return EvaluationCaseResult(
                response_id=extraction.response_id,
                manifest_category=manifest_category,
                model_id=model_id,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimated_cost_usd,
                visual_extraction=extraction,
                verified_steps=[],
                math_verification_status="uninterpretable",
                teacher_escalation_correct=extraction.requires_teacher_review,
                schema_valid=True,
                dry_run=dry_run,
            )

        # 5. Run deterministic SymPy verification on valid hops
        verdict: MathVerificationVerdict = verify_student_math_reasoning(
            hops=valid_hops,
            final_answer=parsed_final_ans,
            rule=active_rule,
        )

        # 6. Format verified step comparisons
        verified_steps_comp: List[VerifiedStepComparison] = []
        for step in verdict.verified_steps:
            verified_steps_comp.append(
                VerifiedStepComparison(
                    step_number=step.step_number,
                    operation=f"{step.start_pos} -> {step.end_pos}",
                    expected_displacement=step.expected_displacement,
                    observed_displacement=step.observed_displacement,
                    is_mathematically_valid=step.is_correct,
                    evidence_citation=step.evidence_notes,
                    discrepancy_explanation=(
                        None
                        if step.is_correct
                        else f"Observed displacement {step.observed_displacement} != Expected {step.expected_displacement}"
                    ),
                )
            )

        # 7. Determine overall math status
        if verdict.is_reasoning_valid and verdict.is_final_answer_valid:
            math_status = "valid"
        elif not verdict.is_reasoning_valid or not verdict.is_final_answer_valid:
            math_status = "arithmetic_error"
        else:
            math_status = "cannot_determine"

        first_err_step = verdict.first_error_step
        first_err_type = verdict.first_error_taxonomy

        # 8. Check teacher escalation correctness
        # For ambiguous/incomplete responses or detected errors, requires_teacher_review should be true or flagged
        should_flag_review = (
            verdict.needs_teacher_review
            or has_blocking_ambiguity
            or manifest_category == "ambiguous_incomplete"
            or verdict.is_compensatory_error
        )
        teacher_escalation_correct = (
            extraction.requires_teacher_review == should_flag_review
            or extraction.requires_teacher_review  # Safe to over-escalate to human
        )

        return EvaluationCaseResult(
            response_id=extraction.response_id,
            manifest_category=manifest_category,
            model_id=model_id,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            visual_extraction=extraction,
            verified_steps=verified_steps_comp,
            math_verification_status=math_status,
            first_supported_error_step=first_err_step,
            first_supported_error_type=first_err_type,
            teacher_escalation_correct=teacher_escalation_correct,
            schema_valid=True,
            dry_run=dry_run,
        )
