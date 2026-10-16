"""Unit tests for TaskRouter, FractionDivisionVerifier, and MultiAgentPipeline stage logs."""

from __future__ import annotations

import pytest

from services.worker.agents.contracts import (
    AnswerStatus,
    QualityStatus,
    ReasoningStatus,
    VisualEvidenceOutput,
    VisualObservation,
)
from services.worker.agents.evidence_sufficiency import EvidenceSufficiencyEvaluator
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.math_verifier.fraction_verifier import FractionDivisionVerifier
from services.worker.math_verifier.task_router import TaskRouter, TaskType


def test_task_router_detection():
    """Verifies that TaskRouter routes topics, formulas, and prompt texts accurately."""
    # Fraction division detection
    assert TaskRouter.resolve_task(math_topic="Division of Fractions") == TaskType.FRACTION_DIVISION
    assert TaskRouter.resolve_task(math_topic="Fraction Division — Unit Form and Visual Models") == TaskType.FRACTION_DIVISION
    assert TaskRouter.resolve_task(question_text="A) Rewrite 8/9 ÷ 4/9 in unit form. B) Draw a model.") == TaskType.FRACTION_DIVISION
    assert TaskRouter.resolve_task(latex_formula="(8/9) / (4/9)") == TaskType.FRACTION_DIVISION
    assert TaskRouter.resolve_task(problem_reference_id="1425504") == TaskType.FRACTION_DIVISION
    assert TaskRouter.resolve_task(problem_reference_id="e921e6") == TaskType.FRACTION_DIVISION

    # Integer number line detection
    assert TaskRouter.resolve_task(math_topic="Integer operations on number lines") == TaskType.INTEGER_NUMBER_LINE
    assert TaskRouter.resolve_task(question_text="Represent -6 + 12 - 4 on the horizontal number line") == TaskType.INTEGER_NUMBER_LINE
    assert TaskRouter.resolve_task(latex_formula="-6 + 12 - 4") == TaskType.INTEGER_NUMBER_LINE
    assert TaskRouter.resolve_task(problem_reference_id="1065658") == TaskType.INTEGER_NUMBER_LINE

    # Unsupported task fallback
    assert TaskRouter.resolve_task(math_topic="Trigonometric Functions", latex_formula=r"\sin(x)") == TaskType.UNSUPPORTED_TASK


def test_fraction_evidence_sufficiency_evaluation():
    """Verifies evidence sufficiency for fraction division with tape diagrams."""
    # Tape diagram present
    vis_tape = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="text_label", value="Tape diagram divided into 9 sections, 8 shaded, 2 groups of 4/9 labeled 1 and 2", confidence=0.95),
            VisualObservation(kind="circled_result", value="2", confidence=0.95),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.95,
        provenance="test_fixture",
    )
    suff_tape = EvidenceSufficiencyEvaluator.evaluate(vis_tape, task_type="fraction_division")
    assert suff_tape.overall_sufficiency == "sufficient"
    assert suff_tape.can_evaluate_reasoning is True
    assert suff_tape.can_diagnose_misconception is True

    # Final answer only
    vis_ans_only = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="circled_result", value="2", confidence=0.95),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.95,
        provenance="test_fixture",
    )
    suff_ans_only = EvidenceSufficiencyEvaluator.evaluate(vis_ans_only, task_type="fraction_division")
    assert suff_ans_only.overall_sufficiency == "partial"
    assert suff_ans_only.can_evaluate_reasoning is True

    # Unreadable image
    vis_unreadable = VisualEvidenceOutput(
        quality_status=QualityStatus.UNREADABLE,
        observations=[],
        has_number_line=False,
        final_answer_marked=None,
        confidence=0.20,
        provenance="test_fixture",
    )
    suff_unreadable = EvidenceSufficiencyEvaluator.evaluate(vis_unreadable, task_type="fraction_division")
    assert suff_unreadable.overall_sufficiency == "insufficient"
    assert suff_unreadable.can_evaluate_reasoning is False


