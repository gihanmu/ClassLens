"""Fault-injection and adversarial testing for the Independent Critic Agent and SymPy Verifier (Gate 4C Checkpoint C).

Verifies:
1. Critic intercepts hallucinated steps (steps not grounded in physical observations).
2. Critic intercepts ungrounded misconceptions assigned on insufficient evidence.
3. Critic intercepts SymPy contradictions (reasoning claimed valid despite mathematical errors).
4. Critic caps unjustified high confidence and enforces teacher review.
5. MultiAgentPipeline enforces bounded reinterpretation (at most 1 retry pass).
6. SymPy arithmetic evaluator handles adversarial inputs without crashing.
7. Geometric number-line verifier handles malformed, discontinuous, and contradictory hops.
"""

from __future__ import annotations

import pytest

from services.worker.agents.contracts import (
    AnswerStatus,
    CriticAuditOutput,
    DiagnosticOutput,
    FirstSupportedError,
    QualityStatus,
    ReasoningStatus,
    VerifiedStep,
    VisualEvidenceOutput,
    VisualObservation,
)
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.tools import eval_sympy_arithmetic, validate_number_line_moves
from services.worker.math_verifier.contracts import NumberLineHop, QuestionRule
from services.worker.math_verifier.verifier import verify_student_math_reasoning


# ==============================================================================
# 1. Critic Fault Injection: Hallucinated Steps
# ==============================================================================

def test_critic_intercepts_hallucinated_steps():
    """Critic must reject diagnosis claiming more steps than physically drawn."""
    # 1 physical hop observed
    visual = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="number_line", value="Line", confidence=0.95),
            VisualObservation(
                kind="arrow_jump",
                value="Jump 0 to -6",
                confidence=0.95,
                start_pos=0.0,
                end_pos=-6.0,
                direction="left",
            ),
        ],
        has_number_line=True,
        final_answer_marked="2",
        confidence=0.95,
    )

    # Diagnosis hallucinates 3 complete steps
    diagnosis = DiagnosticOutput(
        answer_status=AnswerStatus.CORRECT,
        reasoning_status=ReasoningStatus.SUPPORTED_CORRECT,
        inferred_final_answer="2",
        verified_steps=[
            VerifiedStep(
                step_number=1,
                operation="Jump 0 to -6",
                expected_result=-6.0,
                observed_result=-6.0,
                is_correct=True,
                evidence_citation="Step 1",
            ),
            VerifiedStep(
                step_number=2,
                operation="Jump -6 to 6",
                expected_result=12.0,
                observed_result=12.0,
                is_correct=True,
                evidence_citation="Step 2 (Hallucinated)",
            ),
            VerifiedStep(
                step_number=3,
                operation="Jump 6 to 2",
                expected_result=-4.0,
                observed_result=-4.0,
                is_correct=True,
                evidence_citation="Step 3 (Hallucinated)",
            ),
        ],
        confidence=0.95,
        evidence_sufficiency="sufficient",
        diagnostic_explanation="All steps verified.",
    )

    audit = MockAgentAdapter.get_critic_audit(visual=visual, diagnosis=diagnosis)

    assert audit.approved is False
    assert audit.contradiction_detected is True
    assert audit.evidence_grounded is False
    assert audit.audit_verdict == "audit_rejected"
    assert audit.requires_teacher_review is True
    assert any("Hallucinated" in note for note in audit.discrepancy_notes)


# ==============================================================================
# 2. Critic Fault Injection: Ungrounded Misconceptions
# ==============================================================================

