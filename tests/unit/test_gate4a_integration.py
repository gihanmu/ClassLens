"""Unit tests for Gate 4A Live Gemini integration components and safeguards.

Validates:
- Settings mode resolution, dual-gate live activation, and configuration validation.
- VisualEvidenceProvider protocol and Mock / Gemini provider selection.
- Provenance guard enforcement: real dataset blocking, path traversal rejection, SHA-256 allowlist.
- Schema translation from GeminiVisualEvidenceSchema to VisualEvidenceOutput.
- GeminiVisionAdapter local accounting, circuit breaker, and error hierarchy.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.api.config import ConfigurationError, Settings
from services.worker.agents.contracts import (
    QualityStatus,
    VisualEvidenceOutput,
)
from services.worker.agents.provider import (
    GeminiVisualEvidenceProvider,
    MockVisualEvidenceProvider,
    VisualEvidenceProvider,
    gemini_schema_to_visual_evidence,
    get_visual_evidence_provider,
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
from services.worker.gemini.adapter import (
    GeminiAuthenticationError,
    GeminiModelError,
    GeminiQuotaError,
    GeminiTimeoutError,
    GeminiVisionAdapter,
    GeminiVisionError,
)
from services.worker.security.provenance_guard import (
    PROJECT_ROOT,
    TRUSTED_SYNTHETIC_ALLOWLIST,
    TRUSTED_SYNTHETIC_DIR,
    UntrustedProvenanceError,
    calculate_sha256,
    is_trusted_synthetic,
    verify_synthetic_bytes,
    verify_synthetic_path,
)


class TestGate4AConfiguration:
    """Tests configuration and dual-gate authorization for live AI execution."""

    def test_default_configuration_is_mock(self):
        """Default settings must enforce mock mode with zero live inference."""
        s = Settings()
        assert s.ai_mode == "mock"
        assert s.live_inference_enabled is False
        assert s.is_live_mode() is False

    def test_dual_gate_requires_both_flags(self):
        """Live mode requires BOTH ai_mode == 'live' AND live_inference_enabled == True."""
        # Only ai_mode set
        s1 = Settings(ai_mode="live", live_inference_enabled=False, mock_llm=False)
        assert s1.is_live_mode() is False

        # Only live_inference_enabled set
        s2 = Settings(ai_mode="mock", live_inference_enabled=True, mock_llm=False)
        assert s2.is_live_mode() is False

        # Both set
        s3 = Settings(ai_mode="live", live_inference_enabled=True, mock_llm=False)
        assert s3.is_live_mode() is True

    def test_legacy_mock_llm_flag_overrides_non_live(self):
        """Legacy mock_llm=True flag ensures offline execution."""
        s = Settings(mock_llm=True, ai_mode="mock", live_inference_enabled=False)
        assert s.is_live_mode() is False

    def test_validate_live_configuration_checks_project_and_catalog(self):
        """Live configuration requires valid project and verified model catalog ID."""
        # Missing project
        s_no_proj = Settings(
            ai_mode="live",
            live_inference_enabled=True,
            mock_llm=False,
            google_cloud_project=None,
        )
        with pytest.raises(ConfigurationError, match="requires GOOGLE_CLOUD_PROJECT"):
            s_no_proj.validate_live_configuration()

        # Unverified model
        s_bad_model = Settings(
            ai_mode="live",
            live_inference_enabled=True,
            mock_llm=False,
            google_cloud_project="test-project",
            gemini_model="unverified-gpt-model",
        )
        with pytest.raises(ConfigurationError, match="not in the verified Vertex AI model catalog"):
            s_bad_model.validate_live_configuration()

        # Verified model passes
        s_valid = Settings(
            ai_mode="live",
            live_inference_enabled=True,
            mock_llm=False,
            google_cloud_project="precise-equator-511303-m1",
            gemini_model="gemini-3.8-flash",
        )
        s_valid.validate_live_configuration()


class TestProvenanceGuard:
    """Tests security and privacy confinement to trusted synthetic evaluation cases."""

    def test_trusted_synthetic_fixtures_pass(self):
        """All pre-approved synthetic evaluation fixtures must pass verification."""
        for filename in TRUSTED_SYNTHETIC_ALLOWLIST.keys():
            fixture_path = TRUSTED_SYNTHETIC_DIR / filename
            assert fixture_path.exists(), f"Fixture {filename} missing"
            verified = verify_synthetic_path(fixture_path)
            assert verified == fixture_path.resolve()
            assert is_trusted_synthetic(fixture_path) is True

    def test_real_dataset_path_blocked(self):
        """Any attempt to provide paths containing dataset/ or drawedumath is strictly blocked."""
        bad_paths = [
            "/Users/someone/dataset/problem_1065658/img_01.png",
            "dataset/student_work/sample.png",
            "/tmp/drawedumath_extract.jpg",
            "/ClassLens/data/mathwriting_01.png",
        ]
        for p in bad_paths:
            with pytest.raises(UntrustedProvenanceError, match="references a real dataset"):
                verify_synthetic_path(p)

    def test_path_traversal_blocked(self):
        """Path traversal escaping TRUSTED_SYNTHETIC_DIR must be blocked."""
        traversal_path = TRUSTED_SYNTHETIC_DIR / ".." / "synthetic_math_fixtures.py"
        with pytest.raises(UntrustedProvenanceError, match="outside the trusted synthetic directory"):
            verify_synthetic_path(traversal_path)

    def test_arbitrary_client_bytes_blocked(self):
        """Arbitrary image bytes not matching the SHA-256 allowlist must be blocked in live mode."""
        arbitrary_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRarbitrary_random_student_pixels"
        with pytest.raises(UntrustedProvenanceError, match="do not match any authorized synthetic fixture"):
            verify_synthetic_bytes(arbitrary_png)

    def test_valid_synthetic_bytes_pass(self):
        """Authorized synthetic fixture bytes pass byte-level verification."""
        for filename in TRUSTED_SYNTHETIC_ALLOWLIST.keys():
            fixture_path = TRUSTED_SYNTHETIC_DIR / filename
            data = fixture_path.read_bytes()
            matched_name = verify_synthetic_bytes(data)
            assert matched_name == filename


class TestProviderSelectionAndProtocol:
    """Tests provider factory and VisualEvidenceProvider protocol adherence."""

    def test_default_factory_returns_mock_provider(self):
        """Default factory invocation returns MockVisualEvidenceProvider."""
        provider = get_visual_evidence_provider()
        assert isinstance(provider, MockVisualEvidenceProvider)
        assert isinstance(provider, VisualEvidenceProvider)

        # Mock extraction executes offline
        evidence = provider.extract_evidence("resp_04255753")
        assert evidence.provenance == "synthetic_mock_fixture"
        assert provider.last_tokens == 0
        assert provider.last_cost_usd == 0.0

    def test_force_mock_returns_mock_provider(self):
        """Explicit mode='mock' returns MockVisualEvidenceProvider."""
        provider = get_visual_evidence_provider(mode="mock")
        assert isinstance(provider, MockVisualEvidenceProvider)

    def test_force_live_without_credentials_creates_gemini_provider(self):
        """Explicit mode='live' instantiates GeminiVisualEvidenceProvider."""
        stub_adapter = MagicMock(spec=GeminiVisionAdapter)
        stub_adapter.model_id = "gemini-3.8-flash"
        stub_adapter.call_history = []
        stub_adapter.last_latency_ms = 0

        provider = get_visual_evidence_provider(mode="live", adapter=stub_adapter)
        assert isinstance(provider, GeminiVisualEvidenceProvider)
        assert isinstance(provider, VisualEvidenceProvider)


class TestSchemaTranslation:
    """Tests decoupled mapping from GeminiVisualEvidenceSchema to VisualEvidenceOutput."""

    def test_case_01_canonical_correct_mapping(self):
        """Translates canonical correct schema into VisualEvidenceOutput."""
        schema = GeminiVisualEvidenceSchema(
            response_id="case_01_canonical_correct",
            image_quality=ImageQualityAssessment.CLEAR,
            visible_final_answer=VisibleFinalAnswer(
                value="2",
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

        output = gemini_schema_to_visual_evidence(schema, model_id="gemini-3.8-flash")

        assert isinstance(output, VisualEvidenceOutput)
        assert output.quality_status == QualityStatus.CLEAR
        assert output.has_number_line is True
        assert output.final_answer_marked == "2"
        assert output.provenance == "gemini-3.8-flash"
        assert output.confidence >= 0.90
        assert output.requires_teacher_review is False
        assert len(output.observations) == 5  # 1 number line + 3 hops + 1 circled result

        hops = [obs for obs in output.observations if obs.kind == "arrow_jump"]
        assert len(hops) == 3
        assert hops[0].start_pos == 0.0
        assert hops[0].end_pos == -6.0
        assert hops[0].direction == "left"
        assert hops[1].direction == "right"
        assert hops[1].stated_magnitude == 12.0

    def test_case_03_ambiguous_incomplete_mapping_flags_review(self):
        """Translates ambiguous/incomplete schema, propagating ambiguities and review flag."""
        schema = GeminiVisualEvidenceSchema(
            response_id="case_03_ambiguous_incomplete",
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
                        evidence_description="Faint arc without arrowhead",
                        certainty=ExtractionCertainty.MEDIUM,
                    ),
                    ObservedHop(
                        hop_index=2,
                        start_value=-6.0,
                        end_value=None,
                        direction=HopDirection.AMBIGUOUS,
                        arrowhead_visible=False,
                        evidence_description="Incomplete arc terminating ambiguously",
                        certainty=ExtractionCertainty.LOW,
                    ),
                ],
            ),
            ambiguities=[
                VisualAmbiguity(element="arrowhead", description="No arrowheads", severity="minor"),
                VisualAmbiguity(element="hop", description="Hop #2 terminates ambiguously", severity="blocking"),
            ],
            requires_teacher_review=True,
            teacher_review_reason="Incomplete hop sequence requires educator inspection.",
        )

        output = gemini_schema_to_visual_evidence(schema, model_id="gemini-3.8-flash")

        assert output.quality_status == QualityStatus.FAINT_READABLE
        assert output.final_answer_marked is None
        assert output.requires_teacher_review is True
        assert output.teacher_review_reason == "Incomplete hop sequence requires educator inspection."
        assert len(output.ambiguities) == 2
        # Confidence is capped when blocking ambiguity is present
        assert output.confidence <= 0.70


class TestGeminiVisionAdapterAccountingAndCircuitBreaker:
    """Tests GeminiVisionAdapter token rates, circuit breaker, and typed exception hierarchy."""

    def test_pricing_schedule_lookup(self):
        """Adapter correctly reports token price rates for supported models."""
        adapter = GeminiVisionAdapter(model_id="gemini-3.8-flash")
        rates = adapter.get_token_rates()
        assert rates["input_per_token"] == 0.75 / 1_000_000.0
        assert rates["output_per_token"] == 3.75 / 1_000_000.0

    def test_call_budget_circuit_breaker(self):
        """Adapter enforces strict maximum call ceiling."""
        adapter = GeminiVisionAdapter(max_calls=2)
        adapter.call_count = 2

        with pytest.raises(RuntimeError, match="Gate 4A Call Budget Exceeded"):
            adapter.extract_from_bytes(b"dummy_bytes", response_id="resp_test")

    def test_typed_exception_hierarchy(self):
        """Typed exceptions inherit from GeminiVisionError."""
        assert issubclass(GeminiAuthenticationError, GeminiVisionError)
        assert issubclass(GeminiQuotaError, GeminiVisionError)
        assert issubclass(GeminiTimeoutError, GeminiVisionError)
        assert issubclass(GeminiModelError, GeminiVisionError)