def test_fraction_division_verifier_canonical():
    """Verifies canonical correct solution with tape diagram model."""
    vis = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="text_label", value="Partitioned tape diagram with 9 equal pieces, 8 shaded, two groups of 4/9 labeled 1 and 2", confidence=0.95),
            VisualObservation(kind="circled_result", value="2", confidence=0.95),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.95,
        provenance="test_fixture",
    )

    verdict = FractionDivisionVerifier.verify(vis, rule_expr="(8/9) / (4/9)", target_value=2.0)
    assert verdict.is_reasoning_valid is True
    assert verdict.is_final_answer_valid is True
    assert verdict.detected_method == "tape_diagram_grouping"
    assert verdict.is_compensatory_error is False
    assert len(verdict.verified_steps) == 3
    assert all(s.is_correct for s in verdict.verified_steps)


def test_fraction_division_verifier_group_size_misconception():
    """Verifies detection of FRAC-DIV-WRONG-GROUP-SIZE misconception (Student grouped by 2/9 instead of 4/9)."""
    vis = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(
                kind="text_label",
                value="Student has drawn a tape diagram divided into 9 pieces, shaded 8, and groups two ninths together four times",
                confidence=0.92,
            ),
            VisualObservation(kind="circled_result", value="2", confidence=0.90),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.90,
        provenance="test_fixture",
    )

    verdict = FractionDivisionVerifier.verify(vis, rule_expr="(8/9) / (4/9)", target_value=2.0)
    assert verdict.is_reasoning_valid is False
    assert verdict.first_error_taxonomy == "FRAC-DIV-WRONG-GROUP-SIZE"
    assert verdict.is_compensatory_error is True  # Final answer was 2 despite 4 groups of 2/9
    assert verdict.first_supported_error is not None
    assert verdict.first_supported_error.step_number == 2


def test_fraction_division_verifier_invert_and_multiply():
    """Verifies algorithmic solution using invert and multiply."""
    vis = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="text_label", value="Student writes 8/9 divided by 4/9 equals 8/9 multiplied by 9/4 equal to 8/4 = 2", confidence=0.95),
            VisualObservation(kind="circled_result", value="2", confidence=0.95),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.95,
        provenance="test_fixture",
    )

    verdict = FractionDivisionVerifier.verify(vis, rule_expr="(8/9) / (4/9)", target_value=2.0)
    assert verdict.is_reasoning_valid is True
    assert verdict.is_final_answer_valid is True
    assert verdict.detected_method == "invert_and_multiply"


def test_pipeline_fraction_division_end_to_end_with_stage_logs():
    """Verifies full MultiAgentPipeline execution with task routing and stage logs."""
    vis = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="text_label", value="Student drew a tape diagram with 9 sections, 8 shaded, and two groups of 4/9 labeled 1 and 2", confidence=0.95),
            VisualObservation(kind="circled_result", value="2", confidence=0.95),
        ],
        has_number_line=False,
        final_answer_marked="2",
        confidence=0.95,
        provenance="test_synthetic_tape",
    )

    analysis = MultiAgentPipeline.analyze_response(
        response_id="test_resp_frac_01",
        rule_expr="(8/9) / (4/9)",
        target_value=2.0,
        math_topic="Division of Fractions",
        question_text="A) Rewrite 8/9 ÷ 4/9 in unit form. B) Find the quotient. C) Draw a model to support your answer.",
        cached_visual_evidence=vis,
    )

    # Correctness and reasoning assertions
    assert analysis.answer_status == AnswerStatus.CORRECT
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
    assert analysis.needs_teacher_review is False
    assert analysis.is_compensatory_error is False

    # Stage logs assertions
    assert len(analysis.stage_logs) == 5
    stages = [log["stage"] for log in analysis.stage_logs]
    assert stages == ["visual_evidence", "task_routing", "math_interpretation", "diagnostic_agent", "critic_audit"]

    # Verify task routing log
    routing_log = analysis.stage_logs[1]
    assert routing_log["task_type"] == "fraction_division"
    assert routing_log["status"] == "completed"

    # Verify critic audit log
    critic_log = analysis.stage_logs[4]
    assert critic_log["status"] == "completed"
    assert analysis.critic_audit.approved is True