def test_critic_intercepts_ungrounded_misconception_on_insufficient_evidence():
    """Critic must reject diagnosis claiming a specific misconception on insufficient evidence."""
    visual = VisualEvidenceOutput(
        quality_status=QualityStatus.FAINT_READABLE,
        observations=[
            VisualObservation(kind="number_line", value="Faint line", confidence=0.60),
            VisualObservation(
                kind="arrow_jump",
                value="Faint incomplete stroke",
                confidence=0.40,
                start_pos=0.0,
                end_pos=None,
                direction="none",
            ),
        ],
        has_number_line=True,
        final_answer_marked=None,
        confidence=0.55,
    )

    diagnosis = DiagnosticOutput(
        answer_status=AnswerStatus.UNDETERMINED,
        reasoning_status=ReasoningStatus.SUPPORTED_ERROR,
        inferred_final_answer=None,
        verified_steps=[],
        first_supported_error=FirstSupportedError(
            step_number=1,
            error_type="directional_sign",
            observed_behavior="Deviation",
            expected_behavior="Expected -6",
            explanation="Hallucinated reversal",
        ),
        misconception_taxonomy_id="MISC-NUM-DIR-REVERSE",
        confidence=0.85,
        evidence_sufficiency="insufficient",
        diagnostic_explanation="Student reversed direction.",
    )

    audit = MockAgentAdapter.get_critic_audit(visual=visual, diagnosis=diagnosis)

    assert audit.approved is False
    assert audit.contradiction_detected is True
    assert audit.audit_verdict == "audit_rejected"
    assert audit.requires_teacher_review is True
    assert any("insufficient visual evidence" in note for note in audit.discrepancy_notes)


# ==============================================================================
# 3. Critic Fault Injection: SymPy Mathematical Contradiction
# ==============================================================================

def test_critic_intercepts_supported_correct_contradicting_invalid_steps():
    """Critic must reject diagnosis asserting supported_correct when verified steps contain errors."""
    visual = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="number_line", value="Line", confidence=0.98),
            VisualObservation(kind="arrow_jump", value="Jump 0 to -6", confidence=0.95, start_pos=0.0, end_pos=-6.0, direction="left"),
            VisualObservation(kind="arrow_jump", value="Jump -6 to 5", confidence=0.95, start_pos=-6.0, end_pos=5.0, direction="right"),
        ],
        has_number_line=True,
        final_answer_marked="2",
        confidence=0.95,
    )

    # Contradictory diagnosis: claims SUPPORTED_CORRECT despite Step 2 being incorrect
    diagnosis = DiagnosticOutput(
        answer_status=AnswerStatus.CORRECT,
        reasoning_status=ReasoningStatus.SUPPORTED_CORRECT,  # Contradiction!
        inferred_final_answer="2",
        verified_steps=[
            VerifiedStep(step_number=1, operation="0 to -6", expected_result=-6.0, observed_result=-6.0, is_correct=True, evidence_citation="Step 1"),
            VerifiedStep(step_number=2, operation="-6 to 5", expected_result=12.0, observed_result=11.0, is_correct=False, evidence_citation="Step 2"),
        ],
        confidence=0.95,
        evidence_sufficiency="sufficient",
        diagnostic_explanation="Student reasoning is correct.",
    )

    audit = MockAgentAdapter.get_critic_audit(visual=visual, diagnosis=diagnosis)

    assert audit.approved is False
    assert audit.contradiction_detected is True
    assert audit.audit_verdict == "audit_rejected"
    assert audit.requires_teacher_review is True
    assert any("mathematical deviations" in note for note in audit.discrepancy_notes)


# ==============================================================================
# 4. Critic Fault Injection: Unjustified High Confidence & Review Enforcement
# ==============================================================================

def test_critic_enforces_teacher_review_on_compensatory_error():
    """Critic must flag review_required when compensatory error occurs."""
    visual = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="number_line", value="Line", confidence=0.95),
            VisualObservation(kind="arrow_jump", value="0 to -6", confidence=0.95, start_pos=0.0, end_pos=-6.0, direction="left"),
            VisualObservation(kind="arrow_jump", value="-6 to 5", confidence=0.95, start_pos=-6.0, end_pos=5.0, direction="right"),
            VisualObservation(kind="arrow_jump", value="5 to 2", confidence=0.95, start_pos=5.0, end_pos=2.0, direction="left"),
        ],
        has_number_line=True,
        final_answer_marked="2",
        confidence=0.95,
    )

    diagnosis = DiagnosticOutput(
        answer_status=AnswerStatus.CORRECT,
        reasoning_status=ReasoningStatus.SUPPORTED_ERROR,
        inferred_final_answer="2",
        verified_steps=[
            VerifiedStep(step_number=1, operation="0 to -6", expected_result=-6.0, observed_result=-6.0, is_correct=True, evidence_citation="Step 1"),
            VerifiedStep(step_number=2, operation="-6 to 5", expected_result=12.0, observed_result=11.0, is_correct=False, evidence_citation="Step 2"),
            VerifiedStep(step_number=3, operation="5 to 2", expected_result=-4.0, observed_result=-3.0, is_correct=False, evidence_citation="Step 3"),
        ],
        is_compensatory_error=True,
        confidence=0.95,
        evidence_sufficiency="sufficient",
    )

    audit = MockAgentAdapter.get_critic_audit(visual=visual, diagnosis=diagnosis)

    assert audit.requires_teacher_review is True
    assert audit.audit_verdict == "review_required"
    assert audit.confidence <= 0.65  # Heuristic confidence cap applied


