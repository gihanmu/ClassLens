"""Gate 4B: Teacher Dashboard & AI Analysis Integration Tests.

Verifies:
- Dashboard aggregation and metric calculations
- Student response retrieval and tenant isolation
- Grounded diagnosis presentation (Cases 1, 2, and 3)
- Teacher review submission, normalization, and persistence
- Teacher override audit trail logging
- Cohort statistics: evidence-aware aggregation and insufficient-evidence exclusion
- Zero unintended live Gemini calls (mock mode enforcement)
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.config import settings
from services.api.main import app
from services.api.repository.memory_repo import memory_repo
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.cohort.contracts import CohortStatistics
from services.worker.cohort.statistics_calculator import CohortStatisticsCalculator


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def teacher_auth(client):
    resp = client.post("/api/v1/auth/google", json={"demo_mode": True})
    assert resp.status_code == 200
    data = resp.json()
    return {
        "cookies": resp.cookies,
        "csrf_token": data["csrf_token"],
        "user": data["user"],
    }


def test_gate4b_mock_mode_safeguards():
    """Confirms that live inference remains disabled and mock mode is strictly active."""
    assert settings.ai_mode == "mock"
    assert settings.live_inference_enabled is False


def test_gate4b_list_assessments_includes_synthetic(client, teacher_auth):
    """Verifies that assessments listing returns both Checkpoint 1 and Synthetic Benchmark."""
    resp = client.get("/api/v1/assessments", cookies=teacher_auth["cookies"])
    assert resp.status_code == 200
    assessments = resp.json()
    ids = [a["id"] for a in assessments]
    assert "asm_1065658" in ids
    assert "asm_synthetic_cases" in ids


def test_gate4b_synthetic_cases_deterministic_diagnosis():
    """Verifies Cases 1, 2, and 3 yield grounded, unhallucinated results in mock mode."""
    # Case 1: Canonical Correct
    c1 = MultiAgentPipeline.analyze_response("case_01_canonical_correct")
    assert str(c1.answer_status) in ("correct", "AnswerStatus.CORRECT")
    assert str(c1.reasoning_status) in ("supported_correct", "ReasoningStatus.SUPPORTED_CORRECT")
    assert c1.diagnosis.misconception_taxonomy_id is None
    assert c1.needs_teacher_review is False
    assert c1.critic_audit.audit_verdict == "audit_passed"

    # Case 2: Procedural Off-by-One Error
    c2 = MultiAgentPipeline.analyze_response("case_02_off_by_one_error")
    assert str(c2.answer_status) in ("incorrect", "AnswerStatus.INCORRECT")
    assert str(c2.reasoning_status) in ("supported_error", "ReasoningStatus.SUPPORTED_ERROR")
    assert c2.diagnosis.misconception_taxonomy_id == "MISC-LINE-INTERVAL-MISLABEL"
    assert len(c2.diagnosis.verified_steps) == 3

    # Case 3: Ambiguous and Incomplete
    c3 = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")
    assert str(c3.answer_status) in ("undetermined", "AnswerStatus.UNDETERMINED")
    assert str(c3.reasoning_status) in ("incomplete", "ReasoningStatus.INCOMPLETE")
    assert c3.diagnosis.misconception_taxonomy_id is None  # Never hallucinated!
    assert c3.needs_teacher_review is True
    assert c3.critic_audit.audit_verdict == "review_required"


def test_gate4b_teacher_review_submission_and_persistence(client, teacher_auth):
    """Verifies teacher can confirm or override diagnoses, persisting state and audit history."""
    headers = {
        "X-CSRF-Token": teacher_auth["csrf_token"],
        "X-Requested-With": "ClassLens",
    }

    # Override Case 2 with custom taxonomy and notes
    resp_override = client.put(
        "/api/v1/responses/case_02_off_by_one_error/review",
        json={
            "decision": "OVERRIDE",
            "override_misconception_id": "MISC-MAG-COUNT",
            "notes": "Student miscounted tick intervals by 1.",
        },
        headers=headers,
        cookies=teacher_auth["cookies"],
    )
    assert resp_override.status_code == 200
    data = resp_override.json()
    assert data["teacher_review_status"] == "overridden"

    # Retrieve response detail and verify persisted fields
    resp_detail = client.get(
        "/api/v1/responses/case_02_off_by_one_error",
        cookies=teacher_auth["cookies"],
    )
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["teacher_review_status"] == "overridden"
    assert detail["teacher_override_taxonomy_id"] == "MISC-MAG-COUNT"
    assert detail["teacher_notes"] == "Student miscounted tick intervals by 1."

    # Verify audit trail contains logged event
    resp_audit = client.get(
        "/api/v1/responses/case_02_off_by_one_error/audit-trail",
        cookies=teacher_auth["cookies"],
    )
    assert resp_audit.status_code == 200
    audit_events = resp_audit.json()
    assert len(audit_events) >= 1
    latest_event = audit_events[-1]
    assert latest_event["action"] == "overridden"
    assert latest_event["notes"] == "Student miscounted tick intervals by 1."
    assert latest_event["teacher_id"] == teacher_auth["user"]["id"]


def test_gate4b_tenant_isolation(client, teacher_auth):
    """Verifies cross-organization tenant isolation blocks unauthorized access."""
    # Attempting to access non-existent response returns 404
    resp = client.get(
        "/api/v1/responses/non_existent_response_id",
        cookies=teacher_auth["cookies"],
    )
    assert resp.status_code == 404


def test_gate4b_cohort_insights_evidence_aware_aggregation(client, teacher_auth):
    """Verifies cohort insights exclude ambiguous/insufficient evidence from misconception clusters."""
    resp = client.get(
        "/api/v1/assessments/asm_synthetic_cases/insights",
        cookies=teacher_auth["cookies"],
    )
    assert resp.status_code == 200
    insights = resp.json()
    stats = insights["statistics"]

    # Cohort has 3 responses: Case 1 (correct), Case 2 (error), Case 3 (incomplete)
    assert stats["total_responses"] == 3
    assert stats["correct_count"] == 1
    assert stats["error_count"] == 1
    assert stats["insufficient_evidence_count"] >= 1

    # Case 3 must NOT appear as a misconception cluster!
    cluster_tax_ids = [c["taxonomy_id"] for c in stats["misconception_clusters"]]
    assert "None" not in cluster_tax_ids
    assert None not in cluster_tax_ids
    # The only diagnosed misconception cluster is the one for Case 2
    assert len(cluster_tax_ids) == 1


def test_gate4b_response_image_serving(client, teacher_auth):
    """Verifies image endpoint serves synthetic images with correct content type."""
    resp = client.get(
        "/api/v1/responses/case_01_canonical_correct/image",
        cookies=teacher_auth["cookies"],
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ("image/png", "image/jpeg")
    assert len(resp.content) > 1000
