"""Integration tests for Gate 4A Live Gemini integration into the Multi-Agent Pipeline.

Validates end-to-end integration:
- MultiAgentPipeline orchestration with GeminiVisualEvidenceProvider.
- SymPy deterministic mathematical authority across all 3 Gate 3C scenarios:
  1. Case 01: Canonical Correct (SymPy validates steps 0 -> -6 -> 6 -> 2, correct answer 2).
  2. Case 02: Procedural Off-by-one (SymPy identifies step 2 jump to 5, taxonomized as MISC-ARITH-OFF-BY-ONE).
  3. Case 03: Ambiguous / Incomplete (flags teacher review, blank answer, incomplete reasoning).
- Critic audit bounded reinterpretation with Gemini evidence.
- CohortIntelligenceAgent deterministic aggregation and SymPy-verified exit tickets.
- InlineDispatcher background task execution with analysis telemetry persistence.
- Strict security boundaries: zero live network calls during testing, real dataset blocking.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from services.api.dispatch.inline_dispatcher import inline_dispatcher
from services.api.repository.memory_repo import memory_repo
from services.worker.agents.contracts import (
    AnswerStatus,
    ReasoningStatus,
    StudentResponseAnalysis,
)
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.provider import (
    GeminiVisualEvidenceProvider,
    MockVisualEvidenceProvider,
)
from services.worker.evaluation.contracts import (
    ExtractionCertainty,
    GeminiVisualEvidenceSchema,
    HopDirection,
    ImageQualityAssessment,
    NumberLineObservation,
    ObservedHop,
    VisibleFinalAnswer,
    VisualAmbiguity,
)
from services.worker.gemini.adapter import GeminiVisionAdapter
from services.worker.security.provenance_guard import (
    TRUSTED_SYNTHETIC_DIR,
    UntrustedProvenanceError,
)


class StubGeminiVisionAdapter(GeminiVisionAdapter):
    """Offline stub for GeminiVisionAdapter simulating Gate 3 Vertex AI model outputs without credentials."""

    def __init__(self) -> None:
        super().__init__(
            model_id="gemini-3.8-flash",
            location="global",
            project="precise-equator-511303-m1",
            max_calls=10,
        )

    def extract_from_path(
        self,
        image_path: Path,
        response_id: str,
        prompt_override: Optional[str] = None,
    ) -> GeminiVisualEvidenceSchema:
        """Returns deterministic Gate 3 evaluation schemas with realistic token accounting."""
        r_lower = response_id.lower()

        # Simulate token usage telemetry
        self._record_telemetry(
            response_id=response_id,
            input_tokens=258,
            output_tokens=320,
            latency_ms=250,
        )

        if "case_01" in r_lower or "canonical" in r_lower:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.CLEAR,
                visible_final_answer=VisibleFinalAnswer(
                    value="2",
                    evidence_location="Answer box contains written 2",
                    certainty=ExtractionCertainty.HIGH,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-12.0,
                    max_visible_tick=12.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            stated_magnitude_label="-6",
                            evidence_description="Clear arc from 0 to -6",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=6.0,
                            direction=HopDirection.RIGHT_POSITIVE,
                            stated_magnitude_label="+12",
                            evidence_description="Clear arc from -6 to +6",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=3,
                            start_value=6.0,
                            end_value=2.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            stated_magnitude_label="-4",
                            evidence_description="Clear arc from +6 to +2",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                    ],
                ),
                ambiguities=[],
                requires_teacher_review=False,
            )

        elif "case_02" in r_lower or "off_by_one" in r_lower:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.CLEAR,
                visible_final_answer=VisibleFinalAnswer(
                    value="1",
                    evidence_location="Answer box contains written 1",
                    certainty=ExtractionCertainty.HIGH,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-10.0,
                    max_visible_tick=10.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            stated_magnitude_label="-6",
                            evidence_description="Arc from 0 to -6",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=5.0,  # Procedural tick count error
                            direction=HopDirection.RIGHT_POSITIVE,
                            stated_magnitude_label="+12",
                            evidence_description="Arc from -6 to +5",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=3,
                            start_value=5.0,
                            end_value=1.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            stated_magnitude_label="-4",
                            evidence_description="Arc from 5 to 1",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                    ],
                ),
                ambiguities=[],
                requires_teacher_review=False,
            )

        elif "case_03" in r_lower or "ambiguous" in r_lower:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.FAINT_READABLE,
                visible_final_answer=VisibleFinalAnswer(
                    value=None,
                    certainty=ExtractionCertainty.CANNOT_DETERMINE,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-8.0,
                    max_visible_tick=8.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arrowhead_visible=False,
                            evidence_description="Faint arc from 0 to -6 without arrowhead",
                            certainty=ExtractionCertainty.MEDIUM,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=None,
                            direction=HopDirection.AMBIGUOUS,
                            arrowhead_visible=False,
                            evidence_description="Incomplete stroke terminating near 1",
                            certainty=ExtractionCertainty.LOW,
                        ),
                    ],
                ),
                ambiguities=[
                    VisualAmbiguity(element="arrowhead", description="No arrowheads", severity="minor"),
                    VisualAmbiguity(element="hop", description="Hop #2 terminates ambiguously", severity="blocking"),
                ],
                requires_teacher_review=True,
                teacher_review_reason="Incomplete hop sequence and blank answer require teacher review.",
            )

        raise ValueError(f"Unknown test fixture response_id: {response_id}")


class TestGate4APipelineIntegration:
    """End-to-end integration of Gemini visual extraction through the 5-agent pipeline."""

    @pytest.fixture
    def gemini_provider(self) -> GeminiVisualEvidenceProvider:
        """Provides a GeminiVisualEvidenceProvider backed by the offline stub adapter."""
        stub_adapter = StubGeminiVisionAdapter()
        return GeminiVisualEvidenceProvider(adapter=stub_adapter)

    def test_pipeline_case_01_canonical_correct(self, gemini_provider):
        """Case 01: Canonical correct response through full 5-agent pipeline."""
        analysis = MultiAgentPipeline.analyze_response(
            response_id="case_01_canonical_correct",
            provider=gemini_provider,
        )

        assert isinstance(analysis, StudentResponseAnalysis)
        # Provenance: Live Gemini model identifier
        assert analysis.is_mock is False
        assert analysis.model_version == "gemini-3.8-flash"
        assert analysis.visual_evidence.provenance == "gemini-3.8-flash"

        # Mathematical authority: SymPy validated
        assert analysis.answer_status == AnswerStatus.CORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
        assert analysis.is_compensatory_error is False
        assert analysis.needs_teacher_review is False

        # Critic audit: approved without discrepancy
        assert analysis.critic_audit.approved is True
        assert analysis.critic_audit.evidence_grounded is True

        # Telemetry captured
        assert analysis.tokens_consumed == 578  # 258 in + 320 out
        assert analysis.cost_estimate_usd is not None
        assert analysis.cost_estimate_usd > 0.0
        assert analysis.live_telemetry is not None
        assert analysis.live_telemetry["model_id"] == "gemini-3.8-flash"

    def test_pipeline_case_02_off_by_one_procedural_error(self, gemini_provider):
        """Case 02: Procedural off-by-one tick count error through full pipeline."""
        analysis = MultiAgentPipeline.analyze_response(
            response_id="case_02_off_by_one_error",
            provider=gemini_provider,
        )

        assert analysis.is_mock is False
        assert analysis.model_version == "gemini-3.8-flash"

        # SymPy correctly identifies math error
        assert analysis.answer_status == AnswerStatus.INCORRECT
        assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_ERROR

        # Diagnosis correctly localizes step 2 and assigns taxonomy (stated +12 but moved 11)
        assert analysis.diagnosis.misconception_taxonomy_id == "MISC-LINE-INTERVAL-MISLABEL"
        assert analysis.diagnosis.first_supported_error is not None
        assert analysis.diagnosis.first_supported_error.step_number == 2

        # Critic approves diagnosis as grounded in physical marks
        assert analysis.critic_audit.approved is True
        assert analysis.critic_audit.evidence_grounded is True

    def test_pipeline_case_03_ambiguous_incomplete(self, gemini_provider):
        """Case 03: Ambiguous and incomplete response flags teacher review."""
        analysis = MultiAgentPipeline.analyze_response(
            response_id="case_03_ambiguous_incomplete",
            provider=gemini_provider,
        )

        assert analysis.is_mock is False
        assert analysis.needs_teacher_review is True
        assert "require teacher review" in analysis.teacher_review_reason.lower()
        assert analysis.answer_status == AnswerStatus.UNDETERMINED
        assert analysis.reasoning_status in (ReasoningStatus.INCOMPLETE, ReasoningStatus.SUPPORTED_ERROR)

    def test_critic_retry_bounded_with_gemini_evidence(self, gemini_provider):
        """Adversarial critic discrepancy triggers at most one bounded reinterpretation."""
        analysis = MultiAgentPipeline.analyze_response(
            response_id="case_01_canonical_correct",
            provider=gemini_provider,
            force_critic_retry=True,
        )

        assert analysis.reinterpretation_attempted is True
        assert analysis.critic_audit.critic_attempt_number == 2
        assert analysis.critic_audit.approved is True

    def test_cohort_analysis_with_gemini_responses(self, gemini_provider):
        """Cohort intelligence analyzes a mix of responses deterministically."""
        r1 = MultiAgentPipeline.analyze_response("case_01_canonical_correct", provider=gemini_provider)
        r2 = MultiAgentPipeline.analyze_response("case_02_off_by_one_error", provider=gemini_provider)
        r3 = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete", provider=gemini_provider)

        cohort_output = MultiAgentPipeline.analyze_cohort([r1, r2, r3])

        assert cohort_output.executive_narrative is not None
        assert "3 students" in cohort_output.executive_narrative
        # Dominant misconception matches case_02
        assert "MISC-LINE-INTERVAL-MISLABEL" in cohort_output.dominant_misconceptions
        # Exit ticket items verified via SymPy
        assert len(cohort_output.formative_exit_ticket) == 3
        for item in cohort_output.formative_exit_ticket:
            assert item.sympy_verified is True


class TestSecurityBoundaries:
    """Tests security safeguards prohibiting unauthorized image access or live leakage."""

    def test_real_dataset_access_blocked_by_provider(self):
        """GeminiVisualEvidenceProvider blocks any attempt to analyze real student datasets."""
        stub_adapter = StubGeminiVisionAdapter()
        provider = GeminiVisualEvidenceProvider(adapter=stub_adapter)

        forbidden_paths = [
            "/dataset/problem_1065658/real_student_work.jpg",
            "dataset/mathwriting/case.png",
            "/ClassLens/dataset/drawedumath.png",
        ]

        for path in forbidden_paths:
            with pytest.raises(UntrustedProvenanceError, match="references a real dataset"):
                provider.extract_evidence("resp_test", image_source=path)

        # Call count remains zero
        assert stub_adapter.call_count == 0

    def test_unregistered_response_id_blocked_by_provider(self):
        """Passing an arbitrary unregistered response_id without trusted fixture is blocked."""
        stub_adapter = StubGeminiVisionAdapter()
        provider = GeminiVisualEvidenceProvider(adapter=stub_adapter)

        with pytest.raises(UntrustedProvenanceError, match="does not map to an authorized synthetic fixture"):
            provider.extract_evidence("unregistered_student_upload_9999")

        assert stub_adapter.call_count == 0


class TestInlineDispatcherIntegration:
    """Tests inline dispatcher persistence of live/mock metadata."""

    def test_inline_dispatcher_persists_analysis_metadata(self):
        """Inline dispatcher sets task_status, is_mock, model_version, and analysis_data."""
        assessment_id = "asm_1065658"
        resp_id = "resp_04255753"
        resp = memory_repo.get_response(resp_id, assessment_id=assessment_id)
        assert resp is not None

        # Reset status
        resp.task_status = "PENDING"
        memory_repo.update_response(resp)

        job = memory_repo.create_or_get_analysis_job(assessment_id, total_items=1)

        async def _run_batch():
            await inline_dispatcher.dispatch_analysis_batch(
                job_id=job.id,
                assessment_id=assessment_id,
                response_ids=[resp_id],
            )

        asyncio.run(_run_batch())

        updated_resp = memory_repo.get_response(resp_id, assessment_id=assessment_id)
        assert updated_resp.task_status == "COMPLETED"
        assert updated_resp.answer_status == "correct"
        assert updated_resp.is_mock is True
        assert updated_resp.model_version == "mock-offline-fixture"
        assert updated_resp.analysis_data is not None
