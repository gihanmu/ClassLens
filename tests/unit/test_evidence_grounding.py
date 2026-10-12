"""Offline regression tests for Gate 4A.2: Evidence-Grounded Diagnosis & Uncertainty Handling.

Validates the Core Engineering Principle:
The system must never infer a definite mathematical misconception from visual
evidence that is insufficient to establish the student's intended steps.

Covers all 14 points specified in Gate 4A.2 Section 11:
1. Correct number-line reasoning (Case 1: canonical correct)
2. Genuine off-by-one misconception (Case 2: MISC-LINE-INTERVAL-MISLABEL preserved)
3. Missing arrowheads detection
4. Missing final answer handling
5. Unclear / missing endpoint handling (no fabrication of coordinates)
6. Partially supported mathematical steps
7. Unsupported arithmetic-slip diagnosis suppression (Case 3)
8. Completeness classification
9. Teacher-review escalation
10. Critic grounding and contradiction checks
11. Confidence score provenance and calibration (no hardcoded 0.95 on Case 3)
12. API response schema compatibility
13. Dev endpoint output formatting for Case 3
14. Zero additional live calls or network requests from downstream agents
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.main import app
from services.worker.agents.contracts import (
    AnswerStatus,
    QualityStatus,
    ReasoningStatus,
    VisualEvidenceOutput,
    VisualObservation,
)
from services.worker.agents.evidence_sufficiency import (
    EvidenceSufficiencyEvaluator,
    ResponseEvidenceSufficiency,
)
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.math_verifier.contracts import NumberLineHop, QuestionRule
from services.worker.math_verifier.verifier import verify_student_math_reasoning


@pytest.fixture
def api_client():
    return TestClient(app)


# ==============================================================================
# 1. Case 1: Canonical Correct Reasoning
# ==============================================================================

def test_case_01_canonical_correct_preservation():
    """Case 1: Valid hops (0->-6->6->2) and final answer 2 produce clean pass."""
    analysis = MultiAgentPipeline.analyze_response("resp_04255753")

    assert analysis.answer_status == AnswerStatus.CORRECT
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
    assert analysis.needs_teacher_review is False
    assert analysis.diagnosis.misconception_taxonomy_id is None
    assert analysis.diagnosis.first_supported_error is None
    assert analysis.diagnosis.evidence_sufficiency == "sufficient"
    assert analysis.critic_audit.approved is True
    assert analysis.critic_audit.audit_verdict == "audit_passed"
    assert analysis.critic_audit.requires_teacher_review is False
    assert analysis.critic_audit.confidence >= 0.90


# ==============================================================================
# 2. Case 2: Genuine Off-by-One Misconception Preserved
# ==============================================================================

def test_case_02_genuine_off_by_one_preserved():
    """Case 2: Legitimate step discrepancy (-6->5 with label 12) preserves misconception."""
    analysis = MultiAgentPipeline.analyze_response("resp_a5c95313")

    assert analysis.answer_status == AnswerStatus.INCORRECT
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_ERROR
    assert analysis.diagnosis.misconception_taxonomy_id == "MISC-LINE-INTERVAL-MISLABEL"
    assert analysis.diagnosis.first_supported_error is not None
    assert analysis.diagnosis.first_supported_error.step_number == 2
    assert analysis.diagnosis.evidence_sufficiency == "sufficient"
    # Genuine error with sufficient evidence does not fail the grounding audit
    assert analysis.critic_audit.approved is True
    assert analysis.critic_audit.audit_verdict == "audit_passed"


# ==============================================================================
# 3 & 7. Case 3: Ambiguous and Incomplete Work (Defect Resolution)
# ==============================================================================

def test_case_03_ambiguous_incomplete_suppresses_misconception():
    """Case 3: Incomplete/ambiguous strokes MUST NOT assign MISC-ARITH-SLIP."""
    analysis = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")

    # Reasoning cannot be proven correct or erroneous due to lack of evidence
    assert analysis.reasoning_status == ReasoningStatus.INCOMPLETE
    assert analysis.answer_status == AnswerStatus.UNDETERMINED
    assert analysis.diagnosis.inferred_final_answer is None

    # CRITICAL: Suppress definite misconception
    assert analysis.diagnosis.misconception_taxonomy_id is None
    assert analysis.diagnosis.first_supported_error is None
    assert analysis.diagnosis.evidence_sufficiency == "insufficient"
    assert "cannot be definitively diagnosed" in (analysis.diagnosis.diagnostic_explanation or "")

    # Teacher review MUST be required
    assert analysis.needs_teacher_review is True
    assert analysis.critic_audit.requires_teacher_review is True
    assert analysis.critic_audit.audit_verdict == "review_required"


# ==============================================================================
# 4. Missing Arrowhead Handling
# ==============================================================================

def test_missing_arrowhead_detection():
    """Observations lacking clear direction/arrowheads are flagged."""
    obs = VisualObservation(
        kind="arrow_jump",
        value="Arc 0 to -6 missing arrowhead",
        confidence=0.65,
        start_pos=0.0,
        end_pos=-6.0,
        direction="none",
    )
    step_eval = EvidenceSufficiencyEvaluator.evaluate_step(obs, step_number=1)

    assert step_eval.has_arrowhead is False
    assert "missing_or_ambiguous_arrowhead" in step_eval.issues
    assert step_eval.evidence_status in ("partially_supported", "insufficient_evidence")


# ==============================================================================
# 5. Missing Endpoint Handling (No Fabrication)
# ==============================================================================

def test_missing_endpoint_not_fabricated():
    """Arc without endpoint coordinate must not fabricate coordinate or displacement."""
    obs = VisualObservation(
        kind="arrow_jump",
        value="Arc terminating near 1 without endpoint",
        confidence=0.40,
        start_pos=-6.0,
        end_pos=None,
        direction="none",
    )
    step_eval = EvidenceSufficiencyEvaluator.evaluate_step(obs, step_number=2)

    assert step_eval.has_endpoints is False
    assert step_eval.is_supported is False
    assert step_eval.evidence_status == "insufficient_evidence"
    assert "missing_terminal_coordinate" in step_eval.issues


# ==============================================================================
# 6. Missing Final Answer Handling
# ==============================================================================

def test_missing_final_answer_handling():
    """Unmarked final answer does not assume 0.0 or target value."""
    visual = VisualEvidenceOutput(
        quality_status=QualityStatus.CLEAR,
        observations=[
            VisualObservation(kind="number_line", value="Line [-8, 8]", confidence=0.9),
            VisualObservation(kind="arrow_jump", value="Jump 0 to -6", confidence=0.9, start_pos=0.0, end_pos=-6.0, direction="left"),
        ],
        has_number_line=True,
        final_answer_marked=None,
        confidence=0.85,
    )
    hyp = MockAgentAdapter.get_hypotheses(visual)
    diag = MockAgentAdapter.get_diagnosis(hyp, visual)

    # Incomplete hop sequence with no marked final answer leaves answer status undetermined
    assert diag.answer_status == AnswerStatus.UNDETERMINED
    assert diag.inferred_final_answer is None


# ==============================================================================
# 8. Completeness Classification
# ==============================================================================

def test_completeness_classification():
    """Candidate hypotheses reflect incomplete working when evidence is insufficient."""
    visual = MockAgentAdapter.get_visual_evidence("case_03_ambiguous_incomplete")
    hyp = MockAgentAdapter.get_hypotheses(visual)

    assert hyp.reasoning_completeness == "incomplete"
    assert hyp.detected_strategy == "insufficient_evidence"
    assert hyp.evidence_support == "insufficient_evidence"


# ==============================================================================
# 9. Teacher-Review Escalation
# ==============================================================================

def test_teacher_review_escalation_rules():
    """Insufficient evidence unconditionally triggers educator escalation."""
    analysis = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")

    assert analysis.needs_teacher_review is True
    assert analysis.teacher_review_reason is not None
    assert (
        "ambiguities" in analysis.teacher_review_reason.lower()
        or "insufficient" in analysis.teacher_review_reason.lower()
        or "incomplete" in analysis.teacher_review_reason.lower()
        or "low_confidence" in analysis.teacher_review_reason.lower()
    )


# ==============================================================================
# 10. Critic Grounding and Contradiction Checks
# ==============================================================================

def test_critic_contradiction_detection_on_ungrounded_misconception():
    """Independent Critic detects contradiction if misconception is assigned without evidence."""
    visual = MockAgentAdapter.get_visual_evidence("case_03_ambiguous_incomplete")
    hyp = MockAgentAdapter.get_hypotheses(visual)
    diag = MockAgentAdapter.get_diagnosis(hyp, visual)

    # Manually inject an ungrounded misconception to test Critic adversarial defense
    flawed_diag = diag.model_copy(
        update={
            "misconception_taxonomy_id": "MISC-ARITH-SLIP",
            "evidence_sufficiency": "insufficient",
        }
    )

    audit = MockAgentAdapter.get_critic_audit(visual=visual, diagnosis=flawed_diag)

    assert audit.approved is False
    assert audit.contradiction_detected is True
    assert audit.audit_verdict == "audit_rejected"
    assert audit.requires_teacher_review is True
    assert any("insufficient visual evidence" in d for d in audit.discrepancy_notes)


# ==============================================================================
# 11. Confidence Provenance and Calibration
# ==============================================================================

def test_confidence_provenance_and_calibration():
    """Investigates confidence scores: Case 3 visual is 60% and Critic is calibrated <= 65%."""
    analysis = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")

    # Visual confidence reflects blocking ambiguities
    assert analysis.visual_evidence.confidence == pytest.approx(0.60, abs=0.01)

    # Critic confidence is calibrated to visual/evidence uncertainty, not hardcoded 0.95
    assert analysis.critic_audit.confidence <= 0.65
    assert analysis.critic_audit.confidence == pytest.approx(0.60, abs=0.01)


# ==============================================================================
# 12 & 13. API Compatibility and Dev Endpoint
# ==============================================================================

def test_api_dev_analyze_synthetic_case_03(api_client):
    """Verifies FastAPI endpoint /api/v1/dev/analyze-synthetic handles Case 3 correctly."""
    resp = api_client.post(
        "/api/v1/dev/analyze-synthetic",
        json={
            "fixture_id": "case_03_ambiguous_incomplete",
            "rule_expr": "-6 + 12 - 4",
            "target_value": 2.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    analysis = data["analysis"]
    assert analysis["reasoning_status"] == "incomplete"
    assert analysis["answer_status"] == "undetermined"
    assert analysis["needs_teacher_review"] is True

    diag = analysis["diagnosis"]
    assert diag["misconception_taxonomy_id"] is None
    assert diag["first_supported_error"] is None
    assert diag["evidence_sufficiency"] == "insufficient"

    critic = analysis["critic_audit"]
    assert critic["audit_verdict"] == "review_required"
    assert critic["requires_teacher_review"] is True


# ==============================================================================
# 14. Zero Additional Gemini Calls Guard
# ==============================================================================

def test_zero_additional_gemini_calls_in_downstream_pipeline():
    """Downstream agents and Critic must never trigger external API calls."""
    analysis = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")

    # Verified offline execution
    assert analysis.is_mock is True
    assert analysis.tokens_consumed == 0
    assert analysis.cost_estimate_usd == 0.0
    assert analysis.reinterpretation_attempted is False
