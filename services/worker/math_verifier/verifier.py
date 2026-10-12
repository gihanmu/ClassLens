"""Main entrypoint coordinating deterministic mathematical and geometric verification."""

from __future__ import annotations

from typing import List, Optional

from services.worker.math_verifier.contracts import (
    MathVerificationVerdict,
    NumberLineHop,
    QuestionRule,
    StepVerificationResult,
)
from services.worker.math_verifier.method_matcher import MethodMatcher
from services.worker.math_verifier.number_line_geometry import (
    NumberLineDisplacementCalculator,
)
from services.worker.math_verifier.sympy_checker import SymPyChecker
from services.worker.math_verifier.taxonomy_mapper import TaxonomyMapper


def verify_student_math_reasoning(
    hops: List[NumberLineHop],
    final_answer: Optional[float],
    rule: QuestionRule,
) -> MathVerificationVerdict:
    """Verifies student number line reasoning and final answer deterministically.

    Decouples final answer validity from reasoning step validity and detects
    compensatory errors, method variations, and specific error taxonomies.

    Args:
        hops: Ordered sequence of observed NumberLineHop objects.
        final_answer: Student's explicit final written answer, or None if omitted/inferred.
        rule: Question specification containing target expression and rules.

    Returns:
        MathVerificationVerdict containing complete evaluation breakdown.
    """
    # 1. Determine exact target value via SymPy if not explicitly configured
    if rule.target_value is not None:
        target_value = float(rule.target_value)
    else:
        target_value = SymPyChecker.eval_arithmetic(rule.expression)

    tolerance = rule.tolerance

    # 2. Handle empty reasoning (Row 11 / Row 12 cases)
    if not hops:
        is_ans_valid = False
        needs_review = False
        review_reason = None
        confidence = 0.9

        if final_answer is not None:
            is_ans_valid = abs(final_answer - target_value) <= tolerance
            needs_review = True
            review_reason = "Final answer present but no mathematical working or number line hops observed."
        else:
            needs_review = True
            review_reason = "No mathematical working, arrows, or final answer visible on student response."
            confidence = 0.5

        return MathVerificationVerdict(
            is_reasoning_valid=False,
            is_final_answer_valid=is_ans_valid,
            detected_method="unrecognized",
            starting_point=None,
            terminal_position=None,
            verified_steps=[],
            first_error_step=None,
            first_error_taxonomy="REASONING_INCOMPLETE",
            is_compensatory_error=False,
            needs_teacher_review=needs_review,
            teacher_review_reason=review_reason,
            confidence=confidence,
        )

    # 3. Analyze geometry: start, end, continuity, and direction consistency
    starting_point = hops[0].start
    terminal_position = hops[-1].end

    is_continuous, discontinuities = NumberLineDisplacementCalculator.check_path_continuity(
        hops, tolerance
    )

    # 4. Pedagogical method matching
    matched = MethodMatcher.match(hops, rule)

    # 5. Step-by-step verification against matched expected displacements
    verified_steps: List[StepVerificationResult] = []
    first_err_step: Optional[int] = None
    first_err_tax: Optional[str] = None

    has_insufficient_evidence = any(h.evidence_status == "insufficient_evidence" for h in hops)
    has_partial_evidence = any(h.evidence_status == "partially_supported" for h in hops)

    # Check if starting point itself deviated from expected starting point
    start_point_valid = True
    if matched.expected_start is not None and abs(starting_point - matched.expected_start) > tolerance:
        start_point_valid = False

    for i, hop in enumerate(hops):
        step_num = hop.step_number
        obs_disp = hop.displacement
        direction_consistent = NumberLineDisplacementCalculator.check_direction_consistency(hop)

        if i < len(matched.expected_displacements):
            exp_disp = matched.expected_displacements[i]
        else:
            exp_disp = 0.0

        dev = obs_disp - exp_disp
        step_tax: Optional[str] = None

        if hop.evidence_status == "insufficient_evidence":
            step_correct = False
            v_status: Literal["verified_valid", "verified_error", "unverifiable"] = "unverifiable"
            ev_status: Literal["supported", "partially_supported", "insufficient_evidence"] = "insufficient_evidence"
            notes = f"Step {step_num} unverifiable: insufficient visual evidence (missing coordinate, missing arrowhead, or faint mark)."
        else:
            ev_status = hop.evidence_status
            step_correct = (abs(dev) <= tolerance) and direction_consistent

            # If this is step 1 and the start point was wrong, mark step 1 incorrect
            if i == 0 and not start_point_valid:
                step_correct = False

            if not step_correct:
                v_status = "verified_error"
                if not direction_consistent:
                    step_tax, notes = TaxonomyMapper.classify_contradiction(
                        step_num, hop.direction, obs_disp
                    )
                elif i == 0 and not start_point_valid and abs(obs_disp - exp_disp) <= tolerance:
                    step_tax = "MISC-NUM-DIR-REVERSE" if (starting_point * exp_disp < 0) else "MISC-ARITH-SLIP"
                    notes = f"Incorrect starting point: started at {starting_point:g} instead of {matched.expected_start:g}."
                else:
                    step_tax, notes = TaxonomyMapper.classify_step_deviation(
                        expected_displacement=exp_disp,
                        observed_displacement=obs_disp,
                        stated_magnitude=hop.stated_magnitude,
                        tolerance=tolerance,
                    )

                if first_err_step is None and step_tax is not None:
                    first_err_step = step_num
                    first_err_tax = step_tax
            else:
                v_status = "verified_valid"
                notes = f"Step {step_num} valid: hopped from {hop.start:g} to {hop.end:g} (Δ={obs_disp:+g})."

        verified_steps.append(
            StepVerificationResult(
                step_number=step_num,
                start_pos=hop.start,
                end_pos=hop.end,
                expected_displacement=exp_disp,
                observed_displacement=obs_disp,
                is_correct=step_correct,
                deviation=dev,
                error_taxonomy=step_tax,
                evidence_notes=notes,
                evidence_status=ev_status,
                verification_status=v_status,
            )
        )

    # Check for path continuity errors (only if evidence was sufficient)
    if not is_continuous and first_err_step is None and discontinuities and not has_insufficient_evidence:
        first_err_step = discontinuities[0]
        first_err_tax = "REASONING_DISCONTINUOUS"

    # Check for incomplete path (fewer hops than expected, only if evidence was sufficient)
    if len(hops) < len(matched.expected_displacements) and first_err_step is None and not has_insufficient_evidence:
        first_err_step = len(hops) + 1
        first_err_tax = "REASONING_INCOMPLETE"

    # 6. Reasoning validity
    is_reasoning_valid = (
        not has_insufficient_evidence
        and all(s.is_correct for s in verified_steps)
        and (len(hops) >= len(matched.expected_displacements))
        and is_continuous
        and start_point_valid
        and (matched.method_name not in ("unrecognized", "insufficient_evidence"))
    )

    # 7. Final answer validity
    if final_answer is not None:
        is_final_answer_valid = abs(final_answer - target_value) <= tolerance
    elif not has_insufficient_evidence and is_reasoning_valid:
        # Inferred from terminal position only if reasoning is valid without missing hops
        is_final_answer_valid = abs(terminal_position - target_value) <= tolerance
    else:
        is_final_answer_valid = False

    # 8. Compensatory error check:
    # Arrived at correct target despite flawed or erroneous intermediate reasoning
    is_compensatory_error = False
    if not is_reasoning_valid and not has_insufficient_evidence and first_err_tax is not None and (
        abs(terminal_position - target_value) <= tolerance
        or (final_answer is not None and abs(final_answer - target_value) <= tolerance)
    ):
        is_compensatory_error = True

    # 9. Routing for educator review & confidence calculation
    needs_teacher_review = False
    teacher_review_reason: Optional[str] = None
    confidence = 1.0

    if has_insufficient_evidence or matched.method_name in ("unrecognized", "insufficient_evidence"):
        needs_teacher_review = True
        teacher_review_reason = "Visual evidence is incomplete or ambiguous; educator review required to interpret student work."
        confidence = 0.60
    elif is_compensatory_error:
        needs_teacher_review = True
        teacher_review_reason = (
            "Compensatory error detected: student arrived at correct target "
            "despite mathematical errors in intermediate number line hops."
        )
        confidence = 0.95
    elif not is_reasoning_valid and is_final_answer_valid:
        needs_teacher_review = True
        teacher_review_reason = "Final answer matches target but number line working contains deviations."
        confidence = 0.90
    elif is_reasoning_valid and not is_final_answer_valid:
        # Step reasoning was completely correct, but circled/marked final answer was wrong (Row 6)
        confidence = 0.95

    overall_sufficiency = (
        "insufficient"
        if has_insufficient_evidence
        else ("partial" if has_partial_evidence else "sufficient")
    )

    return MathVerificationVerdict(
        is_reasoning_valid=is_reasoning_valid,
        is_final_answer_valid=is_final_answer_valid,
        detected_method=matched.method_name,
        starting_point=starting_point,
        terminal_position=terminal_position,
        evidence_sufficiency=overall_sufficiency,
        verified_steps=verified_steps,
        first_error_step=first_err_step,
        first_error_taxonomy=first_err_tax,
        is_compensatory_error=is_compensatory_error,
        needs_teacher_review=needs_teacher_review,
        teacher_review_reason=teacher_review_reason,
        confidence=confidence,
    )
