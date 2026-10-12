"""Unit tests for Gate 5 Checkpoint C & D: Truthful offline pipeline and teacher workflow."""

import io
import uuid
import pytest
from PIL import Image
from starlette.testclient import TestClient

from services.api.main import app
from services.api.repository.memory_repo import memory_repo, AssessmentDoc, QuestionConfig
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.pipeline import MultiAgentPipeline


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def auth_headers(test_client):
    res = test_client.post("/api/v1/auth/google", json={"demo_mode": True})
    assert res.status_code == 200
    token = res.json()["csrf_token"]
    return {
        "headers": {
            "X-CSRF-Token": token,
            "X-Requested-With": "ClassLens",
        },
        "cookies": res.cookies,
    }


def _create_sample_png():
    img = Image.new("RGB", (1000, 750), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def test_offline_unseen_upload_analysis_truthfully_preserved(test_client, auth_headers):
    """Verifies that analyzing an unseen uploaded worksheet in offline mode never fabricates AI diagnoses."""
    # 1. Create an assessment
    asm_res = test_client.post(
        "/api/v1/assessments",
        json={"title": "Gate 5 Truthfulness Checkpoint"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert asm_res.status_code == 201
    asm_id = asm_res.json()["id"]

    # 2. Upload an unseen worksheet
    file_bytes = _create_sample_png()
    files = {"file": ("unseen_student_work.png", file_bytes, "image/png")}
    data = {"student_id": "stu_truth_01", "student_name": "Student Truth"}
    upl_res = test_client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files=files,
        data=data,
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert upl_res.status_code == 201
    resp_id = upl_res.json()["id"]
    assert resp_id.startswith("resp_")
    assert upl_res.json()["task_status"] == "AWAITING_LIVE_ANALYSIS"
    assert upl_res.json()["answer_status"] == "not_assessed"

    # 3. Trigger analysis on this uploaded worksheet
    an_res = test_client.post(
        f"/api/v1/responses/{resp_id}/analyze",
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert an_res.status_code == 200
    analyzed_doc = an_res.json()

    # 4. Mandatory Gate 5 truthfulness checks:
    # Must remain AWAITING_LIVE_ANALYSIS, not fabricated as COMPLETED with synthetic hops!
    assert analyzed_doc["task_status"] == "AWAITING_LIVE_ANALYSIS"
    assert analyzed_doc["answer_status"] == "not_assessed"
    assert analyzed_doc["reasoning_status"] == "not_assessed"
    assert analyzed_doc["analysis_data"]["diagnosis"]["truthfulness_mode"] == "offline_unseen_requires_live"
    assert "Live multimodal vision model analysis is required" in analyzed_doc["analysis_data"]["diagnosis"]["offline_truthfulness_message"]
    assert analyzed_doc["analysis_data"]["visual_evidence"]["observations"] == []


def test_batch_analysis_truthfully_handles_mixed_or_uploaded_responses(test_client, auth_headers):
    """Verifies batch analysis triggers truthfully preserve uploaded worksheets while processing fixtures."""
    asm_res = test_client.post(
        "/api/v1/assessments",
        json={"title": "Gate 5 Batch Truthfulness Checkpoint"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    asm_id = asm_res.json()["id"]

    # Upload two worksheets
    file_bytes = _create_sample_png()
    test_client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files={"file": ("unseen_1.png", file_bytes, "image/png")},
        data={"student_id": "stu_batch_01", "student_name": "Student 01"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    test_client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files={"file": ("unseen_2.png", file_bytes, "image/png")},
        data={"student_id": "stu_batch_02", "student_name": "Student 02"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )

    # Trigger batch analysis
    an_res = test_client.post(
        f"/api/v1/assessments/{asm_id}/analyze",
        json={"idempotency_key": "job_gate5_test_01"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert an_res.status_code == 202

    # Verify both responses remain truthfully unassessed
    resps = test_client.get(
        f"/api/v1/assessments/{asm_id}/responses",
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    ).json()

    assert len(resps) == 2
    for r in resps:
        assert r["task_status"] == "AWAITING_LIVE_ANALYSIS"
        assert r["answer_status"] == "not_assessed"


def test_teacher_review_and_override_works_on_uploaded_worksheet(test_client, auth_headers):
    """Verifies teacher can manually inspect and submit reviews/overrides for custom uploaded worksheets."""
    asm_res = test_client.post(
        "/api/v1/assessments",
        json={"title": "Gate 5 Teacher Workflow Checkpoint"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    asm_id = asm_res.json()["id"]

    file_bytes = _create_sample_png()
    upl_res = test_client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files={"file": ("student_work.png", file_bytes, "image/png")},
        data={"student_id": "stu_override_01", "student_name": "Student Override"},
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    resp_id = upl_res.json()["id"]

    # Teacher submits manual review / override
    rev_res = test_client.put(
        f"/api/v1/responses/{resp_id}/review",
        json={
            "decision": "overridden",
            "override_misconception_id": "START_POINT_ZERO_MISUNDERSTANDING",
            "notes": "Student started hop at -6 instead of origin 0; verified by teacher manually.",
        },
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["teacher_review_status"] == "overridden"

    # Detail query confirms review persistence
    detail_res = test_client.get(
        f"/api/v1/responses/{resp_id}",
        headers=auth_headers["headers"],
        cookies=auth_headers["cookies"],
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["teacher_review_status"] == "overridden"
    assert detail["teacher_notes"] == "Student started hop at -6 instead of origin 0; verified by teacher manually."


def test_mock_adapter_directly_handles_uploaded_id_truthfully():
    """Verifies that MockAgentAdapter directly protects against hallucinating on upl_ IDs."""
    upl_id = f"upl_{uuid.uuid4().hex[:8]}"
    vis = MockAgentAdapter.get_visual_evidence(upl_id)
    assert vis.provenance == "unseen_upload"
    assert vis.observations == []
    assert vis.confidence == 0.0
    assert vis.requires_teacher_review is True
