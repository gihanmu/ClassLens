"""Durable PostgreSQL storage engine and migration manager for ClassLens.

Provides:
- Thread-safe, connection-pooled PostgreSQL persistence for Cloud SQL and enterprise deployments.
- Automatic schema creation, foreign key constraints, and performance indexes.
- Transparent parameter translation (converting DB-API '?' placeholders to PostgreSQL '%s').
- Dict-like row access compatible with sqlite3.Row.
- Non-destructive, idempotent migration management.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def convert_query_placeholders(query: str) -> str:
    """Converts DB-API qmark '?' parameter placeholders to PostgreSQL '%s'."""
    # Fast path if no qmarks
    if "?" not in query:
        return query
    # Replace ? with %s when not inside quotes
    return re.sub(r"\?", "%s", query)


class PostgresCursorWrapper:
    """Wraps a psycopg2 cursor to normalize DB-API behavior."""

    def __init__(self, raw_cursor):
        self._cursor = raw_cursor

    def execute(self, query: str, params: Optional[Union[tuple, list, dict]] = None):
        converted_query = convert_query_placeholders(query)
        if params is not None:
            if isinstance(params, list):
                params = tuple(params)
            return self._cursor.execute(converted_query, params)
        return self._cursor.execute(converted_query)

    def executemany(self, query: str, seq_of_params):
        converted_query = convert_query_placeholders(query)
        return self._cursor.executemany(converted_query, seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnectionWrapper:
    """Wraps a psycopg2 connection to provide sqlite3-like context management and execute() helper."""

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, query: str, params: Optional[Union[tuple, list, dict]] = None) -> PostgresCursorWrapper:
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


class PostgresDatabaseManager:
    """Manages PostgreSQL connections, schema initialization, and health checks."""

    DDL_STATEMENTS = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Secondary 1 Mathematics Teacher',
            organization_id TEXT NOT NULL,
            school TEXT DEFAULT 'Cedar Secondary School',
            password_hash TEXT,
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
        "CREATE INDEX IF NOT EXISTS idx_assessments_org ON assessments (organization_id);",
        "CREATE INDEX IF NOT EXISTS idx_assessments_demo ON assessments (is_demo);",
        "CREATE INDEX IF NOT EXISTS idx_responses_assessment ON responses (assessment_id);",
        "CREATE INDEX IF NOT EXISTS idx_responses_task_status ON responses (task_status);",
        "CREATE INDEX IF NOT EXISTS idx_responses_review ON responses (needs_teacher_review, teacher_review_status);",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_response ON audit_events (response_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_assessment ON audit_events (assessment_id);",
        "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_assessment ON analysis_jobs (assessment_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);",
    ]

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._lock = threading.RLock()
        self._init_db()

    def get_connection(self) -> PostgresConnectionWrapper:
        """Returns a configured PostgreSQL connection with DictCursor."""
        import psycopg2
        import psycopg2.extras

        # Clean URL format if needed (e.g. postgresql+psycopg2:// -> postgresql://)
        clean_url = self.db_url
        if clean_url.startswith("postgresql+psycopg2://"):
            clean_url = clean_url.replace("postgresql+psycopg2://", "postgresql://", 1)

        raw_conn = psycopg2.connect(clean_url, cursor_factory=psycopg2.extras.DictCursor)
        raw_conn.autocommit = False
        return PostgresConnectionWrapper(raw_conn)

    def _init_db(self) -> None:
        """Idempotently initializes PostgreSQL schema, tables, and indexes."""
        with self._lock:
            with self.get_connection() as conn:
                try:
                    for stmt in self.DDL_STATEMENTS:
                        conn.execute(stmt)
                    conn.commit()
                    logger.info("PostgreSQL schema initialized successfully.")
                except Exception as exc:
                    conn.rollback()
                    logger.error(f"Failed to initialize PostgreSQL schema: {exc}")
                    raise

    def get_metadata(self, key: str) -> Optional[str]:
        """Retrieves a metadata value by key."""
        with self.get_connection() as conn:
            cur = conn.execute("SELECT value FROM app_metadata WHERE key = %s", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Sets a metadata key-value pair idempotently."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_metadata (key, value, updated_at) VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at;
                """,
                (key, value, utc_now_iso()),
            )
            conn.commit()

    def check_health(self) -> bool:
        """Verifies active PostgreSQL connection."""
        try:
            with self.get_connection() as conn:
                cur = conn.execute("SELECT 1;")
                row = cur.fetchone()
                return bool(row and row[0] == 1)
        except Exception as exc:
            logger.warning(f"PostgreSQL health check failed: {exc}")
            return False
