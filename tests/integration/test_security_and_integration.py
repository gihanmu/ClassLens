"""Comprehensive security and integration verification test suite."""

from __future__ import annotations

import json
import pytest
from starlette.testclient import TestClient

from services.api.config import settings
from services.api.main import app
from services.api.repository.memory_repo import AssessmentDoc, QuestionConfig, UserDoc, memory_repo


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def cedar_teacher_session(client):
    """Logs in as default teacher Sarah Lim from org_cedar_sec."""
    resp = client.post("/api/v1/auth/google", json={"demo_mode": True})
    assert resp.status_code == 200
    return {
        "cookies": resp.cookies,
        "csrf_token": resp.json()["csrf_token"],
        "user": resp.json()["user"],
    }


def test_csrf_failure_rejection(client, cedar_teacher_session):
    """Enforces that state-mutating requests lacking X-Requested-With header are rejected."""
    # POST without CSRF header
    resp = client.post(
        "/api/v1/assessments",
        json={"title": "Hacked Assessment", "class_id": "cls_001"},
        cookies=cedar_teacher_session["cookies"],
    )
    assert resp.status_code == 403
    assert "CSRF validation failed" in resp.json()["detail"]


def test_session_tampering_rejection(client):
    """Enforces that tampered HMAC signature on session cookie is rejected with 401."""
    fake_payload = json.dumps({"sub": "usr_sarah_lim", "org": "org_cedar_sec"}).encode().hex()
    tampered_cookie = f"{fake_payload}.invalid_tampered_hmac_signature"

    client.cookies.set("__session", tampered_cookie)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Invalid or expired session token" in resp.json()["detail"]


def test_logout_invalidation(client, cedar_teacher_session):
    """Enforces that logout clears session and subsequent requests fail with 401."""
    # Verify authenticated
    client.cookies.update(cedar_teacher_session["cookies"])
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Next call without session cookie must fail with 401
    client.cookies.clear()
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401


def test_production_mode_demo_auth_rejection(client, monkeypatch):
    """Enforces that demo authentication is strictly rejected with 403 in production mode."""
    monkeypatch.setattr(settings, "environment", "production")

    resp = client.post("/api/v1/auth/google", json={"demo_mode": True})
    assert resp.status_code == 403
    assert "strictly prohibited in production mode" in resp.json()["detail"]


def test_cross_tenant_assessment_isolation(client, cedar_teacher_session):
    """Enforces that teachers from org_cedar_sec cannot access assessments belonging to org_raffles_sec."""
    # Seed a foreign assessment from org_raffles_sec
    foreign_asm = AssessmentDoc(
        id="asm_raffles_001",
        class_id="cls_raffles_sec1",
        organization_id="org_raffles_sec",
        title="Raffles Confidential Assessment",
        status="ready",
        question=QuestionConfig(),
    )
    memory_repo.create_assessment(foreign_asm)

    client.cookies.update(cedar_teacher_session["cookies"])

    # Attempt to read foreign assessment
    resp = client.get(f"/api/v1/assessments/{foreign_asm.id}")
    assert resp.status_code == 404
    assert "not found or access denied" in resp.json()["detail"].lower()


def test_cross_tenant_response_and_image_isolation(client, cedar_teacher_session):
    """Enforces that teachers from org_cedar_sec cannot access responses or images belonging to another org."""
    # Seed a foreign assessment and response in org_raffles_sec
    foreign_asm = AssessmentDoc(
        id="asm_foreign_isolation",
        class_id="cls_foreign",
        organization_id="org_raffles_sec",
        title="Foreign Assessment",
        status="ready",
    )
    memory_repo.create_assessment(foreign_asm)

    foreign_responses = memory_repo.import_demo_responses(foreign_asm.id, org_id="org_raffles_sec")
    foreign_resp_id = foreign_responses[0].id

    # Attempt to read foreign response detail as Cedar teacher
    client.cookies.update(cedar_teacher_session["cookies"])
    detail_resp = client.get(f"/api/v1/responses/{foreign_resp_id}")
    assert detail_resp.status_code == 404
    assert "cross-tenant access denied" in detail_resp.json()["detail"]

    # Attempt to read foreign response image as Cedar teacher must also be denied
    image_resp = client.get(f"/api/v1/responses/{foreign_resp_id}/image")
    assert image_resp.status_code == 404
    assert "cross-tenant access denied" in image_resp.json()["detail"]


