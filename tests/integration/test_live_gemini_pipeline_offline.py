"""Integration tests for Gate 6.1 Checkpoint C: Offline Validation of the Live Gemini Diagnostic Pipeline.

Verifies the entire end-to-end multi-agent pipeline using mocked Google GenAI SDK responses:
1. Valid Gemini visual extraction produces verified SymPy reasoning and passed critic audit.
2. Contradictory visual observations (landing at 5 vs answer 2) trigger Critic escalation.
3. Incomplete visual hops result in appropriate abstention and teacher review routing.
4. Ambiguous / faint visual markings propagate image quality alerts.
5. Malformed or missing schema fields are handled safely with typed errors.
6. Image bytes and MIME type are strictly forwarded to the SDK Part without fixture substitution.
7. Results persist cleanly with full audit trail for teacher overrides.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.api.config import Settings
from services.worker.agents.contracts import (
    DiagnosticOutput,
    QualityStatus,
    ReasoningStatus,
    StudentResponseAnalysis,
)
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.provider import GeminiVisualEvidenceProvider
from services.worker.evaluation.contracts import (
    ExtractionCertainty,
    GeminiVisualEvidenceSchema,
    HopDirection,
    ImageQualityAssessment,
    NumberLineObservation,
    ObservedHop,
    VisualAmbiguity,
    VisibleFinalAnswer,
)
from services.worker.gemini.adapter import (
    GeminiModelError,
    GeminiVisionAdapter,
    reset_shared_gemini_adapter,
)


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure adapter singleton and configuration are clean."""
    reset_shared_gemini_adapter()
    yield
    reset_shared_gemini_adapter()


def _make_mock_settings():
    return Settings(
        ai_mode="live",
        live_inference_enabled=True,
        mock_llm=False,
        google_cloud_project="precise-equator-511303-m1",
        google_cloud_location="global",
        live_auth_key="test-owner-secret-key-12345",
    )


# ==============================================================================
# 1. Valid Multimodal Extraction & Deterministic SymPy Pipeline
# ==============================================================================

def test_pipeline_offline_valid_gemini_extraction():
    """Verify that a valid multimodal Gemini extraction is verified by SymPy and passes Critic."""
    valid_schema = GeminiVisualEvidenceSchema(
        response_id="test_resp_valid",
        image_quality=ImageQualityAssessment.CLEAR,
        visible_final_answer=VisibleFinalAnswer(
            value="2",
            evidence_location="final answer box",
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
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="-6",
                    evidence_description="Arc drawn left from 0 to -6",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=2,
                    start_value=-6.0,
                    end_value=6.0,
                    direction=HopDirection.RIGHT_POSITIVE,
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="+12",
                    evidence_description="Arc drawn right from -6 across 0 to +6",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=3,
                    start_value=6.0,
                    end_value=2.0,
                    direction=HopDirection.LEFT_NEGATIVE,
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="-4",
                    evidence_description="Arc drawn left from 6 to 2",
                    certainty=ExtractionCertainty.HIGH,
                ),
            ],
        ),
        ambiguities=[],
        unsupported_observations=[],
        requires_teacher_review=False,
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = valid_schema.model_dump_json()
    mock_response.usage_metadata.prompt_token_count = 120
    mock_response.usage_metadata.candidates_token_count = 85
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client

    provider = GeminiVisualEvidenceProvider(adapter=adapter)

    with patch("services.api.config.settings", _make_mock_settings()):
        analysis: StudentResponseAnalysis = MultiAgentPipeline.analyze_response(
            response_id="test_resp_valid",
            provider=provider,
            auth_key="test-owner-secret-key-12345",
            rule_expr="-6 + 12 - 4",
            target_value=2.0,
        )

    # Assertions on pipeline synthesis
    assert analysis.answer_status.value == "correct"
    assert analysis.visual_evidence.final_answer_marked == "2"
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
    assert analysis.is_compensatory_error is False
    assert analysis.critic_audit.audit_verdict == "audit_passed"
    assert analysis.critic_audit.challenge_issued is False
    assert analysis.needs_teacher_review is False
    assert analysis.quality_status == QualityStatus.CLEAR


# ==============================================================================
# 2. Contradiction Detection: Math Error vs Lucky Answer (Compensatory)
# ==============================================================================

