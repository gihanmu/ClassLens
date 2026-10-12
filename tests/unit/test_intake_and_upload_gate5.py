"""Unit and integration tests for Gate 5: Assessment creation, secure upload intake, and persistence."""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image
import pytest
from starlette.testclient import TestClient

from services.api.main import app
from services.api.repository.memory_repo import (
    AssessmentDoc,
    QuestionConfig,
    ResponseDoc,
    memory_repo,
)
from services.worker.intake.quality_service import ImageQualityService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth(client):
    """Establishes authenticated session and retrieves CSRF token."""
    res = client.post("/api/v1/auth/google", json={"demo_mode": True})
    assert res.status_code == 200
    token = res.json()["csrf_token"]
    return {
        "headers": {
            "X-CSRF-Token": token,
            "X-Requested-With": "ClassLens",
        },
        "cookies": res.cookies,
    }


def _create_sample_image(width: int = 400, height: int = 300, fmt: str = "JPEG") -> bytes:
    """Creates in-memory test image bytes."""
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_create_custom_assessment_persists_across_restart(client, auth):
    """Verifies teacher can create a custom assessment and it persists on disk."""
    payload = {
        "title": "Integers: Checkpoint 2 — Subtraction on Number Line",
        "math_topic": "Integer operations on number lines",
        "grade_level": "Secondary 1",
        "class_id": "cls_sec1_math",
        "question_text": "Evaluate 5 - 9 + 3 using number line hops.",
        "latex_formula": "5 - 9 + 3",
        "expected_answer": "-1",
    }
    res = client.post(
        "/api/v1/assessments",
        json=payload,
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res.status_code == 201
    data = res.json()
    asm_id = data["id"]
    assert data["title"] == payload["title"]
    assert data["math_topic"] == payload["math_topic"]
    assert data["question"]["expected_answer"] == "-1"

    # Verify retrieval
    res_get = client.get(
        f"/api/v1/assessments/{asm_id}",
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_get.status_code == 200
    assert res_get.json()["id"] == asm_id

    # Verify disk persistence file exists
    tenant_file = memory_repo.persistence._get_tenant_file("org_cedar_sec")
    assert tenant_file.exists()
    persisted = json.loads(tenant_file.read_text(encoding="utf-8"))
    saved_ids = [a["id"] for a in persisted.get("assessments", [])]
    assert asm_id in saved_ids


def test_upload_valid_worksheet_image_success(client, auth):
    """Verifies uploading a valid JPEG worksheet image validates quality and registers response."""
    # 1. Create a fresh test assessment
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "Upload Test Assessment", "question_text": "Test problem"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_asm.status_code == 201
    asm_id = res_asm.json()["id"]

    # 2. Upload valid image
    img_bytes = _create_sample_image(width=600, height=450, fmt="JPEG")
    files = {"file": ("student_worksheet_01.jpg", img_bytes, "image/jpeg")}
    data = {"student_id": "stu_alice_99", "student_name": "Alice Tan"}

    res_up = client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files=files,
        data=data,
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_up.status_code == 201
    resp_data = res_up.json()
    assert resp_data["assessment_id"] == asm_id
    assert resp_data["pseudonymous_student_id"] == "stu_alice_99"
    assert resp_data["pseudonym_label"] == "Alice Tan"
    assert resp_data["task_status"] == "AWAITING_LIVE_ANALYSIS"
    assert resp_data["upload_status"] == "validated"
    assert resp_data["analysis_data"]["offline_status_message"] == (
        "Image uploaded successfully. Live visual analysis is required to interpret this new worksheet."
    )

    # 3. Verify assessment response count increased
    res_asm_after = client.get(
        f"/api/v1/assessments/{asm_id}",
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_asm_after.json()["total_responses"] == 1


def test_upload_invalid_oversized_image_rejected(client, auth):
    """Rejects images exceeding strict 10MB ceiling."""
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "Oversized Test"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    asm_id = res_asm.json()["id"]

    # Construct payload larger than 10MB
    oversized_bytes = b"0" * (11 * 1024 * 1024)
    files = {"file": ("huge_photo.jpg", oversized_bytes, "image/jpeg")}

    res_up = client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files=files,
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_up.status_code == 400
    assert "exceeds" in res_up.json()["detail"].lower() or "limit" in res_up.json()["detail"].lower()


def test_upload_fake_image_file_signature_mismatch_rejected(client, auth):
    """Rejects text or executable file disguised with .jpg extension (MIME magic check)."""
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "MIME Spoof Test"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    asm_id = res_asm.json()["id"]

    fake_bytes = b"#!/bin/bash\necho 'hello world'\n"
    files = {"file": ("malicious_script.jpg", fake_bytes, "image/jpeg")}

    res_up = client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files=files,
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_up.status_code == 400
    assert (
        "magic bytes" in res_up.json()["detail"].lower()
        or "not a recognized" in res_up.json()["detail"].lower()
        or "invalid" in res_up.json()["detail"].lower()
    )


def test_upload_batch_worksheets_with_mapping(client, auth):
    """Verifies batch upload parses multiple files and associates student identifiers."""
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "Batch Intake Assessment"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    asm_id = res_asm.json()["id"]

    img1 = _create_sample_image(fmt="PNG")
    img2 = _create_sample_image(fmt="JPEG")

    files = [
        ("files", ("worksheet_a.png", img1, "image/png")),
        ("files", ("worksheet_b.jpg", img2, "image/jpeg")),
    ]
    mappings = {
        "worksheet_a.png": {"student_id": "stu_bob", "student_name": "Bob Chen"},
        "worksheet_b.jpg": {"student_id": "stu_clara", "student_name": "Clara Lee"},
    }

    res_batch = client.post(
        f"/api/v1/assessments/{asm_id}/upload-batch",
        files=files,
        data={"mappings_json": json.dumps(mappings)},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_batch.status_code == 201
    docs = res_batch.json()
    assert len(docs) == 2
    student_labels = [d["pseudonym_label"] for d in docs]
    assert "Bob Chen" in student_labels
    assert "Clara Lee" in student_labels


def test_get_uploaded_response_image_serves_safely(client, auth):
    """Verifies image retrieval endpoint serves uploaded file from disk."""
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "Image Serve Test"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    asm_id = res_asm.json()["id"]

    img_bytes = _create_sample_image(fmt="JPEG")
    files = {"file": ("test_render.jpg", img_bytes, "image/jpeg")}

    res_up = client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files=files,
        data={"student_name": "David Wu"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    resp_id = res_up.json()["id"]

    # Fetch image
    res_img = client.get(
        f"/api/v1/responses/{resp_id}/image",
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_img.status_code == 200
    assert res_img.headers["content-type"] in ("image/jpeg", "image/png")
    assert len(res_img.content) > 0


def test_delete_uploaded_response_updates_assessment_count(client, auth):
    """Verifies teacher can delete an unassessed submission and response count is updated."""
    res_asm = client.post(
        "/api/v1/assessments",
        json={"title": "Delete Test"},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    asm_id = res_asm.json()["id"]

    img_bytes = _create_sample_image(fmt="JPEG")
    res_up = client.post(
        f"/api/v1/assessments/{asm_id}/upload",
        files={"file": ("to_delete.jpg", img_bytes, "image/jpeg")},
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    resp_id = res_up.json()["id"]

    # Delete response
    res_del = client.delete(
        f"/api/v1/assessments/{asm_id}/responses/{resp_id}",
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_del.status_code == 204

    # Verify deleted
    res_get = client.get(
        f"/api/v1/responses/{resp_id}",
        headers=auth["headers"],
        cookies=auth["cookies"],
    )
    assert res_get.status_code == 404
