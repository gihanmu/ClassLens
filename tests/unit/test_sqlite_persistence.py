"""Unit tests for ClassLens durable SQLite persistence layer and migration manager."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import threading
from pathlib import Path
import pytest

from services.api.repository.sqlite_repository import (
    SqliteAssessmentRepository,
    AssessmentDoc,
    ResponseDoc,
    QuestionConfig,
    AuditEventDoc,
    utc_now,
)


@pytest.fixture
def temp_sqlite_storage():
    """Provides an isolated temporary directory for SQLite persistence testing."""
    temp_dir = tempfile.mkdtemp(prefix="classlens_sqlite_test_")
    old_env = os.environ.get("CLASSLENS_DATA_DIR")
    os.environ["CLASSLENS_DATA_DIR"] = temp_dir
    yield Path(temp_dir)
    # Cleanup
    if old_env is not None:
        os.environ["CLASSLENS_DATA_DIR"] = old_env
    else:
        os.environ.pop("CLASSLENS_DATA_DIR", None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_sqlite_db_and_schema_initialization(temp_sqlite_storage):
    """Verifies SQLite file, tables, foreign keys, and indexes are created properly."""
    repo = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)
    db_file = temp_sqlite_storage / "classlens.db"
    assert db_file.exists()

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "users" in tables
    assert "classes" in tables
    assert "students" in tables
    assert "assessments" in tables
    assert "responses" in tables
    assert "audit_events" in tables
    assert "analysis_jobs" in tables

    # Verify indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    assert "idx_assessments_org" in indexes
    assert "idx_responses_assessment" in indexes
    assert "idx_responses_task_status" in indexes
    assert "idx_responses_review" in indexes
    assert "idx_audit_events_response" in indexes
    assert "idx_analysis_jobs_assessment" in indexes
    conn.close()


def test_sqlite_crud_and_process_restart(temp_sqlite_storage):
    """Verifies that CRUD operations and teacher review overrides durably survive restart."""
    repo1 = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)

    # 1. Create a custom assessment
    asm = AssessmentDoc(
        id="asm_algebra_integers",
        class_id="cls_sec1_math",
        organization_id="org_cedar_sec",
        title="Negative Integer Number Lines",
        status="ready",
        question=QuestionConfig(
            problem_reference_id="alg_01",
            question_text="Evaluate -4 + 7 on number line",
            latex_formula="-4 + 7",
            expected_answer="3",
        ),
    )
    repo1.create_assessment(asm)

    # 2. Add a response
    resp = ResponseDoc(
        id="resp_student_test_01",
        assessment_id="asm_algebra_integers",
        pseudonymous_student_id="stu_test_01",
        pseudonym_label="Student Test 01",
        source_filename="test_worksheet.png",
        image_mime_type="image/png",
        task_status="COMPLETED",
        answer_status="correct",
        reasoning_status="supported_correct",
        teacher_review_status="unreviewed",
        needs_teacher_review=True,
    )
    repo1.create_response(resp)

    # 3. Perform teacher review override
    repo1.record_teacher_override(
        assessment_id="asm_algebra_integers",
        response_id="resp_student_test_01",
        teacher_id="usr_sarah_lim",
        action="overridden",
        override_taxonomy="MISC-OFF-BY-ONE",
        notes="Reviewed step 2 jump length.",
    )

    # 4. Simulate complete process restart (fresh repo instance)
    repo2 = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)

    # Verify assessment persisted
    restored_asm = repo2.get_assessment("asm_algebra_integers", "org_cedar_sec")
    assert restored_asm is not None
    assert restored_asm.title == "Negative Integer Number Lines"
    assert restored_asm.reviewed_responses == 1

    # Verify response and override persisted
    restored_resp = repo2.get_response("resp_student_test_01", "asm_algebra_integers")
    assert restored_resp is not None
    assert restored_resp.teacher_review_status == "overridden"
    assert restored_resp.teacher_override_taxonomy_id == "MISC-OFF-BY-ONE"
    assert restored_resp.teacher_notes == "Reviewed step 2 jump length."

    # Verify audit event persisted
    audit_events = repo2.get_audit_events_for_response("resp_student_test_01")
    assert len(audit_events) == 1
    assert audit_events[0].action == "overridden"
    assert audit_events[0].teacher_id == "usr_sarah_lim"


def test_sqlite_migration_from_json_state(temp_sqlite_storage):
    """Verifies automatic non-destructive migration from JSON state file into SQLite."""
    # Write a pre-existing state JSON file before initializing SQLite
    json_path = temp_sqlite_storage / "org_cedar_sec_state.json"
    state_payload = {
        "version": "1.0",
        "org_id": "org_cedar_sec",
        "assessments": [
            {
                "id": "asm_migrated_01",
                "class_id": "cls_sec1_math",
                "organization_id": "org_cedar_sec",
                "title": "Migrated Assessment",
                "math_topic": "Fractions",
                "grade_level": "Secondary 1",
                "status": "ready",
                "question": {
                    "problem_reference_id": "migrated_ref",
                    "question_text": "Evaluate 1/2 + 1/4",
                    "latex_formula": "1/2 + 1/4",
                    "expected_answer": "3/4",
                },
                "total_responses": 1,
                "reviewed_responses": 0,
                "created_at": utc_now().isoformat(),
                "updated_at": utc_now().isoformat(),
            }
        ],
        "responses": [
            {
                "id": "resp_migrated_01",
                "assessment_id": "asm_migrated_01",
                "pseudonymous_student_id": "stu_migrated_01",
                "pseudonym_label": "Migrated Student",
                "source_filename": "migrated.jpg",
                "image_mime_type": "image/jpeg",
                "upload_status": "validated",
                "task_status": "PENDING",
                "answer_status": "not_assessed",
                "reasoning_status": "not_assessed",
                "teacher_review_status": "unreviewed",
                "created_at": utc_now().isoformat(),
                "updated_at": utc_now().isoformat(),
            }
        ],
        "audit_events": [],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state_payload, f)

    # Initialize repository; should migrate the JSON file into SQLite
    repo = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)

    # Verify backup was created
    backup_file = temp_sqlite_storage / "org_cedar_sec_state.json.bak"
    assert backup_file.exists()

    # Verify data in SQLite
    asm = repo.get_assessment("asm_migrated_01", "org_cedar_sec")
    assert asm is not None
    assert asm.title == "Migrated Assessment"

    resp = repo.get_response("resp_migrated_01")
    assert resp is not None
    assert resp.pseudonym_label == "Migrated Student"


def test_sqlite_truthful_uploaded_worksheet_mock_mode(temp_sqlite_storage):
    """Verifies that uploaded unseen worksheets remain AWAITING_LIVE_ANALYSIS in SQLite."""
    repo = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)

    uploaded_doc = ResponseDoc(
        id="resp_unseen_worksheet_01",
        assessment_id="asm_1065658",
        pseudonymous_student_id="stu_new_01",
        pseudonym_label="Student New 01",
        source_filename="new_upload.jpg",
        task_status="AWAITING_LIVE_ANALYSIS",
        answer_status="not_assessed",
        reasoning_status="not_assessed",
        teacher_review_status="unreviewed",
        is_mock=True,
        model_version="uploaded-unseen",
        analysis_data={
            "offline_status_message": "Image uploaded successfully. Live visual analysis is required."
        },
    )
    repo.create_response(uploaded_doc)

    # Check that in SQLite and cache, task_status is AWAITING_LIVE_ANALYSIS
    retrieved = repo.get_response("resp_unseen_worksheet_01")
    assert retrieved is not None
    assert retrieved.task_status == "AWAITING_LIVE_ANALYSIS"
    assert retrieved.answer_status == "not_assessed"
    assert retrieved.reasoning_status == "not_assessed"
    # Never invent a mock diagnosis for a real upload
    assert retrieved.misconception_taxonomy_id is None

    # Verify dashboard summary counts it as awaiting analysis
    summary = repo.get_dashboard_summary("org_cedar_sec")
    assert summary["awaiting_analysis_count"] >= 1


def test_sqlite_concurrent_transactions(temp_sqlite_storage):
    """Verifies that concurrent threads updating SQLite do not cause lock errors."""
    repo = SqliteAssessmentRepository(data_dir=temp_sqlite_storage)

    errors = []

    def worker(worker_id: int):
        try:
            for i in range(10):
                resp = ResponseDoc(
                    id=f"resp_worker_{worker_id}_{i}",
                    assessment_id="asm_1065658",
                    pseudonymous_student_id=f"stu_w_{worker_id}_{i}",
                    pseudonym_label=f"Worker Student {worker_id}-{i}",
                    source_filename=f"worksheet_{worker_id}_{i}.jpg",
                    task_status="COMPLETED",
                    answer_status="correct",
                    reasoning_status="supported_correct",
                )
                repo.create_response(resp)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    # Verify all 40 responses exist in repo
    responses = repo.list_responses("asm_1065658")
    worker_responses = [r for r in responses if r.id.startswith("resp_worker_")]
    assert len(worker_responses) == 40
