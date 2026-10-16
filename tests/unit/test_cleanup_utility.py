"""Unit and regression tests for scripts/cleanup_test_data.py."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import pytest

from scripts.cleanup_test_data import (
    CANONICAL_DEMO_IDS,
    classify_assessment,
    scan_database,
    scan_uploads,
    execute_cleanup,
    verify_sqlite_integrity,
)


def test_classify_assessment_preserves_canonical_demos():
    """Confirms canonical demo assessments are strictly whitelisted and never classified as test pollution."""
    for demo_id in CANONICAL_DEMO_IDS:
        is_test, reason = classify_assessment(
            asm_id=demo_id,
            title="Any Title",
            class_id="cls_sec1_math",
            org_id="org_cedar_sec",
        )
        assert is_test is False
        assert reason == "canonical_demo"


def test_classify_assessment_preserves_legitimate_teacher_records():
    """Confirms genuine teacher-created assessments are strictly preserved."""
    is_test, reason = classify_assessment(
        asm_id="asm_custom_fractions_01",
        title="Fractions and Decimals Midterm",
        class_id="cls_sec2_math",
        org_id="org_cedar_sec",
    )
    assert is_test is False
    assert reason == "teacher_created_record"


def test_classify_assessment_identifies_test_signatures():
    """Confirms various test artifact signatures are reliably detected."""
    # Known test classes
    is_test, reason = classify_assessment("asm_123", "Custom Quiz", "cls_1", "org_cedar_sec")
    assert is_test is True
    assert "known_test_class" in reason

    # Known test titles
    is_test, reason = classify_assessment("asm_456", "Gate 5 Truthfulness Checkpoint", "cls_sec1_math", "org_cedar_sec")
    assert is_test is True
    assert "known_test_title" in reason

    # Duplicate checkpoint 1
    is_test, reason = classify_assessment("asm_random_uuid", "Integers on Number Line: Checkpoint 1", "cls_sec1_math", "org_cedar_sec")
    assert is_test is True
    assert reason == "duplicate_checkpoint_fixture"

    # Known test IDs
    is_test, reason = classify_assessment("asm_foreign_isolation", "Foreign Assessment", "cls_foreign", "org_raffles_sec")
    assert is_test is True
    assert "known_test_id" in reason


def test_cleanup_execution_with_backup_and_relational_integrity():
    """Tests end-to-end cleanup execution on an isolated SQLite database."""
    with tempfile.TemporaryDirectory(prefix="test_cleanup_exec_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "classlens.db"
        uploads_dir = tmp_path / "uploads"
        uploads_dir.mkdir(parents=True)

        # Setup test database schema
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE assessments (
                id TEXT PRIMARY KEY,
                class_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ready',
                is_demo INTEGER NOT NULL DEFAULT 0,
                question_json TEXT NOT NULL DEFAULT '{}',
                total_responses INTEGER DEFAULT 0,
                reviewed_responses INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE responses (
                id TEXT PRIMARY KEY,
                assessment_id TEXT NOT NULL,
                pseudonymous_student_id TEXT NOT NULL,
                pseudonym_label TEXT NOT NULL,
                source_filename TEXT NOT NULL,
                task_status TEXT NOT NULL DEFAULT 'COMPLETED',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE audit_events (
                id TEXT PRIMARY KEY,
                assessment_id TEXT NOT NULL,
                response_id TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE analysis_jobs (
                id TEXT PRIMARY KEY,
                assessment_id TEXT NOT NULL,
                status TEXT NOT NULL
            );
        """)

        # Insert 1 canonical demo, 1 real teacher assessment, and 2 test assessments
        now_iso = "2026-10-16T12:00:00Z"
        conn.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     ("asm_1065658", "cls_sec1_math", "org_cedar_sec", "Integers on Number Line: Checkpoint 1", "ready", 1, "{}", 1, 0, now_iso, now_iso))
        conn.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     ("asm_real_teacher", "cls_sec1_math", "org_cedar_sec", "Real Algebra Checkpoint", "ready", 0, "{}", 1, 0, now_iso, now_iso))
        conn.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     ("asm_test_conc1", "cls_1", "org_cedar_sec", "Concurrent 1", "ready", 0, "{}", 1, 0, now_iso, now_iso))
        conn.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     ("asm_test_dup", "cls_sec1_math", "org_cedar_sec", "Integers on Number Line: Checkpoint 1", "ready", 0, "{}", 1, 0, now_iso, now_iso))

        # Insert child records
        for asm_id in ["asm_1065658", "asm_real_teacher", "asm_test_conc1", "asm_test_dup"]:
            conn.execute("INSERT INTO responses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (f"resp_{asm_id}", asm_id, "stu_01", "Student 01", "file.jpg", "COMPLETED", now_iso, now_iso))
            conn.execute("INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?)",
                         (f"evt_{asm_id}", asm_id, f"resp_{asm_id}", "usr_t", "approved", now_iso))
            conn.execute("INSERT INTO analysis_jobs VALUES (?, ?, ?)",
                         (f"job_{asm_id}", asm_id, "completed"))

        conn.commit()
        conn.close()

        # Create dummy upload directories
        for asm_id in ["asm_1065658", "asm_real_teacher", "asm_test_conc1", "asm_test_dup"]:
            u_dir = uploads_dir / "org_cedar_sec" / asm_id
            u_dir.mkdir(parents=True)
            (u_dir / "worksheet.jpg").write_text("dummy")

        # 1. Scan database
        scan_res = scan_database(db_path)
        assert scan_res["total_assessments"] == 4
        assert len(scan_res["preserved_records"]) == 2
        assert {r["id"] for r in scan_res["preserved_records"]} == {"asm_1065658", "asm_real_teacher"}
        assert len(scan_res["test_records"]) == 2
        assert {r["id"] for r in scan_res["test_records"]} == {"asm_test_conc1", "asm_test_dup"}

        # 2. Execute cleanup
        exec_res = execute_cleanup(db_path, uploads_dir, scan_res)
        assert exec_res["status"] == "success"
        assert exec_res["assessments_deleted"] == 2
        assert exec_res["responses_deleted"] == 2
        assert exec_res["audit_events_deleted"] == 2
        assert exec_res["analysis_jobs_deleted"] == 2

        # Verify backup exists and is valid
        backup_file = Path(exec_res["backup_db"])
        assert backup_file.is_file()
        assert verify_sqlite_integrity(backup_file) is True

        # Verify remaining records in database
        conn_after = sqlite3.connect(str(db_path))
        cur = conn_after.cursor()
        cur.execute("SELECT id FROM assessments ORDER BY id")
        remaining_asm = [r[0] for r in cur.fetchall()]
        assert remaining_asm == ["asm_1065658", "asm_real_teacher"]

        cur.execute("SELECT assessment_id FROM responses ORDER BY assessment_id")
        remaining_resp = [r[0] for r in cur.fetchall()]
        assert remaining_resp == ["asm_1065658", "asm_real_teacher"]

        cur.execute("SELECT assessment_id FROM audit_events ORDER BY assessment_id")
        remaining_audit = [r[0] for r in cur.fetchall()]
        assert remaining_audit == ["asm_1065658", "asm_real_teacher"]

        cur.execute("SELECT value FROM app_metadata WHERE key = 'demo_seeded'")
        assert cur.fetchone()[0] == "true"
        conn_after.close()

        # Verify uploads directories: test dirs removed, demo and teacher preserved
        assert (uploads_dir / "org_cedar_sec" / "asm_1065658").is_dir()
        assert (uploads_dir / "org_cedar_sec" / "asm_real_teacher").is_dir()
        assert not (uploads_dir / "org_cedar_sec" / "asm_test_conc1").exists()
        assert not (uploads_dir / "org_cedar_sec" / "asm_test_dup").exists()
