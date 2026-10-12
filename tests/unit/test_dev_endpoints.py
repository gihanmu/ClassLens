"""Unit tests for development-only manual testing endpoints (/api/v1/dev/*).

Validates:
- Development environment restriction (403 when environment != 'development').
- Status endpoint reporting mode, budget, and authorized fixtures.
- Serving authorized synthetic benchmark images with provenance check.
- Rejection of invalid fixture IDs or path traversal attempts.
- Analysis pipeline execution with structured responses and decoupled fields.
- Call budget ceiling enforcement (429 when max_calls reached in live mode).
- Graceful 502 error mapping for Gemini vision failures.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from services.api.config import settings
from services.api.main import app
from services.api.routers.dev import dev_session_tracker
from services.worker.agents.contracts import (
    AnswerStatus,
    CriticAuditOutput,
    DiagnosticOutput,
    FirstSupportedError,
    QualityStatus,
    ReasoningStatus,
    StudentResponseAnalysis,
    VerifiedStep,
    VisualEvidenceOutput,
    VisualObservation,
    CandidateHypothesesOutput,
)
from services.worker.gemini.adapter import GeminiVisionError


@pytest.fixture
def client():
    """Returns a test client session."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_session_counter():
    """Resets dev session call tracker before each test."""
    dev_session_tracker.reset()
    yield
    dev_session_tracker.reset()