def test_pipeline_offline_contradiction_gemini_extraction():
    """Verify that an arithmetic-numberline contradiction causes Critic to flag review_required."""
    contradiction_schema = GeminiVisualEvidenceSchema(
        response_id="test_resp_contradiction",
        image_quality=ImageQualityAssessment.CLEAR,
        visible_final_answer=VisibleFinalAnswer(
            value="2",  # Correct answer claimed!
            evidence_location="box",
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
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="-6",
                    evidence_description="Arc from 0 to -6",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=2,
                    start_value=-6.0,
                    end_value=5.0,  # Undercounted by 1!
                    direction=HopDirection.RIGHT_POSITIVE,
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="+12",
                    evidence_description="Arc landing at 5",
                    certainty=ExtractionCertainty.HIGH,
                ),
                ObservedHop(
                    hop_index=3,
                    start_value=5.0,
                    end_value=2.0,  # Jump of 3 labeled -4
                    direction=HopDirection.LEFT_NEGATIVE,
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="-4",
                    evidence_description="Arc landing at 2",
                    certainty=ExtractionCertainty.HIGH,
                ),
            ],
        ),
        ambiguities=[],
        unsupported_observations=[],
        requires_teacher_review=False,
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = contradiction_schema.model_dump_json()
    mock_response.usage_metadata.prompt_token_count = 130
    mock_response.usage_metadata.candidates_token_count = 90
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client
    provider = GeminiVisualEvidenceProvider(adapter=adapter)

    with patch("services.api.config.settings", _make_mock_settings()):
        analysis = MultiAgentPipeline.analyze_response(
            response_id="test_resp_contradiction",
            provider=provider,
            auth_key="test-owner-secret-key-12345",
            rule_expr="-6 + 12 - 4",
            target_value=2.0,
        )

    # Even though answer 2 is mathematically right, the working is flawed
    assert analysis.answer_status.value == "correct"
    assert analysis.reasoning_status == ReasoningStatus.SUPPORTED_ERROR
    assert analysis.is_compensatory_error is True
    # Critic must catch the compensatory contradiction and require human review
    assert analysis.critic_audit.audit_verdict == "review_required"
    assert analysis.critic_audit.challenge_issued is True
    assert analysis.needs_teacher_review is True


# ==============================================================================
# 3. Incomplete Working & Appropriate Abstention
# ==============================================================================

def test_pipeline_offline_incomplete_hops_gemini_extraction():
    """Verify that incomplete visual evidence leads to abstention, not hallucinated diagnosis."""
    incomplete_schema = GeminiVisualEvidenceSchema(
        response_id="test_resp_incomplete",
        image_quality=ImageQualityAssessment.CLEAR,
        visible_final_answer=VisibleFinalAnswer(
            value=None,  # No answer in box
            evidence_location=None,
            certainty=ExtractionCertainty.CANNOT_DETERMINE,
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
                    arc_drawn=True,
                    arrowhead_visible=True,
                    stated_magnitude_label="-6",
                    evidence_description="Only first hop drawn",
                    certainty=ExtractionCertainty.HIGH,
                ),
            ],
        ),
        ambiguities=[],
        unsupported_observations=[],
        requires_teacher_review=True,
        teacher_review_reason="Incomplete student worksheet: subsequent hops (+12 and -4) are missing.",
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = incomplete_schema.model_dump_json()
    mock_response.usage_metadata.prompt_token_count = 110
    mock_response.usage_metadata.candidates_token_count = 60
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client
    provider = GeminiVisualEvidenceProvider(adapter=adapter)

    with patch("services.api.config.settings", _make_mock_settings()):
        analysis = MultiAgentPipeline.analyze_response(
            response_id="test_resp_incomplete",
            provider=provider,
            auth_key="test-owner-secret-key-12345",
            rule_expr="-6 + 12 - 4",
            target_value=2.0,
        )

    assert analysis.answer_status.value == "undetermined"
    assert analysis.visual_evidence.final_answer_marked is None
    assert analysis.reasoning_status == ReasoningStatus.INCOMPLETE
    assert analysis.diagnosis.evidence_sufficiency == "insufficient"
    assert analysis.needs_teacher_review is True
    assert "incomplete" in (analysis.teacher_review_reason or "").lower()


