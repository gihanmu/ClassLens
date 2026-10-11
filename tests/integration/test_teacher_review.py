"""Integration tests for teacher review and override workflows."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def authenticated_session(client):
    resp = client.post(
        "/api/v1/auth/google",
        json={"demo_mode": True},
    )
    assert resp.status_code == 200
    return {
        "cookies": resp.cookies,
        "csrf_token": resp.json()["csrf_token"],
    }


def test_put_teacher_review_approved_as_is(client, authenticated_session):
    """Verifies teacher approving an AI diagnosis as-is."""
    # Ensure demo data is imported and analyzed on asm_1065658
    asm_id = "asm_1065658"
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

    resp_id = "resp_04255753"
    review_resp = client.put(
        f"/api/v1/responses/{resp_id}/review",
        json={
            "decision": "approved_as_is",
            "notes": "Clear hops, correct answer.",
        },
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["response_id"] == resp_id
    assert data["teacher_review_status"] == "approved_as_is"
    assert data["reviewed_by"] == "usr_sarah_lim"


def test_put_teacher_review_overridden(client, authenticated_session):
    """Verifies teacher overriding an AI diagnosis with custom taxonomy."""
    resp_id = "resp_80545ef3"
    review_resp = client.put(
        f"/api/v1/responses/{resp_id}/review",
        json={
            "decision": "overridden",
            "override_misconception_id": "MISC-ARITH-OFF-BY-ONE",
            "notes": "Confirmed student counted boundary tick marker.",
        },
        headers={"X-Requested-With": "ClassLens"},
        cookies=authenticated_session["cookies"],
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["response_id"] == resp_id
    assert data["teacher_review_status"] == "overridden"

    # Verify audit event
    audit_resp = client.get(
        f"/api/v1/responses/{resp_id}/audit-trail",
        cookies=authenticated_session["cookies"],
    )
    assert audit_resp.status_code == 200
    trail = audit_resp.json()
    assert len(trail) >= 1
    assert trail[-1]["action"] == "overridden"
    assert trail[-1]["notes"] == "Confirmed student counted boundary tick marker."
