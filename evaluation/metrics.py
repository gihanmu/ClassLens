"""Metric calculation logic for ClassLens Gate 4C evaluation harness.

Each metric strictly specifies:
- Numerator
- Denominator
- Inclusion / Exclusion criteria
- Semantic definition
"""

from __future__ import annotations

from typing import List, Optional
from evaluation.schemas import (
    BenchmarkCase,
    CaseEvaluationResult,
    EvaluationMetricsSummary,
    MetricFraction,
)


def _calc_fraction(
    name: str,
    num: int,
    den: int,
    desc: str,
    threshold: Optional[float] = None,
) -> MetricFraction:
    if den == 0:
        return MetricFraction(
            name=name,
            numerator=num,
            denominator=den,
            percentage=None,
            display_value="N/A",
            description=desc,
            target_threshold_pct=threshold,
            status="N/A",
        )
    pct = round((num / den) * 100, 1)
    status = "PASS"
    if threshold is not None:
        status = "PASS" if pct >= threshold else "FAIL"

    return MetricFraction(
        name=name,
        numerator=num,
        denominator=den,
        percentage=pct,
        display_value=f"{num}/{den} ({pct}%)",
        description=desc,
        target_threshold_pct=threshold,
        status=status,
    )


def compute_evaluation_metrics(
    cases: List[BenchmarkCase],
    results: List[CaseEvaluationResult],
    total_eval_duration_sec: float,
) -> EvaluationMetricsSummary:
    """Computes comprehensive metrics across categories A through G."""
    case_map = {c.case_id: c for c in cases}
    total_cases = len(results)

    # A. Mathematical Outcome Accuracy
    ans_status_correct = sum(1 for r in results if r.answer_status_match)
    answer_status_accuracy = _calc_fraction(
        name="Answer Status Accuracy",
        num=ans_status_correct,
        den=total_cases,
        desc="Proportion of cases where predicted AnswerStatus (correct/incorrect/undetermined) matches ground truth.",
        threshold=90.0,
    )

    # Final answer agreement: evaluated on cases with an observable final answer
    observable_cases = [r for r in results if case_map[r.case_id].expected_answer is not None]
    final_ans_agreed = sum(1 for r in observable_cases if r.final_answer_match)
    final_answer_agreement = _calc_fraction(
        name="Final Answer Agreement",
        num=final_ans_agreed,
        den=len(observable_cases),
        desc="Agreement between inferred final answer and ground truth for cases with observable answers.",
        threshold=90.0,
    )

    # B. Reasoning Verification Accuracy
    reasoning_correct = sum(1 for r in results if r.reasoning_status_match)
    reasoning_status_accuracy = _calc_fraction(
        name="Reasoning Status Accuracy",
        num=reasoning_correct,
        den=total_cases,
        desc="Proportion of cases where predicted ReasoningStatus matches ground truth.",
        threshold=85.0,
    )

    error_gt_cases = [
        r for r in results
        if case_map[r.case_id].expected_reasoning_status == "supported_error"
    ]
    error_detected = sum(
        1 for r in error_gt_cases
        if r.actual_values.get("reasoning_status") == "supported_error"
    )
    procedural_error_detection_recall = _calc_fraction(
        name="Procedural Error Detection Recall",
        num=error_detected,
        den=len(error_gt_cases),
        desc="Sensitivity in detecting genuine procedural reasoning errors.",
        threshold=90.0,
    )

    localized_cases = [
        r for r in results
        if case_map[r.case_id].expected_error_step_index is not None
    ]
    step_localized = sum(1 for r in localized_cases if r.error_step_match)
    error_step_localization_accuracy = _calc_fraction(
        name="Error-Step Localization Accuracy",
        num=step_localized,
        den=len(localized_cases),
        desc="Accuracy in pinpointing the earliest flawed intermediate hop.",
        threshold=80.0,
    )

    # C. Misconception Detection
    # C. Misconception Detection (excluding structural REASONING_INCOMPLETE)
    predicted_misc_cases = [
        r for r in results
        if r.actual_values.get("misconception_id") is not None
        and r.actual_values.get("misconception_id") != "REASONING_INCOMPLETE"
    ]
    misc_true_positives = sum(
        1 for r in predicted_misc_cases
        if r.misconception_match and case_map[r.case_id].expected_misconception_id is not None
    )
    misconception_precision = _calc_fraction(
        name="Misconception Detection Precision",
        num=misc_true_positives,
        den=len(predicted_misc_cases),
        desc="Precision of assigned misconception taxonomy IDs against ground truth.",
        threshold=85.0,
    )

    gt_misc_cases = [
        r for r in results
        if case_map[r.case_id].expected_misconception_id is not None
        and case_map[r.case_id].expected_misconception_id != "REASONING_INCOMPLETE"
    ]
    misc_recalled = sum(1 for r in gt_misc_cases if r.misconception_match)
    misconception_recall = _calc_fraction(
        name="Misconception Detection Recall",
        num=misc_recalled,
        den=len(gt_misc_cases),
        desc="Recall in surfacing known procedural misconceptions.",
        threshold=85.0,
    )

    exact_misc_matches = sum(1 for r in results if r.misconception_match)
    exact_taxonomy_match_rate = _calc_fraction(
        name="Exact Taxonomy Match Rate",
        num=exact_misc_matches,
        den=total_cases,
        desc="Proportion of cases where assigned misconception (including None) exactly matches expectation.",
        threshold=85.0,
    )

    no_misc_gt_cases = [
        r for r in results
        if case_map[r.case_id].expected_misconception_id is None
    ]
    false_misc_assigned = sum(
        1 for r in no_misc_gt_cases
        if r.actual_values.get("misconception_id") is not None
        and r.actual_values.get("misconception_id") != "REASONING_INCOMPLETE"
    )
    fp_pct = round((false_misc_assigned / len(no_misc_gt_cases)) * 100, 1) if no_misc_gt_cases else 0.0
    false_positive_misconception_rate = MetricFraction(
        name="False-Positive Misconception Rate",
        numerator=false_misc_assigned,
        denominator=len(no_misc_gt_cases),
        percentage=fp_pct,
        display_value=f"{false_misc_assigned}/{len(no_misc_gt_cases)} ({fp_pct}%)",
        description="Rate of hallucinated/unsupported misconception assignments on sound or ambiguous work.",
        target_threshold_pct=0.0,
        status="PASS" if false_misc_assigned == 0 else "FAIL",
    )

    # D. Evidence Grounding & Abstention
    ev_suff_correct = sum(1 for r in results if r.evidence_sufficiency_match)
    evidence_sufficiency_accuracy = _calc_fraction(
        name="Evidence Sufficiency Accuracy",
        num=ev_suff_correct,
        den=total_cases,
        desc="Correct classification of evidence sufficiency (sufficient / partial / insufficient).",
        threshold=90.0,
    )

    insufficient_cases = [
        r for r in results
        if case_map[r.case_id].expected_evidence_sufficiency == "insufficient"
    ]
    abstained = sum(
        1 for r in insufficient_cases
        if (
            r.actual_values.get("misconception_id") is None
            or r.actual_values.get("misconception_id") == "REASONING_INCOMPLETE"
        )
        and r.actual_values.get("evidence_sufficiency") == "insufficient"
    )
    appropriate_abstention_rate = _calc_fraction(
        name="Appropriate Abstention Rate",
        num=abstained,
        den=len(insufficient_cases),
        desc="Rate at which the pipeline refrains from claiming misconceptions on ambiguous/faint work.",
        threshold=100.0,
    )

    unsupported_claims = sum(1 for r in results if r.unsupported_claim_detected)
    unsupported_claim_rate = _calc_fraction(
        name="Unsupported Claim Rate",
        num=unsupported_claims,
        den=total_cases,
        desc="Frequency of diagnostic assertions without visible ink justification.",
        threshold=0.0,
    )

    contradictions = sum(1 for r in results if r.contradiction_detected)
    contradiction_rate = _calc_fraction(
        name="Contradiction Rate",
        num=contradictions,
        den=total_cases,
        desc="Frequency of pipeline conclusions contradicting SymPy verified mathematical facts.",
        threshold=0.0,
    )

    # E. Teacher Review Routing
    flagged_review_cases = [
        r for r in results
        if r.actual_values.get("requires_teacher_review") is True
    ]
    review_true_positives = sum(
        1 for r in flagged_review_cases
        if case_map[r.case_id].expected_requires_teacher_review is True
    )
    review_routing_precision = _calc_fraction(
        name="Review Routing Precision",
        num=review_true_positives,
        den=len(flagged_review_cases),
        desc="Proportion of teacher escalation flags that genuinely warrant manual inspection.",
        threshold=80.0,
    )

    gt_review_cases = [
        r for r in results
        if case_map[r.case_id].expected_requires_teacher_review is True
    ]
    review_recalled = sum(
        1 for r in gt_review_cases
        if r.actual_values.get("requires_teacher_review") is True
    )
    review_routing_recall = _calc_fraction(
        name="Review Routing Recall",
        num=review_recalled,
        den=len(gt_review_cases),
        desc="Sensitivity in escalating ambiguous or compensatory cases to the educator.",
        threshold=95.0,
    )
    missed_critical = len(gt_review_cases) - review_recalled

    # F. Critic Effectiveness
    critic_matches = sum(1 for r in results if r.critic_verdict_match)
    critic_verdict_accuracy = _calc_fraction(
        name="Critic Verdict Accuracy",
        num=critic_matches,
        den=total_cases,
        desc="Agreement between Independent Critic verdict and expected audit verdict.",
        threshold=85.0,
    )

    critic_challenge_cases = [
        r for r in results
        if r.actual_values.get("critic_verdict") == "review_required"
    ]
    critic_challenge_correct = sum(
        1 for r in critic_challenge_cases
        if case_map[r.case_id].expected_requires_teacher_review is True
    )
    critic_challenge_precision = _calc_fraction(
        name="Critic Challenge Precision",
        num=critic_challenge_correct,
        den=len(critic_challenge_cases),
        desc="Precision of adversarial critic challenges in identifying genuine uncertainties.",
        threshold=80.0,
    )

    avg_latency = round((total_eval_duration_sec / max(total_cases, 1)) * 1000, 1)

    return EvaluationMetricsSummary(
        answer_status_accuracy=answer_status_accuracy,
        final_answer_agreement=final_answer_agreement,
        reasoning_status_accuracy=reasoning_status_accuracy,
        procedural_error_detection_recall=procedural_error_detection_recall,
        error_step_localization_accuracy=error_step_localization_accuracy,
        misconception_precision=misconception_precision,
        misconception_recall=misconception_recall,
        exact_taxonomy_match_rate=exact_taxonomy_match_rate,
        false_positive_misconception_rate=false_positive_misconception_rate,
        evidence_sufficiency_accuracy=evidence_sufficiency_accuracy,
        appropriate_abstention_rate=appropriate_abstention_rate,
        unsupported_claim_rate=unsupported_claim_rate,
        contradiction_rate=contradiction_rate,
        review_routing_precision=review_routing_precision,
        review_routing_recall=review_routing_recall,
        missed_critical_review_count=missed_critical,
        critic_verdict_accuracy=critic_verdict_accuracy,
        critic_challenge_precision=critic_challenge_precision,
        avg_latency_ms=avg_latency,
        total_eval_duration_sec=round(total_eval_duration_sec, 2),
    )