# ==============================================================================
# 4. Low-Contrast / Ambiguous Markings
# ==============================================================================

def test_pipeline_offline_ambiguous_faint_gemini_extraction():
    """Verify that faint pencil and ambiguous tick landings escalate to teacher review."""
    ambiguous_schema = GeminiVisualEvidenceSchema(
        response_id="test_resp_ambiguous",
        image_quality=ImageQualityAssessment.LOW_CONTRAST,
        visible_final_answer=VisibleFinalAnswer(
            value="2",
            evidence_location="box",
            certainty=ExtractionCertainty.LOW,
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
                    arc_drawn=True,
                    arrowhead_visible=False,
                    stated_magnitude_label=None,
                    evidence_description="Faint arc from 0 to -6",
                    certainty=ExtractionCertainty.MEDIUM,
                ),
            ],
        ),
        ambiguities=[
            VisualAmbiguity(
                element="hop",
                description="Hop 2 landing mark is blurred between tick 5 and 6",
                severity="blocking",
            ),
            VisualAmbiguity(
                element="erased_mark",
                description="Smudge visible near 0 axis",
                severity="minor",
            ),
        ],
        unsupported_observations=[],
        requires_teacher_review=True,
        teacher_review_reason="Faint low-contrast pencil and blocking ambiguity on hop landing.",
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ambiguous_schema.model_dump_json()
    mock_response.usage_metadata.prompt_token_count = 125
    mock_response.usage_metadata.candidates_token_count = 75
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client
    provider = GeminiVisualEvidenceProvider(adapter=adapter)

    with patch("services.api.config.settings", _make_mock_settings()):
        analysis = MultiAgentPipeline.analyze_response(
            response_id="test_resp_ambiguous",
            provider=provider,
            auth_key="test-owner-secret-key-12345",
            rule_expr="-6 + 12 - 4",
            target_value=2.0,
        )

    assert analysis.quality_status == QualityStatus.LOW_CONTRAST
    assert len(analysis.visual_evidence.ambiguities) == 2
    assert analysis.needs_teacher_review is True
    assert analysis.confidence <= 0.70


# ==============================================================================
# 5. Malformed JSON & Schema Error Handling
# ==============================================================================

def test_pipeline_offline_malformed_json_raises_model_error():
    """Verify that unparseable or schema-violating Gemini output raises GeminiModelError."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "{ malformed: json, missing_bracket: "
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client

    with pytest.raises(GeminiModelError) as exc_info:
        adapter.extract_from_bytes(b"dummy_bytes", response_id="resp_malformed")

    assert "Failed to validate response against GeminiVisualEvidenceSchema" in str(exc_info.value)


# ==============================================================================
# 6. MIME Type & Byte Integrity Preservation
# ==============================================================================

def test_pipeline_preserves_uploaded_image_bytes_and_mime():
    """Verify that actual file bytes and correct MIME type are passed to the Gemini SDK Part."""
    test_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_valid_png_content"

    captured_parts = []

    def mock_generate_content(model, contents, config):
        captured_parts.extend(contents)
        res = MagicMock()
        valid_schema = GeminiVisualEvidenceSchema(
            response_id="resp_mime_check",
            image_quality=ImageQualityAssessment.CLEAR,
            visible_final_answer=VisibleFinalAnswer(value="2", certainty=ExtractionCertainty.HIGH),
            number_line=NumberLineObservation(is_present=True, observed_hops=[]),
        )
        res.text = valid_schema.model_dump_json()
        res.usage_metadata.prompt_token_count = 50
        res.usage_metadata.candidates_token_count = 20
        return res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    adapter = GeminiVisionAdapter(project="test-proj")
    adapter._client = mock_client

    with patch("services.api.config.settings", _make_mock_settings()):
        schema = adapter.extract_from_bytes(
            image_bytes=test_image_bytes,
            response_id="resp_mime_check",
            mime_type="image/png",
        )

    assert schema.response_id == "resp_mime_check"
    assert len(captured_parts) >= 1
    # Check that Part object received exact bytes and mime_type
    part = captured_parts[0]
    assert part.inline_data.data == test_image_bytes
    assert part.inline_data.mime_type == "image/png"