def test_unauthorized_image_access(client):
    """Enforces that unauthenticated requests to view images return 401."""
    client.cookies.clear()
    resp = client.get("/api/v1/responses/resp_04255753/image")
    assert resp.status_code == 401


def test_duplicate_analysis_requests_idempotency(client, cedar_teacher_session):
    """Enforces that duplicate analysis triggers with identical idempotency keys replay existing job."""
    asm_id = "asm_1065658"
    client.cookies.update(cedar_teacher_session["cookies"])
    headers = {"X-Requested-With": "ClassLens"}

    client.post(f"/api/v1/assessments/{asm_id}/demo-import", headers=headers)

    key = "unique_idemp_key_999"
    # First request
    r1 = client.post(f"/api/v1/assessments/{asm_id}/analyze", json={"idempotency_key": key}, headers=headers)
    assert r1.status_code == 202
    assert r1.json()["idempotent_replay"] is False
    job_id = r1.json()["job_id"]

    # Second duplicate request
    r2 = client.post(f"/api/v1/assessments/{asm_id}/analyze", json={"idempotency_key": key}, headers=headers)
    assert r2.status_code == 202
    assert r2.json()["idempotent_replay"] is True
    assert r2.json()["job_id"] == job_id


def test_teacher_override_audit_consistency(client, cedar_teacher_session):
    """Enforces teacher override persistence and audit log consistency."""
    asm_id = "asm_1065658"
    resp_id = "resp_2292f546"
    client.cookies.update(cedar_teacher_session["cookies"])
    headers = {"X-Requested-With": "ClassLens"}

    # Submit override
    review_resp = client.put(
        f"/api/v1/responses/{resp_id}/review",
        json={
            "decision": "overridden",
            "override_misconception_id": "MISC-DIR-INV",
            "notes": "Pedagogical check: reversed sign vector direction.",
        },
        headers=headers,
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["teacher_review_status"] == "overridden"

    # Query audit trail
    trail_resp = client.get(f"/api/v1/responses/{resp_id}/audit-trail")
    assert trail_resp.status_code == 200
    trail = trail_resp.json()
    assert len(trail) >= 1
    latest = trail[-1]
    assert latest["action"] == "overridden"
    assert latest["teacher_id"] == cedar_teacher_session["user"]["id"]
    assert latest["notes"] == "Pedagogical check: reversed sign vector direction."
    assert latest["new_state"]["teacher_review_status"] == "overridden"


def test_concurrent_background_jobs(client, cedar_teacher_session):
    """Enforces that concurrent batch analysis jobs track items without race conditions."""
    client.cookies.update(cedar_teacher_session["cookies"])
    headers = {"X-Requested-With": "ClassLens"}

    # Create two distinct assessments
    asm1 = client.post("/api/v1/assessments", json={"title": "Concurrent 1", "class_id": "cls_1"}, headers=headers).json()
    asm2 = client.post("/api/v1/assessments", json={"title": "Concurrent 2", "class_id": "cls_2"}, headers=headers).json()

    # Import responses for both
    client.post(f"/api/v1/assessments/{asm1['id']}/demo-import", headers=headers)
    client.post(f"/api/v1/assessments/{asm2['id']}/demo-import", headers=headers)

    # Launch both
    r1 = client.post(f"/api/v1/assessments/{asm1['id']}/analyze", headers=headers)
    r2 = client.post(f"/api/v1/assessments/{asm2['id']}/analyze", headers=headers)
    assert r1.status_code == 202
    assert r2.status_code == 202

    # Status for both should be isolated
    s1 = client.get(f"/api/v1/assessments/{asm1['id']}/status")
    s2 = client.get(f"/api/v1/assessments/{asm2['id']}/status")
    assert s1.status_code == 200
    assert s2.status_code == 200
    assert s1.json()["total_items"] == 13
    assert s2.json()["total_items"] == 13


def test_failed_analysis_resilience(client, cedar_teacher_session):
    """Enforces graceful handling of un-analyzable empty or failed response items."""
    client.cookies.update(cedar_teacher_session["cookies"])
    headers = {"X-Requested-With": "ClassLens"}

    asm = client.post("/api/v1/assessments", json={"title": "Empty Assessment", "class_id": "cls_empty"}, headers=headers).json()

    # Analyzing assessment with 0 responses must fail gracefully with 400
    err_resp = client.post(f"/api/v1/assessments/{asm['id']}/analyze", headers=headers)
    assert err_resp.status_code == 400
    assert "No student responses found" in err_resp.json()["detail"]
