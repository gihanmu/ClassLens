"""Integration test suite for ClassLens REST API, auth, dispatch, and review workflows."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.main import app
from services.api.repository.memory_repo import memory_repo


@pytest.fixture(scope="module")
def client():
    """Returns a test client session."""
    return TestClient(app)


@pytest.fixture(scope="module")
def authenticated_session(client):
    """Logs in as the demo teacher and extracts session cookies."""
    resp = client.post(
        "/api/v1/auth/google",
        json={"demo_mode": True},
    )
    assert resp.status_code == 200
    cookies = resp.cookies
    data = resp.json()
    csrf_token = data["csrf_token"]
    return {
        "cookies": cookies,
        "csrf_token": csrf_token,
        "user": data["user"],
    }


def test_health_endpoints(client):
    """Verifies /health and /api/v1/health return database and storage readiness fields."""
    for path in ("/health", "/api/v1/health"):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database_backend"] in ("sqlite", "postgresql")
        assert data["database_healthy"] is True
        assert data["schema_version"] == "1.0.0"
        assert data["storage_backend"] in ("local", "gcs")


def test_tc_004_01_demo_login(client):
    """TC-004.01: Verifies demo login sets cookies and returns user profile."""
    resp = client.post(
        "/api/v1/auth/google",
        json={"demo_mode": True},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "user" in data
    assert data["user"]["id"] == "usr_sarah_lim"
    assert data["user"]["email"] == "teacher@classlens.demo"
    assert data["user"]["role"] in ("Secondary 1 Mathematics Teacher", "teacher")
    assert "csrf_token" in data
    assert "__session" in resp.cookies
    assert "csrf_token" in resp.cookies


def test_tc_004_02_csrf_rejection(client, authenticated_session):
    """TC-004.02: Rejects state mutations lacking X-Requested-With header."""
    # Attempt POST /api/v1/assessments without X-Requested-With header
    resp = client.post(
        "/api/v1/assessments",
        json={"title": "Unauthorized CSRF Test", "class_id": "cls_sec1_math"},
        cookies=authenticated_session["cookies"],
    )
    assert resp.status_code == 403
    assert "CSRF validation failed" in resp.json()["detail"]


def test_tc_004_03_demo_import(client, authenticated_session):
    """TC-004.03: Imports 13 response records for Problem #1065658."""
    # First ensure assessment exists
    create_resp = client.post(
        "/api/v1/assessments",
        json={"title": "Integers on Number Line: Checkpoint 1", "class_id": "cls_sec1_math"},
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert create_resp.status_code in (200, 201)
    asm_id = create_resp.json()["id"]

    import_resp = client.post(
        f"/api/v1/assessments/{asm_id}/demo-import",
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert import_resp.status_code == 200
    data = import_resp.json()
    assert data["imported_count"] == 13
    assert len(data["responses"]) == 13


def test_tc_004_04_05_06_batch_analyze_and_response_detail(client, authenticated_session):
    """TC-004.04, TC-004.05, TC-004.06: Full batch analysis and student response inspection."""
    # 1. Create assessment and import responses
    create_resp = client.post(
        "/api/v1/assessments",
        json={"title": "Integers Batch Check", "class_id": "cls_sec1_math"},
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    asm_id = create_resp.json()["id"]

    client.post(
        f"/api/v1/assessments/{asm_id}/demo-import",
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )

    # 2. TC-004.04: Trigger batch analysis
    analyze_resp = client.post(
        f"/api/v1/assessments/{asm_id}/analyze",
        json={"idempotency_key": "test_idemp_key_001"},
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert analyze_resp.status_code == 202
    job_data = analyze_resp.json()
    assert "job_id" in job_data
    assert job_data["total_items"] == 13
    assert job_data["idempotent_replay"] is False

    # 3. Test idempotent replay
    replay_resp = client.post(
        f"/api/v1/assessments/{asm_id}/analyze",
        json={"idempotency_key": "test_idemp_key_001"},
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert replay_resp.status_code == 202
    assert replay_resp.json()["idempotent_replay"] is True

    # 4. TC-004.05: Poll status
    status_resp = client.get(
        f"/api/v1/assessments/{asm_id}/status",
        cookies=authenticated_session["cookies"],
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["total_items"] == 13
    assert status_data["completed_items"] == 13
    assert status_data["failed_items"] == 0

    # 5. TC-004.06: Get response detail
    # Pick response resp_80545ef3 (off-by-one error)
    detail_resp = client.get(
        "/api/v1/responses/resp_80545ef3",
        cookies=authenticated_session["cookies"],
    )
    assert detail_resp.status_code == 200
    res_data = detail_resp.json()

    assert res_data["response_id"] == "resp_80545ef3"
    assert "visual_evidence" in res_data
    assert "candidate_hypotheses" in res_data
    assert "diagnosis" in res_data
    assert "critic_audit" in res_data
    assert res_data["diagnosis"]["misconception_taxonomy_id"] == "MISC-ARITH-OFF-BY-ONE"
    assert res_data["is_mock"] is True


def test_teacher_override_and_audit_trail(client, authenticated_session):
    """Verifies teacher override workflow and audit event capture."""
    target_resp_id = "resp_8ef9d302"

    override_resp = client.post(
        f"/api/v1/responses/{target_resp_id}/override",
        json={
            "action": "overridden",
            "override_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
            "notes": "Verified student started counting at -6 instead of moving 1 unit.",
        },
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert override_resp.status_code == 200
    updated_doc = override_resp.json()
    assert updated_doc["teacher_review_status"] == "overridden"
    assert updated_doc["teacher_notes"] is not None

    # Retrieve audit trail
    audit_resp = client.get(
        f"/api/v1/responses/{target_resp_id}/audit-trail",
        cookies=authenticated_session["cookies"],
    )
    assert audit_resp.status_code == 200
    trail = audit_resp.json()
    assert len(trail) >= 1
    latest_event = trail[-1]
    assert latest_event["teacher_id"] == "usr_sarah_lim"
    assert latest_event["action"] == "overridden"


def test_cohort_insights_api(client, authenticated_session):
    """Verifies GET /api/v1/assessments/{id}/insights returns statistics and intelligence."""
    # Pre-seeded assessment asm_1065658
    asm_id = "asm_1065658"

    # Make sure responses are imported and analyzed
    client.post(
        f"/api/v1/assessments/{asm_id}/demo-import",
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    client.post(
        f"/api/v1/assessments/{asm_id}/analyze",
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )

    insights_resp = client.get(
        f"/api/v1/assessments/{asm_id}/insights",
        cookies=authenticated_session["cookies"],
    )
    assert insights_resp.status_code == 200
    data = insights_resp.json()

    assert "statistics" in data
    assert "intelligence" in data
    stats = data["statistics"]
    assert stats["total_responses"] == 13
    assert stats["correct_count"] == 7
    assert stats["error_count"] == 4

    intelligence = data["intelligence"]
    assert len(intelligence["differentiated_actions"]) == 3
    assert len(intelligence["formative_exit_ticket"]) == 3
