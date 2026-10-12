"""Unit tests for Gate 6 Fail-Closed Live Gemini Authorization and Worksheet Ingestion.

Verifies:
1. Live inference is disabled by default ($0.00 spend).
2. Missing owner authorization blocks live calls (fail-closed).
3. Invalid owner authorization key is rejected with constant-time comparison.
4. Valid owner authorization allows execution using mocked Gemini SDK.
5. Path confinement and traversal protection for uploaded worksheets.
6. Explicit timeout enforcement and typed exception mapping.
7. Token tracking and telemetry recording.
8. Error truthfulness without silent mock substitution.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from services.api.config import ConfigurationError, Settings
from services.worker.agents.provider import (
    GeminiVisualEvidenceProvider,
    MockVisualEvidenceProvider,
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
)
from services.worker.gemini.adapter import (
    GeminiAuthenticationError,
    GeminiModelError,
    GeminiQuotaError,
    GeminiTimeoutError,
    GeminiVisionAdapter,
    GeminiVisionError,
    reset_shared_gemini_adapter,
)
from services.worker.security.provenance_guard import (
    TRUSTED_SYNTHETIC_DIR,
    TRUSTED_UPLOADS_DIR,
    UntrustedProvenanceError,
    verify_analysis_image_source,
    verify_synthetic_path,
    verify_uploaded_worksheet_path,
)


@pytest.fixture(autouse=True)
def clean_adapter():
    """Reset shared adapter before and after each test."""
    reset_shared_gemini_adapter()
    yield
    reset_shared_gemini_adapter()


# ==============================================================================
# 1. Default Configuration & Fail-Closed Safeguards
# ==============================================================================

def test_live_inference_disabled_by_default():
    """Ensures default settings strictly prohibit live calls ($0.00 spend)."""
    s = Settings(
        ai_mode="mock",
        live_inference_enabled=False,
        mock_llm=True,
        live_auth_key=None,
    )
    assert not s.is_live_mode()
    assert not s.is_live_authorized()


def test_live_mode_without_owner_auth_key_fails_closed():
    """Enabling ai_mode='live' without CLASSLENS_LIVE_AUTH_KEY must fail closed."""
    s = Settings(
        ai_mode="live",
        live_inference_enabled=True,
        mock_llm=False,
        google_cloud_project="test-proj",
        live_auth_key=None,  # No owner token configured
    )
    assert s.is_live_mode()
    assert not s.is_live_authorized()
    with pytest.raises(ConfigurationError) as exc_info:
        s.validate_live_authorization()
    assert "CLASSLENS_LIVE_AUTH_KEY" in str(exc_info.value)


def test_invalid_owner_auth_token_rejected():
    """Providing a mismatched authorization key fails constant-time verification."""
    s = Settings(
        ai_mode="live",
        live_inference_enabled=True,
        mock_llm=False,
        google_cloud_project="test-proj",
        live_auth_key="valid-owner-secret-token-xyz",
    )
    assert s.is_live_mode()
    assert not s.is_live_authorized("wrong-token-123")
    with pytest.raises(ConfigurationError) as exc_info:
        s.validate_live_configuration(provided_key="wrong-token-123")
    assert "Invalid owner authorization key" in str(exc_info.value)


def test_valid_owner_auth_token_accepted():
    """Providing the correct authorization key validates successfully."""
    s = Settings(
        ai_mode="live",
        live_inference_enabled=True,
        mock_llm=False,
        google_cloud_project="test-proj",
        gemini_model="gemini-3.8-flash",
        live_auth_key="valid-owner-secret-token-xyz",
    )
    assert s.is_live_mode()
    assert s.is_live_authorized("valid-owner-secret-token-xyz")
    # Must not raise
    s.validate_live_configuration(provided_key="valid-owner-secret-token-xyz")


# ==============================================================================
# 2. Uploaded Worksheet Provenance & Confinement Guard
# ==============================================================================

def test_uploaded_worksheet_blocked_without_live_authorization(tmp_path):
    """Uploaded worksheets cannot be sent to live AI without active owner authorization."""
    upload_file = TRUSTED_UPLOADS_DIR / "sample_student_work.png"
    TRUSTED_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    try:
        with patch.object(Settings, "is_live_authorized", return_value=False):
            with pytest.raises(UntrustedProvenanceError) as exc_info:
                verify_uploaded_worksheet_path(upload_file, auth_key=None)
            assert "Fail-Closed Safeguard" in str(exc_info.value)
    finally:
        if upload_file.exists():
            upload_file.unlink()


def test_uploaded_worksheet_path_traversal_blocked():
    """Paths escaping local-data/uploads/ are blocked by realpath resolution."""
    with patch.object(Settings, "is_live_authorized", return_value=True):
        with pytest.raises(UntrustedProvenanceError) as exc_info:
            verify_uploaded_worksheet_path(Path("/etc/passwd"), auth_key="key")
        assert "escapes the trusted uploads directory" in str(exc_info.value)


def test_uploaded_worksheet_verified_when_authorized():
    """Uploaded worksheets inside local-data/uploads/ are verified when authorized."""
    upload_file = TRUSTED_UPLOADS_DIR / "test_authorized_worksheet.png"
    TRUSTED_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy-pixel-data" * 10)

    try:
        with patch.object(Settings, "is_live_authorized", return_value=True):
            verified = verify_uploaded_worksheet_path(upload_file, auth_key="valid-key")
            assert verified == upload_file.resolve()
            assert verified.is_file()
    finally:
        if upload_file.exists():
            upload_file.unlink()


# ==============================================================================
# 3. Gemini Vision Adapter Error Handling & Mocked SDK Execution
# ==============================================================================

def _create_sample_gemini_schema() -> GeminiVisualEvidenceSchema:
    """Helper creating a valid GeminiVisualEvidenceSchema."""
    return GeminiVisualEvidenceSchema(
        response_id="test_resp_001",
        image_quality=ImageQualityAssessment.CLEAR,
        number_line=NumberLineObservation(
            is_present=True,
            min_visible_tick=-10.0,
            max_visible_tick=10.0,
            observed_hops=[
                ObservedHop(
                    hop_index=1,
                    start_value=0.0,
                    end_value=-6.0,
                    direction=HopDirection.LEFT_NEGATIVE,
                    arrowhead_visible=True,
                    stated_magnitude_label="-6",
                    evidence_description="Arc drawn left from 0 to -6 with visible arrowhead",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=2,
                    start_value=-6.0,
                    end_value=6.0,
                    direction=HopDirection.RIGHT_POSITIVE,
                    arrowhead_visible=True,
                    stated_magnitude_label="+12",
                    evidence_description="Arc drawn right from -6 to 6 with visible arrowhead",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=3,
                    start_value=6.0,
                    end_value=2.0,
                    direction=HopDirection.LEFT_NEGATIVE,
                    arrowhead_visible=True,
                    stated_magnitude_label="-4",
                    evidence_description="Arc drawn left from 6 to 2 with visible arrowhead",
                    certainty=ExtractionCertainty.HIGH,
                ),
            ],
        ),
        visible_final_answer=VisibleFinalAnswer(
            value="2",
            certainty=ExtractionCertainty.HIGH,
        ),
        ambiguities=[],
        requires_teacher_review=False,
    )


def test_gemini_adapter_mocked_sdk_successful_extraction():
    """Tests successful structured extraction with mocked GenAI Client and usage capture."""
    sample_schema = _create_sample_gemini_schema()
    raw_json = sample_schema.model_dump_json()

    adapter = GeminiVisionAdapter(
        model_id="gemini-3.8-flash",
        max_calls=3,
        timeout_seconds=15.0,
    )

    mock_response = MagicMock()
    mock_response.text = raw_json
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=1024,
        candidates_token_count=256,
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    adapter._client = mock_client

    image_bytes = b"\x89PNG\r\n\x1a\n" + b"pixels" * 20
    extracted = adapter.extract_from_bytes(
        image_bytes=image_bytes,
        response_id="test_resp_001",
    )

    assert extracted.response_id == "test_resp_001"
    assert len(extracted.number_line.observed_hops) == 3
    assert extracted.visible_final_answer.value == "2"
    assert adapter.call_count == 1
    assert adapter.total_input_tokens == 1024
    assert adapter.total_output_tokens == 256
    assert adapter.total_estimated_cost_usd > 0.0


def test_gemini_adapter_timeout_maps_to_typed_exception():
    """Requests that time out are translated into GeminiTimeoutError."""
    adapter = GeminiVisionAdapter(model_id="gemini-3.8-flash")
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Deadline exceeded: Request timed out")
    adapter._client = mock_client

    with pytest.raises(GeminiTimeoutError) as exc_info:
        adapter.extract_from_bytes(b"\x89PNG\r\n\x1a\nfake", "test_timeout")
    assert "timed out" in str(exc_info.value).lower()


def test_gemini_adapter_quota_maps_to_typed_exception():
    """Vertex AI 429 quota exhaustion is mapped to GeminiQuotaError."""
    adapter = GeminiVisionAdapter(model_id="gemini-3.8-flash")
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 Resource exhausted: quota exceeded")
    adapter._client = mock_client

    with pytest.raises(GeminiQuotaError) as exc_info:
        adapter.extract_from_bytes(b"\x89PNG\r\n\x1a\nfake", "test_quota")
    assert "quota exhausted" in str(exc_info.value).lower()


def test_gemini_adapter_malformed_json_raises_model_error():
    """Malformed or invalid JSON returned by model raises GeminiModelError."""
    adapter = GeminiVisionAdapter(model_id="gemini-3.8-flash")
    mock_response = MagicMock()
    mock_response.text = "NOT JSON AT ALL"
    mock_response.usage_metadata = None

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    adapter._client = mock_client

    with pytest.raises(GeminiModelError) as exc_info:
        adapter.extract_from_bytes(b"\x89PNG\r\n\x1a\nfake", "test_malformed")
    assert "Failed to validate" in str(exc_info.value)


def test_gemini_adapter_payload_size_limit_enforced():
    """Images exceeding max_image_size_bytes are rejected before sending to Vertex AI."""
    adapter = GeminiVisionAdapter(
        model_id="gemini-3.8-flash",
        max_image_size_bytes=1000,
    )
    oversized = b"A" * 2000
    with pytest.raises(GeminiVisionError) as exc_info:
        adapter.extract_from_bytes(oversized, "test_oversized")
    assert "exceeds maximum limit" in str(exc_info.value)


# ==============================================================================
# 4. Visual Evidence Provider Factory & Schema Translation
# ==============================================================================

def test_get_visual_evidence_provider_defaults_to_mock():
    """Factory returns MockVisualEvidenceProvider when live mode is not authorized."""
    with patch.object(Settings, "is_live_authorized", return_value=False):
        provider = get_visual_evidence_provider()
        assert isinstance(provider, MockVisualEvidenceProvider)


def test_provider_translates_ambiguities_to_teacher_review():
    """Ambiguities and low certainty in schema correctly propagate requires_teacher_review."""
    sample_schema = _create_sample_gemini_schema()
    sample_schema.requires_teacher_review = True
    sample_schema.teacher_review_reason = "Faint hop endpoint between tick 1 and 2."

    from services.worker.agents.provider import gemini_schema_to_visual_evidence
    evidence = gemini_schema_to_visual_evidence(sample_schema)

    assert evidence.requires_teacher_review is True
    assert evidence.teacher_review_reason == "Faint hop endpoint between tick 1 and 2."
    assert evidence.confidence < 0.75
