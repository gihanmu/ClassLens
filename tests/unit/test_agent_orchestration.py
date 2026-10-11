"""Comprehensive unit and acceptance test suite for Google ADK multi-agent orchestration."""

from __future__ import annotations

import pytest

from services.worker.agents.cohort_agent import create_cohort_intelligence_agent
from services.worker.agents.contracts import (
    AnswerStatus,
    CohortIntelligenceOutput,
    CriticAuditOutput,
    DiagnosticOutput,
    QualityStatus,
    ReasoningStatus,
    StudentResponseAnalysis,
    VisualEvidenceOutput,
)
from services.worker.agents.critic_agent import create_critic_agent
from services.worker.agents.diagnostic_agent import create_diagnostic_agent
from services.worker.agents.interpretation_agent import create_math_interpretation_agent
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.tools import (
    compute_cohort_statistics,
    eval_sympy_arithmetic,
    validate_number_line_moves,
)
from services.worker.agents.visual_agent import create_visual_evidence_agent
from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES


# ==============================================================================
# 1. Google ADK Agent Abstraction Tests
# ==============================================================================

class TestADKAgentDefinitions:
    """Verifies that all 5 agents instantiate properly using Google ADK Agent abstractions."""

    def test_visual_evidence_agent_instantiation(self):
        agent = create_visual_evidence_agent(model="gemini-3.8-flash", high_res_mode=False)
        assert agent.name == "visual_evidence_agent"
        assert agent.model == "gemini-3.8-flash"
        assert len(agent.tools) == 0

    def test_visual_evidence_agent_high_res_mode(self):
        agent = create_visual_evidence_agent(model="gemini-3.8-flash", high_res_mode=True)
        assert "high-resolution" in agent.description

    def test_math_interpretation_agent_instantiation(self):
        agent = create_math_interpretation_agent(model="gemini-3.8-flash")
        assert agent.name == "math_interpretation_agent"
        assert agent.model == "gemini-3.8-flash"

    def test_diagnostic_agent_has_deterministic_tools(self):
        agent = create_diagnostic_agent(model="gemini-3.8-flash")
        assert agent.name == "diagnostic_agent"
        assert len(agent.tools) == 2
        tool_names = [t.__name__ for t in agent.tools]
        assert "eval_sympy_arithmetic" in tool_names
        assert "validate_number_line_moves" in tool_names

    def test_critic_agent_instantiation(self):
        agent = create_critic_agent(model="gemini-3.8-flash")
        assert agent.name == "independent_critic_agent"

    def test_cohort_agent_has_sympy_tool(self):
        agent = create_cohort_intelligence_agent(model="gemini-3.8-flash")
        assert agent.name == "cohort_intelligence_agent"
        tool_names = [t.__name__ for t in agent.tools]
        assert "eval_sympy_arithmetic" in tool_names
        assert "compute_cohort_statistics" in tool_names


# ==============================================================================
# 2. Deterministic Tools Tests
# ==============================================================================

class TestAgentTools:
    """Tests for deterministic tools bound to ADK agents."""

    def test_eval_sympy_arithmetic_tool(self):
        res = eval_sympy_arithmetic("-6 + 12 - 4", expected_value=2.0)
        assert res["success"] is True
        assert res["computed_value"] == 2.0
        assert res["is_equal"] is True
        assert res["addends"] == [-6.0, 12.0, -4.0]

    def test_validate_number_line_moves_tool(self):
        moves = [
            {"step_number": 1, "start": 0.0, "end": -6.0, "direction": "left"},
            {"step_number": 2, "start": -6.0, "end": 6.0, "direction": "right"},
            {"step_number": 3, "start": 6.0, "end": 2.0, "direction": "left"},
        ]
        verdict = validate_number_line_moves(start=0.0, moves=moves, target_value=2.0)
        assert verdict["is_reasoning_valid"] is True
        assert verdict["is_final_answer_valid"] is True
        assert verdict["detected_method"] == "hop_from_zero"

    def test_compute_cohort_statistics_tool(self):
        sample_responses = [
            {"response_id": "r1", "answer_status": "correct", "reasoning_status": "supported_correct"},
            {"response_id": "r2", "answer_status": "correct", "reasoning_status": "supported_error", "is_compensatory_error": True, "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE"},
            {"response_id": "r3", "answer_status": "incorrect", "reasoning_status": "supported_error", "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE"},
            {"response_id": "r4", "answer_status": "incorrect", "reasoning_status": "supported_error", "misconception_taxonomy_id": "MISC-NUM-DIR-REVERSE"},
        ]
        stats = compute_cohort_statistics(sample_responses)
        assert stats["total_students"] == 4
        assert stats["correct_answers"] == 2
        assert stats["correct_answers_pct"] == 50.0
        assert stats["valid_reasoning"] == 1
        assert stats["compensatory_errors"] == 1
        assert len(stats["misconception_clusters"]) == 2
        top_cluster = stats["misconception_clusters"][0]
        assert top_cluster["taxonomy_id"] == "MISC-ARITH-OFF-BY-ONE"
        assert top_cluster["count"] == 2
        assert top_cluster["percentage"] == 50.0


# ==============================================================================
# 3. Acceptance Tests (TC-003.01 through TC-003.05)
# ==============================================================================

