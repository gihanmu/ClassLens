"""Durable SQLite storage engine and migration manager for ClassLens.

Provides:
- Thread-safe, transactional SQLite persistence for assessments, responses,
  audit events, analysis jobs, and users.
- Automatic WAL (Write-Ahead Logging) mode, foreign key enforcement, and indexes.
- Non-destructive, idempotent migration from existing local-data/store/{org_id}_state.json.
- Dual-persistence support to maintain full backward compatibility with tests
  expecting JSON state file artifacts while providing relational SQLite durability.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.api.repository.storage_config import DEFAULT_DATA_DIR, get_data_dir

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteDatabaseManager:
    """Manages SQLite database connections, DDL schema creation, and migrations."""

    DDL_STATEMENTS = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'teacher',
            organization_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            name TEXT NOT NULL,
            grade_level TEXT,
            subject TEXT,
            created_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            class_id TEXT,
            pseudonym_label TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            class_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            title TEXT NOT NULL,
            math_topic TEXT,
            grade_level TEXT,
            status TEXT NOT NULL DEFAULT 'ready',
            is_demo INTEGER NOT NULL DEFAULT 0,
            question_json TEXT NOT NULL,
            total_responses INTEGER DEFAULT 0,
            reviewed_responses INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            assessment_id TEXT NOT NULL,
            pseudonymous_student_id TEXT NOT NULL,
            pseudonym_label TEXT NOT NULL,
            source_filename TEXT NOT NULL,
            image_mime_type TEXT NOT NULL DEFAULT 'image/jpeg',
            sha256_hash TEXT,
            upload_status TEXT NOT NULL DEFAULT 'validated',
            task_status TEXT NOT NULL DEFAULT 'PENDING',
            answer_status TEXT NOT NULL DEFAULT 'not_assessed',
            reasoning_status TEXT NOT NULL DEFAULT 'not_assessed',
            teacher_review_status TEXT NOT NULL DEFAULT 'unreviewed',
            is_compensatory_error INTEGER NOT NULL DEFAULT 0,
            needs_teacher_review INTEGER NOT NULL DEFAULT 0,
            misconception_taxonomy_id TEXT,
            teacher_override_taxonomy_id TEXT,
            teacher_notes TEXT,
            analysis_data_json TEXT,
            is_mock INTEGER NOT NULL DEFAULT 1,
            model_version TEXT NOT NULL DEFAULT 'mock-offline-fixture',
            cost_estimate_usd REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            assessment_id TEXT NOT NULL,
            response_id TEXT NOT NULL,
            teacher_id TEXT NOT NULL,
            action TEXT NOT NULL,
            old_state_json TEXT NOT NULL,
            new_state_json TEXT NOT NULL,
            notes TEXT,
            timestamp TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            id TEXT PRIMARY KEY,
            assessment_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'processing',
            total_items INTEGER NOT NULL DEFAULT 0,
            completed_items INTEGER NOT NULL DEFAULT 0,
            failed_items INTEGER NOT NULL DEFAULT 0,
            idempotency_key TEXT UNIQUE,
            created_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
        # Indexes for fast querying & aggregations
        "CREATE INDEX IF NOT EXISTS idx_assessments_org ON assessments (organization_id);",
        "CREATE INDEX IF NOT EXISTS idx_responses_assessment ON responses (assessment_id);",
        "CREATE INDEX IF NOT EXISTS idx_responses_task_status ON responses (task_status);",
        "CREATE INDEX IF NOT EXISTS idx_responses_review ON responses (needs_teacher_review, teacher_review_status);",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_response ON audit_events (response_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_assessment ON audit_events (assessment_id);",
        "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_assessment ON analysis_jobs (assessment_id);",
    ]

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode by default; manual transactions with BEGIN/COMMIT
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes safely."""
        with self._lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    for stmt in self.DDL_STATEMENTS:
                        conn.execute(stmt)

                    # Ensure is_demo exists on assessments for pre-existing databases
                    cur = conn.execute("PRAGMA table_info(assessments);")
                    cols = [r["name"] for r in cur.fetchall()]
                    if "is_demo" not in cols:
                        conn.execute("ALTER TABLE assessments ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0;")

                    # Index for demo filtering (guaranteed column exists)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_demo ON assessments (is_demo);")

                    conn.execute("COMMIT;")
                except Exception as exc:
                    conn.execute("ROLLBACK;")
                    logger.error(f"Failed to initialize SQLite schema: {exc}")
                    raise

    def get_metadata(self, key: str) -> Optional[str]:
        """Retrieves a metadata value by key."""
        with self.get_connection() as conn:
            cur = conn.execute("SELECT value FROM app_metadata WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Sets a metadata key-value pair idempotently."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_metadata (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
                """,
                (key, value, utc_now_iso()),
            )

    def migrate_from_json_if_needed(self, data_dir: Path, org_id: str = "org_cedar_sec") -> bool:
        """Non-destructively migrates records from existing JSON state file into SQLite if tables are empty."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM assessments WHERE organization_id = ?", (org_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    # SQLite already populated
                    return False

            # Check for existing state JSON file
            safe_org = "".join(c for c in org_id if c.isalnum() or c in ("-", "_"))
            json_file = data_dir / f"{safe_org}_state.json"
            if not json_file.is_file():
                return False

            try:
                # Create safety backup
                backup_file = data_dir / f"{safe_org}_state.json.bak"
                if not backup_file.exists():
                    shutil.copy2(json_file, backup_file)

                with open(json_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)

                assessments = state_data.get("assessments", [])
                responses = state_data.get("responses", [])
                audit_events = state_data.get("audit_events", [])

                with self.get_connection() as conn:
                    conn.execute("BEGIN IMMEDIATE;")
                    try:
                        for a in assessments:
                            q_json = json.dumps(a.get("question", {}), default=str)
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO assessments (
                                    id, class_id, organization_id, title, math_topic,
                                    grade_level, status, question_json, total_responses,
                                    reviewed_responses, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    a.get("id"),
                                    a.get("class_id", "cls_sec1_math"),
                                    a.get("organization_id", org_id),
                                    a.get("title", "Untitled Assessment"),
                                    a.get("math_topic", "Mathematics"),
                                    a.get("grade_level", "Secondary 1"),
                                    a.get("status", "ready"),
                                    q_json,
                                    a.get("total_responses", 0),
                                    a.get("reviewed_responses", 0),
                                    str(a.get("created_at", utc_now_iso())),
                                    str(a.get("updated_at", utc_now_iso())),
                                ),
                            )

                        for r in responses:
                            analysis_json = json.dumps(r.get("analysis_data"), default=str) if r.get("analysis_data") else None
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO responses (
                                    id, assessment_id, pseudonymous_student_id, pseudonym_label,
                                    source_filename, image_mime_type, sha256_hash, upload_status,
                                    task_status, answer_status, reasoning_status, teacher_review_status,
                                    is_compensatory_error, needs_teacher_review, misconception_taxonomy_id,
                                    teacher_override_taxonomy_id, teacher_notes, analysis_data_json,
                                    is_mock, model_version, cost_estimate_usd, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    r.get("id"),
                                    r.get("assessment_id"),
                                    r.get("pseudonymous_student_id", "stu_anon"),
                                    r.get("pseudonym_label", "Student"),
                                    r.get("source_filename", "worksheet.jpg"),
                                    r.get("image_mime_type", "image/jpeg"),
                                    r.get("sha256_hash"),
                                    r.get("upload_status", "validated"),
                                    r.get("task_status", "PENDING"),
                                    r.get("answer_status", "not_assessed"),
                                    r.get("reasoning_status", "not_assessed"),
                                    r.get("teacher_review_status", "unreviewed"),
                                    1 if r.get("is_compensatory_error") else 0,
                                    1 if r.get("needs_teacher_review") else 0,
                                    r.get("misconception_taxonomy_id"),
                                    r.get("teacher_override_taxonomy_id"),
                                    r.get("teacher_notes"),
                                    analysis_json,
                                    1 if r.get("is_mock", True) else 0,
                                    r.get("model_version", "mock-offline-fixture"),
                                    r.get("cost_estimate_usd"),
                                    str(r.get("created_at", utc_now_iso())),
                                    str(r.get("updated_at", utc_now_iso())),
                                ),
                            )

                        for ev in audit_events:
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO audit_events (
                                    id, assessment_id, response_id, teacher_id, action,
                                    old_state_json, new_state_json, notes, timestamp
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    ev.get("id"),
                                    ev.get("assessment_id"),
                                    ev.get("response_id"),
                                    ev.get("teacher_id", "usr_sarah_lim"),
                                    ev.get("action", "reviewed"),
                                    json.dumps(ev.get("old_state", {}), default=str),
                                    json.dumps(ev.get("new_state", {}), default=str),
                                    ev.get("notes"),
                                    str(ev.get("timestamp", utc_now_iso())),
                                ),
                            )

                        conn.execute("COMMIT;")
                        logger.info(
                            f"Successfully migrated {len(assessments)} assessments, "
                            f"{len(responses)} responses, and {len(audit_events)} audit events to SQLite."
                        )
                        return True
                    except Exception as exc:
                        conn.execute("ROLLBACK;")
                        logger.error(f"Migration from JSON to SQLite failed: {exc}")
                        return False
            except Exception as e:
                logger.error(f"Error reading JSON state file for migration: {e}")
                return False
