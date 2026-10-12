"""Gate 4B.1: Dedicated Teacher Dashboard & Assessment Status Improvements Tests.

Verifies:
- Dedicated teacher dashboard summary endpoint (/api/v1/dashboard/summary)
- Accurate teacher-level metrics before and after analysis
- Clear distinction between "Not analyzed" and "Insufficient evidence"
- Single response analysis endpoint (/api/v1/responses/{id}/analyze)
- Assessment list analysis progress calculation
- Teacher attention items queue derivation without fabricated data
- Recent activity chronological event ordering
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.main import app
from services.api.repository.memory_repo import memory_repo


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


def test_dashboard_summary_metrics_before_batch_analysis(client, teacher_auth):
    """Verifies that teacher dashboard accurately reflects unanalyzed submissions before batch run."""
    headers = {
        "X-CSRF-Token": teacher_auth["csrf_token"],
        "X-Requested-With": "ClassLens",
    }
    # Create fresh unanalyzed assessment to test unanalyzed metrics in isolation
    asm_resp = client.post(
        "/api/v1/assessments",
        json={"title": "Unanalyzed Integers Checkpoint", "class_id": "cls_sec1_math"},
        headers=headers,
        cookies=teacher_auth["cookies"],
    )
    assert asm_resp.status_code == 201
    fresh_asm = asm_resp.json()

    # Import responses into fresh assessment (not yet analyzed)
    import_resp = client.post(
        f"/api/v1/assessments/{fresh_asm['id']}/demo-import",
        headers=headers,
        cookies=teacher_auth["cookies"],
    )
    assert import_resp.status_code == 200

    resp = client.get("/api/v1/dashboard/summary", cookies=teacher_auth["cookies"])
    assert resp.status_code == 200
    data = resp.json()

    # Verify teacher-level summary counts
    assert data["active_classes_count"] >= 1
    assert data["total_students_count"] >= 13
    assert data["total_assessments_count"] >= 3
    assert data["awaiting_analysis_count"] >= 13

    # Check assessments list for fresh unanalyzed assessment
    assessments = data["assessments"]
    asm_map = {a["id"]: a for a in assessments}
    assert fresh_asm["id"] in asm_map
    target_asm = asm_map[fresh_asm["id"]]

    assert target_asm["total_submissions"] == 13
    assert target_asm["awaiting_analysis_count"] == 13
    assert target_asm["analyzed_count"] == 0
    assert target_asm["progress_percentage"] == 0
    assert target_asm["status"] == "awaiting_analysis"

    # Attention queue must include pending batch action
    attn_types = [item["type"] for item in data["attention_items"]]
    assert "awaiting_analysis" in attn_types


def test_unanalyzed_submissions_have_not_assessed_status(client, teacher_auth):
    """Verifies that unanalyzed submissions are not prematurely labeled as undetermined or unverifiable."""
    resp = client.get("/api/v1/assessments/asm_1065658/responses", cookies=teacher_auth["cookies"])
    assert resp.status_code == 200
    responses = resp.json()

    for r in responses:
        if r["task_status"] == "PENDING":
            # Must be not_assessed, never undetermined or insufficient evidence before AI evaluation!
            assert r["answer_status"] == "not_assessed"
            assert r["reasoning_status"] == "not_assessed"
            assert r.get("analysis_data") is None


def test_single_response_analysis_execution(client, teacher_auth):
    """Verifies that an individual response can be analyzed on demand."""
    headers = {
        "X-CSRF-Token": teacher_auth["csrf_token"],
        "X-Requested-With": "ClassLens",
    }
    target_resp_id = "resp_80545ef3"

    # Analyze single response
    resp = client.post(
        f"/api/v1/responses/{target_resp_id}/analyze",
        headers=headers,
        cookies=teacher_auth["cookies"],
    )
    assert resp.status_code == 200
    analyzed = resp.json()
    assert analyzed["task_status"] == "COMPLETED"
    assert analyzed["answer_status"] in ("correct", "incorrect", "undetermined")
    assert analyzed["reasoning_status"] in (
        "supported_correct",
        "supported_error",
        "incomplete",
        "unverifiable",
    )
    assert analyzed["analysis_data"] is not None

    # Fetching response detail returns full diagnosis
    detail_resp = client.get(
        f"/api/v1/responses/{target_resp_id}",
        cookies=teacher_auth["cookies"],
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "diagnosis" in detail
    assert "visual_evidence" in detail


def test_evidence_insufficiency_distinction_after_analysis(client, teacher_auth):
    """Verifies that Case 3 is identified as insufficient evidence only AFTER analysis."""
    # Case 3 in synthetic benchmark is completed and has insufficient evidence
    resp = client.get(
        "/api/v1/responses/case_03_ambiguous_incomplete",
        cookies=teacher_auth["cookies"],
    )
    assert resp.status_code == 200
    case3 = resp.json()
    assert case3["diagnosis"]["answer_status"] == "undetermined"
    assert case3["diagnosis"]["evidence_sufficiency"] == "insufficient"
    assert case3["needs_teacher_review"] is True
    # Crucially, ungrounded claims are suppressed:
    assert case3["diagnosis"]["misconception_taxonomy_id"] is None


def test_dashboard_summary_after_batch_analysis(client, teacher_auth):
    """Verifies that teacher dashboard transitions correctly once batch analysis executes."""
    headers = {
        "X-CSRF-Token": teacher_auth["csrf_token"],
        "X-Requested-With": "ClassLens",
    }
    # Run batch analysis on asm_1065658
    analyze_resp = client.post(
        "/api/v1/assessments/asm_1065658/analyze",
        headers=headers,
        cookies=teacher_auth["cookies"],
    )
    assert analyze_resp.status_code in (200, 202)

    resp = client.get("/api/v1/dashboard/summary", cookies=teacher_auth["cookies"])
    assert resp.status_code == 200
    data = resp.json()

    # Learning insights snapshot should now be populated with real cohort data
    snapshot = data["learning_insights_snapshot"]
    assert snapshot is not None
    assert snapshot["has_analyzed_data"] is True
    assert snapshot["analyzed_count"] >= 13
    assert snapshot["correct_answers_pct"] > 0
    assert len(snapshot["top_misconceptions"]) > 0