class TestAcceptanceCases:
    """Verifies all acceptance criteria defined in specs/003-agent-orchestration/acceptance-tests.md."""

    def test_tc_003_01_clean_student_response(self):
        """TC-003.01: Clean student response fixture (resp_04255753)."""
        analysis = MultiAgentPipeline.analyze_response("resp_04255753")

        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.answer_status == AnswerStatus.CORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
        assert analysis.needs_teacher_review is False
        assert analysis.is_compensatory_error is False
        assert analysis.is_mock is True
        assert analysis.model_version == "mock-offline-fixture"

    def test_tc_003_02_compensatory_error_handling(self):
        """TC-003.02: Compensatory error fixture (resp_56005c1c)."""
        analysis = MultiAgentPipeline.analyze_response("resp_56005c1c")

        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.answer_status == AnswerStatus.CORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_ERROR
        assert analysis.is_compensatory_error is True
        assert analysis.needs_teacher_review is True
        assert analysis.diagnosis.first_supported_error is not None
        assert analysis.diagnosis.first_supported_error.step_number == 2
        assert analysis.diagnosis.misconception_taxonomy_id == "MISC-ARITH-OFF-BY-ONE"

    def test_tc_003_03_incomplete_reasoning(self):
        """TC-003.03: Answer marked without working (resp_e33295ea)."""
        analysis = MultiAgentPipeline.analyze_response("resp_e33295ea")

        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.answer_status == AnswerStatus.CORRECT
        assert analysis.reasoning_status == ReasoningStatus.INCOMPLETE
        assert analysis.needs_teacher_review is True
        assert "Incomplete reasoning" in analysis.teacher_review_reason

    def test_tc_003_04_critic_bounded_retry(self):
        """TC-003.04: Mock Critic detects contradiction on pass 1 -> triggers at most 1 reinterpretation."""
        analysis = MultiAgentPipeline.analyze_response(
            "resp_04255753", force_critic_retry=True
        )

        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.reinterpretation_attempted is True
        assert analysis.critic_audit.critic_attempt_number == 2
        assert analysis.critic_audit.approved is True

    def test_tc_003_05_low_confidence_escalation(self):
        """TC-003.05: Mock perception emits confidence 0.65 -> flags teacher review."""
        analysis = MultiAgentPipeline.analyze_response(
            "resp_04255753", confidence_override=0.65
        )

        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.needs_teacher_review is True
        assert analysis.teacher_review_reason == "low_confidence"


# ==============================================================================
# 4. Comprehensive Evaluation across All 13 Problem #1065658 Responses
# ==============================================================================

class TestAll13ResponsesBatch:
    """Evaluates all 13 response fixtures of Problem #1065658."""

    @pytest.mark.parametrize("resp_id", list(MOCK_FIXTURES.keys()))
    def test_all_13_responses_parse_cleanly(self, resp_id: str):
        analysis = MultiAgentPipeline.analyze_response(resp_id)
        assert isinstance(analysis, StudentResponseAnalysis)
        assert analysis.response_id == resp_id
        assert analysis.is_mock is True

    def test_row_6_answer_mismatch_flagged(self):
        """Row 6: Student circled 3, number line was correct -> answer incorrect, reasoning correct."""
        analysis = MultiAgentPipeline.analyze_response("resp_8cbadb4e")
        assert analysis.answer_status == AnswerStatus.INCORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT

    def test_row_8_interval_mislabel_flagged(self):
        """Row 8: Mislabeled number line intervals -> MISC-LINE-INTERVAL-MISLABEL."""
        analysis = MultiAgentPipeline.analyze_response("resp_a5c95313")
        assert analysis.diagnosis.misconception_taxonomy_id == "MISC-LINE-INTERVAL-MISLABEL"

    def test_row_9_commutative_rearrangement(self):
        """Row 9: 12 - 4 - 6 = 2 accepted as valid commutative path."""
        analysis = MultiAgentPipeline.analyze_response("resp_b4214e02")
        assert analysis.answer_status == AnswerStatus.CORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
        assert analysis.candidate_hypotheses.detected_strategy == "commutative"

    def test_row_12_unreadable_submission(self):
        """Row 12: Incomplete/unreadable -> needs_teacher_review True."""
        analysis = MultiAgentPipeline.analyze_response("resp_f0738571")
        assert analysis.quality_status == QualityStatus.UNREADABLE
        assert analysis.needs_teacher_review is True


# ==============================================================================
# 5. Cohort Intelligence Agent Integration Tests
# ==============================================================================

class TestCohortIntelligenceIntegration:
    """Verifies Agent 5: CohortIntelligenceAgent batch analysis."""

    def test_analyze_cohort_full_batch(self):
        all_analyses = [MultiAgentPipeline.analyze_response(rid) for rid in MOCK_FIXTURES.keys()]
        cohort_out = MultiAgentPipeline.analyze_cohort(all_analyses)

        assert isinstance(cohort_out, CohortIntelligenceOutput)
        assert "Class Assessment Analysis (13 students)" in cohort_out.executive_narrative
        assert len(cohort_out.dominant_misconceptions) > 0
        assert len(cohort_out.differentiated_actions) > 0

        # Verify all 3 formative exit ticket items were verified with SymPy
        assert len(cohort_out.formative_exit_ticket) == 3
        for item in cohort_out.formative_exit_ticket:
            assert item.sympy_verified is True