def test_dev_status_returns_configuration_and_fixtures(client):
    """Verifies GET /api/v1/dev/status returns correct environment and fixture metadata."""
    resp = client.get("/api/v1/dev/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["environment"] == "development"
    assert data["ai_mode"] in ("mock", "live")
    assert "model" in data
    assert "project" in data
    assert data["max_calls"] == 3
    assert data["calls_used"] == 0
    assert data["calls_remaining"] == 3

    fixtures = data["authorized_fixtures"]
    assert len(fixtures) == 3
    fixture_ids = [f["id"] for f in fixtures]
    assert "case_01_canonical_correct" in fixture_ids
    assert "case_02_off_by_one_error" in fixture_ids
    assert "case_03_ambiguous_incomplete" in fixture_ids


def test_dev_endpoints_forbidden_outside_development(client):
    """Verifies all dev endpoints return 403 when ENVIRONMENT != 'development'."""
    with patch.object(settings, "environment", "production"):
        status_resp = client.get("/api/v1/dev/status")
        assert status_resp.status_code == 403
        assert "strictly disabled" in status_resp.json()["detail"]

        img_resp = client.get("/api/v1/dev/synthetic-fixtures/case_01_canonical_correct/image")
        assert img_resp.status_code == 403

        analyze_resp = client.post(
            "/api/v1/dev/analyze-synthetic",
            json={"fixture_id": "case_01_canonical_correct"},
        )
        assert analyze_resp.status_code == 403


def test_get_synthetic_fixture_image_success(client):
    """Verifies GET /api/v1/dev/synthetic-fixtures/{id}/image serves verified PNGs."""
    resp = client.get("/api/v1/dev/synthetic-fixtures/case_01_canonical_correct/image")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 1000  # Non-empty binary image


def test_get_synthetic_fixture_image_invalid_id_rejected(client):
    """Verifies invalid or malicious fixture IDs are rejected with 400 Bad Request."""
    resp = client.get("/api/v1/dev/synthetic-fixtures/case_99_invalid/image")
    assert resp.status_code == 400
    assert "Invalid fixture ID" in resp.json()["detail"]

    # Traversal attempt
    resp_traversal = client.get("/api/v1/dev/synthetic-fixtures/../../etc/passwd/image")
    assert resp_traversal.status_code in (400, 404)


def test_analyze_synthetic_mock_case_01(client):
    """Verifies analyze-synthetic executes pipeline on Case 1 with mock provider."""
    resp = client.post(
        "/api/v1/dev/analyze-synthetic",
        json={
            "fixture_id": "case_01_canonical_correct",
            "rule_expr": "-6 + 12 - 4",
            "target_value": 2.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["fixture_id"] == "case_01_canonical_correct"
    assert data["mode"] == "mock"
    assert data["is_mock"] is True
    assert data["calls_used"] == 0  # Mock does not consume live budget
    assert data["calls_remaining"] == 3

    analysis = data["analysis"]
    assert analysis["answer_status"] == "correct"
    assert analysis["reasoning_status"] == "supported_correct"
    assert analysis["visual_evidence"]["has_number_line"] is True
    assert len(analysis["diagnosis"]["verified_steps"]) >= 3


def test_analyze_synthetic_mock_case_02_error_detected(client):
    """Verifies analyze-synthetic on Case 2 detects off-by-one procedural error."""
    resp = client.post(
        "/api/v1/dev/analyze-synthetic",
        json={
            "fixture_id": "case_02_off_by_one_error",
            "rule_expr": "-6 + 12 - 4",
            "target_value": 2.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    analysis = data["analysis"]
    assert analysis["answer_status"] == "incorrect"
    assert analysis["reasoning_status"] == "supported_error"
    assert analysis["diagnosis"]["first_supported_error"] is not None


def test_analyze_synthetic_mock_case_03_needs_teacher_review(client):
    """Verifies analyze-synthetic on Case 3 flags incomplete work and requires teacher review."""
    resp = client.post(
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
    assert analysis["needs_teacher_review"] is True


def test_analyze_synthetic_rejects_invalid_fixture(client):
    """Verifies analyze-synthetic rejects unauthorized fixture IDs with 422 or 400."""
    resp = client.post(
        "/api/v1/dev/analyze-synthetic",
        json={"fixture_id": "case_unauthorized"},
    )
    assert resp.status_code in (400, 422)


def test_live_budget_ceiling_enforcement(client):
    """Verifies live mode enforces max_live_calls (3) ceiling and returns 429 when exhausted."""
    # Create a dummy StudentResponseAnalysis representing a live call
    dummy_analysis = StudentResponseAnalysis(
        response_id="case_01_canonical_correct",
        quality_status=QualityStatus.CLEAR,
        visual_evidence=VisualEvidenceOutput(
            quality_status=QualityStatus.CLEAR,
            has_number_line=True,
            confidence=0.95,
            provenance="gemini-3.8-flash",
        ),
        candidate_hypotheses=CandidateHypothesesOutput(
            hypotheses=[],
            detected_strategy="number_line",
            reasoning_completeness="complete",
            confidence=0.9,
        ),
        diagnosis=DiagnosticOutput(
            answer_status=AnswerStatus.CORRECT,
            reasoning_status=ReasoningStatus.SUPPORTED_CORRECT,
            confidence=0.95,
        ),
        critic_audit=CriticAuditOutput(
            approved=True,
            confidence=0.95,
            evidence_grounded=True,
            contradiction_detected=False,
            reinterpretation_needed=False,
            requires_teacher_review=False,
        ),
        answer_status=AnswerStatus.CORRECT,
        reasoning_status=ReasoningStatus.SUPPORTED_CORRECT,
        needs_teacher_review=False,
        is_mock=False,
        model_version="gemini-3.8-flash",
        tokens_consumed=1500,
        cost_estimate_usd=0.0003,
    )

    with patch.object(settings, "ai_mode", "live"), \
         patch.object(settings, "live_inference_enabled", True), \
         patch("services.api.routers.dev.MultiAgentPipeline.analyze_response", return_value=dummy_analysis):

        # Call 1: Allowed
        r1 = client.post("/api/v1/dev/analyze-synthetic", json={"fixture_id": "case_01_canonical_correct"})
        assert r1.status_code == 200
        assert r1.json()["calls_used"] == 1
        assert r1.json()["calls_remaining"] == 2

        # Call 2: Allowed
        r2 = client.post("/api/v1/dev/analyze-synthetic", json={"fixture_id": "case_01_canonical_correct"})
        assert r2.status_code == 200
        assert r2.json()["calls_used"] == 2
        assert r2.json()["calls_remaining"] == 1

        # Call 3: Allowed (Ceiling reached)
        r3 = client.post("/api/v1/dev/analyze-synthetic", json={"fixture_id": "case_01_canonical_correct"})
        assert r3.status_code == 200
        assert r3.json()["calls_used"] == 3
        assert r3.json()["calls_remaining"] == 0

        # Call 4: Blocked by ceiling (429 Too Many Requests)
        r4 = client.post("/api/v1/dev/analyze-synthetic", json={"fixture_id": "case_01_canonical_correct"})
        assert r4.status_code == 429
        assert "Budget Exceeded" in r4.json()["detail"]


def test_gemini_vision_error_returns_502_bad_gateway(client):
    """Verifies GeminiVisionError exceptions are mapped to 502 Bad Gateway with details."""
    with patch("services.api.routers.dev.MultiAgentPipeline.analyze_response", side_effect=GeminiVisionError("Model timeout")):
        resp = client.post(
            "/api/v1/dev/analyze-synthetic",
            json={"fixture_id": "case_01_canonical_correct"},
        )
        assert resp.status_code == 502
        assert "Google Vertex AI Gemini inference error" in resp.json()["detail"]