# ==============================================================================
# 5. MultiAgentPipeline: Bounded Reinterpretation (At Most 1 Retry Pass)
# ==============================================================================

def test_pipeline_bounded_reinterpretation_executes_single_retry():
    """Pipeline reinterpretation triggers at most 1 pass and terminates cleanly."""
    analysis = MultiAgentPipeline.analyze_response(
        response_id="case_01_canonical_correct",
        force_critic_retry=True,
    )

    # After pass 1 contradiction, pass 2 re-evaluates and clears contradiction
    assert analysis.critic_audit.critic_attempt_number == 2
    assert analysis.critic_audit.approved is True
    assert analysis.critic_audit.reinterpretation_needed is False
    assert analysis.answer_status == AnswerStatus.CORRECT
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT


# ==============================================================================
# 6. SymPy Arithmetic Verifier: Adversarial Input Resilience
# ==============================================================================

def test_eval_sympy_arithmetic_handles_adversarial_inputs():
    """SymPy rational evaluator must safely return error dictionaries for hostile expressions."""
    # 1. Division by zero
    res_zero = eval_sympy_arithmetic("12 / 0")
    assert res_zero["success"] is False
    assert res_zero["error"] is not None

    # 2. Algebraic symbols injected
    res_algebraic = eval_sympy_arithmetic("2 * x + 5")
    assert res_algebraic["success"] is False
    assert "algebraic symbols" in res_algebraic["error"].lower()

    # 3. Python syntax / code injection attempt
    res_injection = eval_sympy_arithmetic("__import__('os').system('ls')")
    assert res_injection["success"] is False
    assert res_injection["computed_value"] is None

    # 4. Malformed syntax
    res_syntax = eval_sympy_arithmetic("++--4")
    # Even if parser fails, it does not raise uncaught exception
    assert isinstance(res_syntax, dict)


# ==============================================================================
# 7. Geometric Verifier: Discontinuous and Contradictory Hops
# ==============================================================================

def test_validate_number_line_moves_handles_adversarial_geometry():
    """Geometry verifier must classify discontinuous and contradictory paths deterministically."""
    # Discontinuous path: hop 1 ends at -6, hop 2 starts at 10 (gap of 16 units)
    moves_discontinuous = [
        {"step_number": 1, "start": 0.0, "end": -6.0, "direction": "left"},
        {"step_number": 2, "start": 10.0, "end": 22.0, "direction": "right"},
    ]
    verdict_disc = validate_number_line_moves(start=0.0, moves=moves_discontinuous)
    assert verdict_disc["is_reasoning_valid"] is False
    assert verdict_disc["first_error_taxonomy"] in ("REASONING_DISCONTINUOUS", "MISC-ARITH-SLIP", "MISC-NUM-DIR-REVERSE")

    # Contradictory arrow direction vs coordinate movement:
    # Drawn coordinate moves right (0 to 6), but arrow head is pointed 'left'
    moves_contradictory = [
        {"step_number": 1, "start": 0.0, "end": 6.0, "direction": "left"},  # Contradiction!
    ]
    verdict_contra = validate_number_line_moves(start=0.0, moves=moves_contradictory)
    assert verdict_contra["is_reasoning_valid"] is False
    assert verdict_contra["verified_steps"][0]["verification_status"] == "verified_error"
