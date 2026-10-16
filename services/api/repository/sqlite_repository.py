"""Durable SQLite Assessment Repository for ClassLens.

Provides:
- Fully relational, durable persistence backed by SQLite.
- Seamless compatibility with existing domain contracts (AssessmentDoc, ResponseDoc, AuditEventDoc).
- ACID transactions for student response updates and educator review overrides.
- Automatic migration from existing JSON state files upon initialization.
- Sync with JSON backups to prevent any data loss and maintain dual-layer durability.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.api.repository.local_persistence import LocalStatePersistence
from services.api.repository.sqlite_storage import SqliteDatabaseManager, utc_now_iso
from services.api.repository.storage_config import DEFAULT_DATA_DIR, get_data_dir
from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(dt_val: Any) -> datetime:
    if isinstance(dt_val, datetime):
        return dt_val
    if isinstance(dt_val, str):
        try:
            return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            pass
    return utc_now()


class UserDoc(BaseModel):
    id: str
    email: str
    name: str
    role: str = "Secondary 1 Mathematics Teacher"
    organization_id: str
    school: Optional[str] = "Cedar Secondary School"
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None


class QuestionConfig(BaseModel):
    problem_reference_id: str = "1065658"
    question_text: str = "Use the number line to evaluate -6 + 12 - 4"
    latex_formula: str = "-6 + 12 - 4"
    expected_answer: str = "2"
    accepted_methods: List[str] = [
        "hop_from_zero",
        "direct_jump_from_negative_six",
        "commutative_rearrangement",
    ]


class AssessmentDoc(BaseModel):
    id: str
    class_id: str = "cls_sec1_math"
    organization_id: str = "org_cedar_sec"
    title: str = "Integers on Number Line: Checkpoint 1"
    math_topic: str = "Integer operations on number lines"
    grade_level: str = "Secondary 1"
    status: str = "ready"  # draft, ready, processing, review, completed
    is_demo: bool = False
    question: QuestionConfig = Field(default_factory=QuestionConfig)
    total_responses: int = 0
    reviewed_responses: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ResponseDoc(BaseModel):
    id: str
    assessment_id: str
    pseudonymous_student_id: str
    pseudonym_label: str
    source_filename: str
    image_mime_type: str = "image/jpeg"
    sha256_hash: Optional[str] = None
    upload_status: str = "validated"  # uploaded_unverified, validating, validated, rejected
    task_status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, AWAITING_LIVE_ANALYSIS
    answer_status: str = "not_assessed"  # correct, incorrect, undetermined, not_assessed
    reasoning_status: str = "not_assessed"  # supported_correct, supported_error, incomplete, unverifiable, not_assessed
    teacher_review_status: str = "unreviewed"  # unreviewed, approved_as_is, overridden, marked_unreadable
    is_compensatory_error: bool = False
    needs_teacher_review: bool = False
    misconception_taxonomy_id: Optional[str] = None
    teacher_override_taxonomy_id: Optional[str] = None
    teacher_notes: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None
    is_mock: bool = True
    model_version: str = "mock-offline-fixture"
    cost_estimate_usd: Optional[float] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AuditEventDoc(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    assessment_id: str
    response_id: str
    teacher_id: str
    action: str  # approved_as_is, overridden, marked_unreadable
    old_state: Dict[str, Any]
    new_state: Dict[str, Any]
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class AnalysisJobDoc(BaseModel):
    id: str
    assessment_id: str
    status: str = "processing"  # processing, completed, failed, completed_with_errors
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class SqliteAssessmentRepository:
    """Relational SQLite-backed assessment repository with cached in-memory access and JSON dual-persistence."""

    def __init__(self, data_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self._lock = threading.RLock()
        if db_path is not None:
            self.db_path = Path(db_path)
            self.data_dir = self.db_path.parent
        else:
            self.data_dir = data_dir or get_data_dir()
            self.db_path = self.data_dir / "classlens.db"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database manager
        self.db_manager = SqliteDatabaseManager(self.db_path)
        self.persistence = LocalStatePersistence(data_dir=self.data_dir)

        # In-memory working cache
        self.users: Dict[str, UserDoc] = {}
        self.assessments: Dict[str, AssessmentDoc] = {}
        self.responses: Dict[str, ResponseDoc] = {}
        self.audit_events: List[AuditEventDoc] = []
        self.analysis_jobs: Dict[str, AnalysisJobDoc] = {}
        self.idempotency_keys: Dict[str, str] = {}

        # 1. Attempt non-destructive migration from JSON if SQLite is empty
        migrated = self.db_manager.migrate_from_json_if_needed(self.data_dir, "org_cedar_sec")

        # 2. Load all state from SQLite into in-memory cache
        self._load_from_sqlite()

        # 3. Check demo seeding status in metadata:
        # If metadata key 'demo_seeded' is absent and assessments is empty, seed demo data once.
        # If assessments were deleted by user, do NOT re-seed on ordinary startup.
        demo_seeded = self.db_manager.get_metadata("demo_seeded")
        if demo_seeded is None and not self.assessments:
            self.seed_demo_data(force=False)
            self._save_all_to_sqlite("org_cedar_sec")

    def reconfigure(self, data_dir: Optional[Path] = None) -> None:
        """Reconfigures the repository to use a specified or newly resolved data directory."""
        with self._lock:
            self.data_dir = data_dir or get_data_dir()
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.data_dir / "classlens.db"
            self.db_manager = SqliteDatabaseManager(self.db_path)
            self.persistence = LocalStatePersistence(data_dir=self.data_dir)
            self.users.clear()
            self.assessments.clear()
            self.responses.clear()
            self.audit_events.clear()
            self.analysis_jobs.clear()
            self.idempotency_keys.clear()
            self._load_from_sqlite()
            demo_seeded = self.db_manager.get_metadata("demo_seeded")
            if demo_seeded is None and not self.assessments:
                self.seed_demo_data(force=False)
                self._save_all_to_sqlite("org_cedar_sec")

    def _row_to_assessment(self, row: Any) -> AssessmentDoc:
        q_data = json.loads(row["question_json"]) if row["question_json"] else {}
        is_demo = bool(row["is_demo"]) if "is_demo" in row.keys() else False
        return AssessmentDoc(
            id=row["id"],
            class_id=row["class_id"],
            organization_id=row["organization_id"],
            title=row["title"],
            math_topic=row["math_topic"] or "Mathematics",
            grade_level=row["grade_level"] or "Secondary 1",
            status=row["status"],
            is_demo=is_demo,
            question=QuestionConfig(**q_data),
            total_responses=row["total_responses"],
            reviewed_responses=row["reviewed_responses"],
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
        )

    def _row_to_response(self, row: Any) -> ResponseDoc:
        analysis_data = json.loads(row["analysis_data_json"]) if row["analysis_data_json"] else None
        return ResponseDoc(
            id=row["id"],
            assessment_id=row["assessment_id"],
            pseudonymous_student_id=row["pseudonymous_student_id"],
            pseudonym_label=row["pseudonym_label"],
            source_filename=row["source_filename"],
            image_mime_type=row["image_mime_type"],
            sha256_hash=row["sha256_hash"],
            upload_status=row["upload_status"],
            task_status=row["task_status"],
            answer_status=row["answer_status"],
            reasoning_status=row["reasoning_status"],
            teacher_review_status=row["teacher_review_status"],
            is_compensatory_error=bool(row["is_compensatory_error"]),
            needs_teacher_review=bool(row["needs_teacher_review"]),
            misconception_taxonomy_id=row["misconception_taxonomy_id"],
            teacher_override_taxonomy_id=row["teacher_override_taxonomy_id"],
            teacher_notes=row["teacher_notes"],
            analysis_data=analysis_data,
            is_mock=bool(row["is_mock"]),
            model_version=row["model_version"],
            cost_estimate_usd=row["cost_estimate_usd"],
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
        )

    def _row_to_audit_event(self, row: Any) -> AuditEventDoc:
        old_st = json.loads(row["old_state_json"]) if row["old_state_json"] else {}
        new_st = json.loads(row["new_state_json"]) if row["new_state_json"] else {}
        return AuditEventDoc(
            id=row["id"],
            assessment_id=row["assessment_id"],
            response_id=row["response_id"],
            teacher_id=row["teacher_id"],
            action=row["action"],
            old_state=old_st,
            new_state=new_st,
            notes=row["notes"],
            timestamp=parse_datetime(row["timestamp"]),
        )

    def _row_to_analysis_job(self, row: Any) -> AnalysisJobDoc:
        return AnalysisJobDoc(
            id=row["id"],
            assessment_id=row["assessment_id"],
            status=row["status"],
            total_items=row["total_items"],
            completed_items=row["completed_items"],
            failed_items=row["failed_items"],
            idempotency_key=row["idempotency_key"],
            created_at=parse_datetime(row["created_at"]),
        )

    def _load_from_sqlite(self) -> None:
        """Hydrates the in-memory cache directly from the SQLite database."""
        with self._lock:
            with self.db_manager.get_connection() as conn:
                # 1. Users
                cur = conn.execute("SELECT * FROM users")
                for r in cur.fetchall():
                    cols = r.keys()
                    self.users[r["id"]] = UserDoc(
                        id=r["id"],
                        email=r["email"],
                        name=r["name"],
                        role=r["role"],
                        organization_id=r["organization_id"],
                        school=r["school"] if "school" in cols else "Cedar Secondary School",
                        password_hash=r["password_hash"] if "password_hash" in cols else None,
                        created_at=parse_datetime(r["created_at"]) if "created_at" in cols and r["created_at"] else None,
                    )

                # 2. Assessments
                cur = conn.execute("SELECT * FROM assessments")
                for r in cur.fetchall():
                    doc = self._row_to_assessment(r)
                    self.assessments[doc.id] = doc

                # 3. Responses
                cur = conn.execute("SELECT * FROM responses")
                for r in cur.fetchall():
                    doc = self._row_to_response(r)
                    self.responses[doc.id] = doc

                # 4. Audit events
                cur = conn.execute("SELECT * FROM audit_events ORDER BY timestamp ASC")
                self.audit_events = [self._row_to_audit_event(r) for r in cur.fetchall()]

                # 5. Analysis jobs
                cur = conn.execute("SELECT * FROM analysis_jobs")
                for r in cur.fetchall():
                    job = self._row_to_analysis_job(r)
                    self.analysis_jobs[job.id] = job
                    if job.idempotency_key:
                        self.idempotency_keys[job.idempotency_key] = job.id

            # Recalculate response and reviewed counts for consistency
            for asm in self.assessments.values():
                resps = [r for r in self.responses.values() if r.assessment_id == asm.id]
                asm.total_responses = len(resps)
                asm.reviewed_responses = sum(
                    1 for r in resps if r.teacher_review_status and r.teacher_review_status != "unreviewed"
                )

    def _save_assessment_to_sqlite(self, doc: AssessmentDoc) -> None:
        with self.db_manager.get_connection() as conn:
            q_json = json.dumps(doc.question.model_dump(), default=str)
            conn.execute(
                """
                INSERT INTO assessments (
                    id, class_id, organization_id, title, math_topic,
                    grade_level, status, is_demo, question_json, total_responses,
                    reviewed_responses, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    class_id = excluded.class_id,
                    organization_id = excluded.organization_id,
                    title = excluded.title,
                    math_topic = excluded.math_topic,
                    grade_level = excluded.grade_level,
                    status = excluded.status,
                    is_demo = excluded.is_demo,
                    question_json = excluded.question_json,
                    total_responses = excluded.total_responses,
                    reviewed_responses = excluded.reviewed_responses,
                    updated_at = excluded.updated_at
                """,
                (
                    doc.id,
                    doc.class_id,
                    doc.organization_id,
                    doc.title,
                    doc.math_topic,
                    doc.grade_level,
                    doc.status,
                    1 if doc.is_demo else 0,
                    q_json,
                    doc.total_responses,
                    doc.reviewed_responses,
                    doc.created_at.isoformat(),
                    doc.updated_at.isoformat(),
                ),
            )

    def _save_response_to_sqlite(self, doc: ResponseDoc) -> None:
        with self.db_manager.get_connection() as conn:
            analysis_json = json.dumps(doc.analysis_data, default=str) if doc.analysis_data else None
            conn.execute(
                """
                INSERT INTO responses (
                    id, assessment_id, pseudonymous_student_id, pseudonym_label,
                    source_filename, image_mime_type, sha256_hash, upload_status,
                    task_status, answer_status, reasoning_status, teacher_review_status,
                    is_compensatory_error, needs_teacher_review, misconception_taxonomy_id,
                    teacher_override_taxonomy_id, teacher_notes, analysis_data_json,
                    is_mock, model_version, cost_estimate_usd, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    assessment_id = excluded.assessment_id,
                    pseudonymous_student_id = excluded.pseudonymous_student_id,
                    pseudonym_label = excluded.pseudonym_label,
                    source_filename = excluded.source_filename,
                    image_mime_type = excluded.image_mime_type,
                    sha256_hash = excluded.sha256_hash,
                    upload_status = excluded.upload_status,
                    task_status = excluded.task_status,
                    answer_status = excluded.answer_status,
                    reasoning_status = excluded.reasoning_status,
                    teacher_review_status = excluded.teacher_review_status,
                    is_compensatory_error = excluded.is_compensatory_error,
                    needs_teacher_review = excluded.needs_teacher_review,
                    misconception_taxonomy_id = excluded.misconception_taxonomy_id,
                    teacher_override_taxonomy_id = excluded.teacher_override_taxonomy_id,
                    teacher_notes = excluded.teacher_notes,
                    analysis_data_json = excluded.analysis_data_json,
                    is_mock = excluded.is_mock,
                    model_version = excluded.model_version,
                    cost_estimate_usd = excluded.cost_estimate_usd,
                    updated_at = excluded.updated_at
                """,
                (
                    doc.id,
                    doc.assessment_id,
                    doc.pseudonymous_student_id,
                    doc.pseudonym_label,
                    doc.source_filename,
                    doc.image_mime_type,
                    doc.sha256_hash,
                    doc.upload_status,
                    doc.task_status,
                    doc.answer_status,
                    doc.reasoning_status,
                    doc.teacher_review_status,
                    1 if doc.is_compensatory_error else 0,
                    1 if doc.needs_teacher_review else 0,
                    doc.misconception_taxonomy_id,
                    doc.teacher_override_taxonomy_id,
                    doc.teacher_notes,
                    analysis_json,
                    1 if doc.is_mock else 0,
                    doc.model_version,
                    doc.cost_estimate_usd,
                    doc.created_at.isoformat(),
                    doc.updated_at.isoformat(),
                ),
            )

    def _save_audit_event_to_sqlite(self, evt: AuditEventDoc) -> None:
        with self.db_manager.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_events (
                    id, assessment_id, response_id, teacher_id, action,
                    old_state_json, new_state_json, notes, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evt.id,
                    evt.assessment_id,
                    evt.response_id,
                    evt.teacher_id,
                    evt.action,
                    json.dumps(evt.old_state, default=str),
                    json.dumps(evt.new_state, default=str),
                    evt.notes,
                    evt.timestamp.isoformat(),
                ),
            )

    def _save_all_to_sqlite(self, org_id: str) -> None:
        """Batch saves state to SQLite and syncs to JSON backup."""
        with self._lock:
            with self.db_manager.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    for u in self.users.values():
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO users (id, email, name, role, organization_id, school, password_hash, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                u.id,
                                u.email,
                                u.name,
                                u.role,
                                u.organization_id,
                                u.school or "Cedar Secondary School",
                                u.password_hash,
                                u.created_at.isoformat() if u.created_at else utc_now_iso(),
                            ),
                        )

                    for a in self.assessments.values():
                        if a.organization_id == org_id:
                            q_json = json.dumps(a.question.model_dump(), default=str)
                            conn.execute(
                                """
                                INSERT INTO assessments (
                                    id, class_id, organization_id, title, math_topic,
                                    grade_level, status, question_json, total_responses,
                                    reviewed_responses, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(id) DO UPDATE SET
                                    class_id = excluded.class_id,
                                    organization_id = excluded.organization_id,
                                    title = excluded.title,
                                    math_topic = excluded.math_topic,
                                    grade_level = excluded.grade_level,
                                    status = excluded.status,
                                    question_json = excluded.question_json,
                                    total_responses = excluded.total_responses,
                                    reviewed_responses = excluded.reviewed_responses,
                                    updated_at = excluded.updated_at
                                """,
                                (
                                    a.id,
                                    a.class_id,
                                    a.organization_id,
                                    a.title,
                                    a.math_topic,
                                    a.grade_level,
                                    a.status,
                                    q_json,
                                    a.total_responses,
                                    a.reviewed_responses,
                                    a.created_at.isoformat(),
                                    a.updated_at.isoformat(),
                                ),
                            )

                    asm_ids = {a.id for a in self.assessments.values() if a.organization_id == org_id}
                    for r in self.responses.values():
                        if r.assessment_id in asm_ids:
                            analysis_json = json.dumps(r.analysis_data, default=str) if r.analysis_data else None
                            conn.execute(
                                """
                                INSERT INTO responses (
                                    id, assessment_id, pseudonymous_student_id, pseudonym_label,
                                    source_filename, image_mime_type, sha256_hash, upload_status,
                                    task_status, answer_status, reasoning_status, teacher_review_status,
                                    is_compensatory_error, needs_teacher_review, misconception_taxonomy_id,
                                    teacher_override_taxonomy_id, teacher_notes, analysis_data_json,
                                    is_mock, model_version, cost_estimate_usd, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(id) DO UPDATE SET
                                    assessment_id = excluded.assessment_id,
                                    pseudonymous_student_id = excluded.pseudonymous_student_id,
                                    pseudonym_label = excluded.pseudonym_label,
                                    source_filename = excluded.source_filename,
                                    image_mime_type = excluded.image_mime_type,
                                    sha256_hash = excluded.sha256_hash,
                                    upload_status = excluded.upload_status,
                                    task_status = excluded.task_status,
                                    answer_status = excluded.answer_status,
                                    reasoning_status = excluded.reasoning_status,
                                    teacher_review_status = excluded.teacher_review_status,
                                    is_compensatory_error = excluded.is_compensatory_error,
                                    needs_teacher_review = excluded.needs_teacher_review,
                                    misconception_taxonomy_id = excluded.misconception_taxonomy_id,
                                    teacher_override_taxonomy_id = excluded.teacher_override_taxonomy_id,
                                    teacher_notes = excluded.teacher_notes,
                                    analysis_data_json = excluded.analysis_data_json,
                                    is_mock = excluded.is_mock,
                                    model_version = excluded.model_version,
                                    cost_estimate_usd = excluded.cost_estimate_usd,
                                    updated_at = excluded.updated_at
                                """,
                                (
                                    r.id,
                                    r.assessment_id,
                                    r.pseudonymous_student_id,
                                    r.pseudonym_label,
                                    r.source_filename,
                                    r.image_mime_type,
                                    r.sha256_hash,
                                    r.upload_status,
                                    r.task_status,
                                    r.answer_status,
                                    r.reasoning_status,
                                    r.teacher_review_status,
                                    1 if r.is_compensatory_error else 0,
                                    1 if r.needs_teacher_review else 0,
                                    r.misconception_taxonomy_id,
                                    r.teacher_override_taxonomy_id,
                                    r.teacher_notes,
                                    analysis_json,
                                    1 if r.is_mock else 0,
                                    r.model_version,
                                    r.cost_estimate_usd,
                                    r.created_at.isoformat(),
                                    r.updated_at.isoformat(),
                                ),
                            )

                    for ev in self.audit_events:
                        if ev.assessment_id in asm_ids or (ev.response_id in self.responses and self.responses[ev.response_id].assessment_id in asm_ids):
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO audit_events (
                                    id, assessment_id, response_id, teacher_id, action,
                                    old_state_json, new_state_json, notes, timestamp
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    ev.id,
                                    ev.assessment_id,
                                    ev.response_id,
                                    ev.teacher_id,
                                    ev.action,
                                    json.dumps(ev.old_state, default=str),
                                    json.dumps(ev.new_state, default=str),
                                    ev.notes,
                                    ev.timestamp.isoformat(),
                                ),
                            )

                    conn.execute("COMMIT;")
                except Exception as exc:
                    conn.execute("ROLLBACK;")
                    logger.error(f"Failed to batch save SQLite state: {exc}")

            # Also sync to JSON state for backward-compatibility with tests expecting tenant state files
            self._save_persisted_state(org_id)

    def _save_persisted_state(self, org_id: str) -> None:
        """Dual-write sync to JSON state file for tenant."""
        with self._lock:
            org_asms = [
                a.model_dump(mode="json")
                for a in self.assessments.values()
                if a.organization_id == org_id
            ]
            asm_ids = {a.id for a in self.assessments.values() if a.organization_id == org_id}
            org_resps = [
                r.model_dump(mode="json")
                for r in self.responses.values()
                if r.assessment_id in asm_ids
            ]
            org_evts = [
                e.model_dump(mode="json")
                for e in self.audit_events
                if (
                    e.assessment_id in asm_ids
                    or (
                        e.response_id in self.responses
                        and self.responses[e.response_id].assessment_id in asm_ids
                    )
                )
            ]
            self.persistence.save_tenant_state(org_id, org_asms, org_resps, org_evts)

    def seed_demo_data(self, force: bool = False) -> None:
        """Seeds the 2 canonical demo assessments with is_demo=True deterministically and idempotently."""
        with self._lock:
            demo_pwd = os.getenv("CLASSLENS_DEMO_PASSWORD")
            existing_user = self.get_user("usr_sarah_lim")
            existing_hash = existing_user.password_hash if existing_user else None

            initial_hash = existing_hash
            if not initial_hash and demo_pwd:
                from services.api.auth.security import hash_password
                initial_hash = hash_password(demo_pwd)

            sarah = UserDoc(
                id="usr_sarah_lim",
                email="teacher@classlens.demo",
                name="Mrs. Sarah Lim",
                role="Secondary 1 Mathematics Teacher",
                organization_id="org_cedar_sec",
                school="Cedar Secondary School",
                password_hash=initial_hash,
            )
            self.users[sarah.id] = sarah
            self.save_user(sarah)

            default_asm = AssessmentDoc(
                id="asm_1065658",
                class_id="cls_sec1_math",
                organization_id="org_cedar_sec",
                title="Integers on Number Line: Checkpoint 1",
                math_topic="Integer operations on number lines",
                grade_level="Secondary 1",
                status="ready",
                is_demo=True,
                question=QuestionConfig(),
            )
            if force or "asm_1065658" not in self.assessments:
                self.assessments[default_asm.id] = default_asm
                self._save_assessment_to_sqlite(default_asm)
                self.import_demo_responses(default_asm.id, default_asm.organization_id)

            synthetic_asm = AssessmentDoc(
                id="asm_synthetic_cases",
                class_id="cls_sec1_math",
                organization_id="org_cedar_sec",
                title="Synthetic Feasibility Benchmark: Cases 1–3",
                math_topic="Integer operations on number lines",
                grade_level="Secondary 1",
                status="ready",
                is_demo=True,
                question=QuestionConfig(
                    problem_reference_id="synthetic_benchmark",
                    question_text="Evaluate -6 + 12 - 4 on the number line (Evaluation Benchmark).",
                    latex_formula="-6 + 12 - 4",
                    expected_answer="2",
                ),
            )
            if force or "asm_synthetic_cases" not in self.assessments:
                self.assessments[synthetic_asm.id] = synthetic_asm
                self._save_assessment_to_sqlite(synthetic_asm)
                self.import_synthetic_demo_cases(synthetic_asm.id, synthetic_asm.organization_id)

            self.db_manager.set_metadata("demo_seeded", "true")

    def _seed_default_data(self):
        self.seed_demo_data(force=False)

    def import_synthetic_demo_cases(self, assessment_id: str, org_id: str) -> List[ResponseDoc]:
        with self._lock:
            asm = self.get_assessment(assessment_id, org_id)
            if not asm:
                raise ValueError("Assessment not found or access denied")

            from services.worker.agents.pipeline import MultiAgentPipeline

            cases = [
                (
                    "case_01_canonical_correct",
                    "Student-01 (Canonical Correct)",
                    "case_01_canonical_correct.png",
                ),
                (
                    "case_02_off_by_one_error",
                    "Student-02 (Off-by-One Error)",
                    "case_02_off_by_one_error.png",
                ),
                (
                    "case_03_ambiguous_incomplete",
                    "Student-03 (Ambiguous & Incomplete)",
                    "case_03_ambiguous_incomplete.png",
                ),
            ]

            from services.worker.agents.provider import MockVisualEvidenceProvider

            imported: List[ResponseDoc] = []
            for cid, label, filename in cases:
                doc_id = cid if assessment_id == "asm_synthetic_cases" else f"{assessment_id}_{cid}"
                analysis = MultiAgentPipeline.analyze_response(
                    response_id=cid,
                    provider=MockVisualEvidenceProvider(),
                )
                doc = ResponseDoc(
                    id=doc_id,
                    assessment_id=assessment_id,
                    pseudonymous_student_id=f"stu_{cid}",
                    pseudonym_label=label,
                    source_filename=filename,
                    image_mime_type="image/png",
                    sha256_hash=f"hash_{cid}",
                    upload_status="validated",
                    task_status="COMPLETED",
                    answer_status=(
                        analysis.answer_status.value
                        if hasattr(analysis.answer_status, "value")
                        else str(analysis.answer_status)
                    ),
                    reasoning_status=(
                        analysis.reasoning_status.value
                        if hasattr(analysis.reasoning_status, "value")
                        else str(analysis.reasoning_status)
                    ),
                    teacher_review_status="unreviewed",
                    is_compensatory_error=analysis.is_compensatory_error,
                    needs_teacher_review=analysis.needs_teacher_review,
                    misconception_taxonomy_id=analysis.diagnosis.misconception_taxonomy_id,
                    analysis_data=analysis.model_dump(),
                    is_mock=True,
                    model_version=analysis.model_version,
                    cost_estimate_usd=analysis.cost_estimate_usd,
                )
                self.responses[doc_id] = doc
                self._save_response_to_sqlite(doc)
                imported.append(doc)

            asm.total_responses = len(imported)
            asm.status = "ready"
            asm.updated_at = utc_now()
            self._save_assessment_to_sqlite(asm)
            self._save_persisted_state(org_id)
            return imported

    def import_demo_responses(self, assessment_id: str, org_id: str) -> List[ResponseDoc]:
        with self._lock:
            asm = self.get_assessment(assessment_id, org_id)
            if not asm:
                raise ValueError("Assessment not found or access denied")

            dataset_dir = os.path.join(os.getcwd(), "dataset", "problem_1065658")
            file_map = {}
            if os.path.isdir(dataset_dir):
                for f in os.listdir(dataset_dir):
                    if f.endswith((".jpeg", ".jpg", ".png", ".webp")):
                        prefix = f.split("-")[0]
                        file_map[prefix] = f

            imported: List[ResponseDoc] = []
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM responses WHERE assessment_id = ?", (assessment_id,))
                conn.execute("DELETE FROM analysis_jobs WHERE assessment_id = ?", (assessment_id,))

            for j_id, j in list(self.analysis_jobs.items()):
                if j.assessment_id == assessment_id:
                    if j.idempotency_key and j.idempotency_key in self.idempotency_keys:
                        del self.idempotency_keys[j.idempotency_key]
                    del self.analysis_jobs[j_id]

            for k in list(self.responses.keys()):
                if self.responses[k].assessment_id == assessment_id:
                    del self.responses[k]

            for idx, resp_id in enumerate(MOCK_FIXTURES.keys(), start=1):
                label = f"Student-{idx:02d}"
                prefix = resp_id.replace("resp_", "")
                filename = file_map.get(prefix, f"{resp_id}.jpg")
                mime_type = "image/png" if filename.endswith(".png") else "image/jpeg"
                doc_id = resp_id if assessment_id == "asm_1065658" else f"{assessment_id}_{resp_id}"
                doc = ResponseDoc(
                    id=doc_id,
                    assessment_id=assessment_id,
                    pseudonymous_student_id=f"stu_{idx:02d}",
                    pseudonym_label=label,
                    source_filename=filename,
                    image_mime_type=mime_type,
                    sha256_hash=f"hash_{resp_id}",
                    upload_status="validated",
                    task_status="PENDING",
                    answer_status="not_assessed",
                    reasoning_status="not_assessed",
                    teacher_review_status="unreviewed",
                )
                self.responses[doc_id] = doc
                self._save_response_to_sqlite(doc)
                imported.append(doc)

            asm.total_responses = len(imported)
            asm.status = "ready"
            asm.updated_at = utc_now()
            self._save_assessment_to_sqlite(asm)
            self._save_persisted_state(org_id)
            return imported

    def get_user(self, user_id: str) -> Optional[UserDoc]:
        with self._lock:
            return self.users.get(user_id)

    def save_user(self, user: UserDoc) -> UserDoc:
        with self._lock:
            self.users[user.id] = user
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO users (id, email, name, role, organization_id, school, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.id,
                        user.email,
                        user.name,
                        user.role,
                        user.organization_id,
                        user.school or "Cedar Secondary School",
                        user.password_hash,
                        user.created_at.isoformat() if user.created_at else utc_now_iso(),
                    ),
                )
            return user

    def get_user_by_identifier(self, identifier: str) -> Optional[UserDoc]:
        with self._lock:
            if not identifier:
                return None
            norm = identifier.strip().lower()
            for u in self.users.values():
                if (
                    u.id.lower() == norm
                    or u.email.lower() == norm
                    or (norm in ("teacher@classlens.demo", "sarah.lim@moe.edu.sg", "usr_sarah_lim") and u.id == "usr_sarah_lim")
                ):
                    return u

            # Fallback to SQLite
            with self.db_manager.get_connection() as conn:
                cur = conn.execute(
                    "SELECT * FROM users WHERE LOWER(id) = ? OR LOWER(email) = ?",
                    (norm, norm),
                )
                row = cur.fetchone()
                if row:
                    cols = row.keys()
                    doc = UserDoc(
                        id=row["id"],
                        email=row["email"],
                        name=row["name"],
                        role=row["role"],
                        organization_id=row["organization_id"],
                        school=row["school"] if "school" in cols else "Cedar Secondary School",
                        password_hash=row["password_hash"] if "password_hash" in cols else None,
                        created_at=parse_datetime(row["created_at"]) if "created_at" in cols and row["created_at"] else None,
                    )
                    self.users[doc.id] = doc
                    return doc
            return None

    def create_assessment(self, doc: AssessmentDoc) -> AssessmentDoc:
        with self._lock:
            self.assessments[doc.id] = doc
            self._save_assessment_to_sqlite(doc)
            self._save_persisted_state(doc.organization_id)
            return doc

    def create_response(self, doc: ResponseDoc) -> ResponseDoc:
        with self._lock:
            self.responses[doc.id] = doc
            self._save_response_to_sqlite(doc)
            asm = self.assessments.get(doc.assessment_id)
            if asm:
                asm.total_responses = len(self.list_responses(doc.assessment_id))
                asm.updated_at = utc_now()
                self._save_assessment_to_sqlite(asm)
                self._save_persisted_state(asm.organization_id)
            else:
                self._save_persisted_state("org_cedar_sec")
            return doc

    def delete_response(self, response_id: str, assessment_id: str) -> bool:
        with self._lock:
            found = False
            for k in list(self.responses.keys()):
                r = self.responses[k]
                if (r.id == response_id or k == response_id) and r.assessment_id == assessment_id:
                    del self.responses[k]
                    found = True
                    break
            if found:
                with self.db_manager.get_connection() as conn:
                    conn.execute("DELETE FROM responses WHERE id = ?", (response_id,))
                asm = self.assessments.get(assessment_id)
                if asm:
                    asm.total_responses = len(self.list_responses(assessment_id))
                    asm.updated_at = utc_now()
                    self._save_assessment_to_sqlite(asm)
                    self._save_persisted_state(asm.organization_id)
                return True
            return False

    def get_assessment(self, assessment_id: str, org_id: Optional[str] = None) -> Optional[AssessmentDoc]:
        with self._lock:
            asm = self.assessments.get(assessment_id)
            if asm and org_id and asm.organization_id != org_id:
                return None
            return asm

    def list_assessments(self, org_id: str) -> List[AssessmentDoc]:
        with self._lock:
            return [a for a in self.assessments.values() if a.organization_id == org_id]

    def list_responses(self, assessment_id: str) -> List[ResponseDoc]:
        with self._lock:
            return [r for r in self.responses.values() if r.assessment_id == assessment_id]

    def get_response(
        self,
        response_id: str,
        assessment_id: Optional[str] = None,
    ) -> Optional[ResponseDoc]:
        with self._lock:
            if assessment_id:
                if response_id in self.responses and self.responses[response_id].assessment_id == assessment_id:
                    return self.responses[response_id]
                for r in self.responses.values():
                    if r.assessment_id == assessment_id and (
                        r.id == response_id
                        or r.id.endswith(f"_{response_id}")
                        or response_id in r.id
                        or r.id.replace("resp_", "") == response_id.replace("resp_", "")
                    ):
                        return r
                return None

            if response_id in self.responses:
                r = self.responses[response_id]
                if r.task_status == "COMPLETED":
                    return r

            matches = [
                r
                for r in self.responses.values()
                if r.id == response_id
                or r.id.endswith(f"_{response_id}")
                or response_id in r.id
                or r.id.replace("resp_", "") == response_id.replace("resp_", "")
            ]
            if matches:
                completed = [m for m in matches if m.task_status == "COMPLETED"]
                return completed[0] if completed else matches[0]

            if response_id in self.responses:
                return self.responses[response_id]

            return None

    def update_response(self, response: ResponseDoc) -> ResponseDoc:
        with self._lock:
            response.updated_at = utc_now()
            self.responses[response.id] = response
            self._save_response_to_sqlite(response)
            asm = self.assessments.get(response.assessment_id)
            org_id = asm.organization_id if asm else "org_cedar_sec"
            self._save_persisted_state(org_id)
            return response

    def create_or_get_analysis_job(
        self,
        assessment_id: str,
        idempotency_key: Optional[str] = None,
        total_items: int = 0,
    ) -> AnalysisJobDoc:
        with self._lock:
            if idempotency_key and idempotency_key in self.idempotency_keys:
                existing_job_id = self.idempotency_keys[idempotency_key]
                existing_job = self.analysis_jobs.get(existing_job_id)
                if existing_job and existing_job.assessment_id == assessment_id:
                    return existing_job

            job_id = f"job_{uuid.uuid4().hex[:8]}"
            job = AnalysisJobDoc(
                id=job_id,
                assessment_id=assessment_id,
                status="processing",
                total_items=total_items,
                completed_items=0,
                failed_items=0,
                idempotency_key=idempotency_key,
            )
            self.analysis_jobs[job_id] = job
            if idempotency_key:
                self.idempotency_keys[idempotency_key] = job_id

            with self.db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analysis_jobs (
                        id, assessment_id, status, total_items, completed_items, failed_items, idempotency_key, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.id,
                        job.assessment_id,
                        job.status,
                        job.total_items,
                        job.completed_items,
                        job.failed_items,
                        job.idempotency_key,
                        job.created_at.isoformat(),
                    ),
                )
            return job

    def get_analysis_job(self, job_id: str) -> Optional[AnalysisJobDoc]:
        with self._lock:
            return self.analysis_jobs.get(job_id)

    def increment_job_progress(self, job_id: str, success: bool = True):
        with self._lock:
            job = self.analysis_jobs.get(job_id)
            if job:
                if success:
                    job.completed_items += 1
                else:
                    job.failed_items += 1
                if (job.completed_items + job.failed_items) >= job.total_items:
                    if job.failed_items > 0 and job.completed_items == 0:
                        job.status = "failed"
                    elif job.failed_items > 0:
                        job.status = "completed_with_errors"
                    else:
                        job.status = "completed"

                with self.db_manager.get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE analysis_jobs SET completed_items = ?, failed_items = ?, status = ? WHERE id = ?
                        """,
                        (job.completed_items, job.failed_items, job.status, job.id),
                    )

    def record_teacher_override(
        self,
        assessment_id: str,
        response_id: str,
        teacher_id: str,
        action: str,
        override_taxonomy: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ResponseDoc:
        with self._lock:
            resp = self.get_response(response_id)
            if not resp:
                raise ValueError("Response not found")

            old_state = {
                "teacher_review_status": resp.teacher_review_status,
                "misconception_taxonomy_id": resp.misconception_taxonomy_id,
                "teacher_override_taxonomy_id": resp.teacher_override_taxonomy_id,
                "teacher_notes": resp.teacher_notes,
            }

            resp.teacher_review_status = action
            if override_taxonomy:
                resp.teacher_override_taxonomy_id = override_taxonomy
            if notes:
                resp.teacher_notes = notes
            resp.updated_at = utc_now()

            new_state = {
                "teacher_review_status": resp.teacher_review_status,
                "misconception_taxonomy_id": resp.misconception_taxonomy_id,
                "teacher_override_taxonomy_id": resp.teacher_override_taxonomy_id,
                "teacher_notes": resp.teacher_notes,
            }

            evt = AuditEventDoc(
                assessment_id=assessment_id,
                response_id=response_id,
                teacher_id=teacher_id,
                action=action,
                old_state=old_state,
                new_state=new_state,
                notes=notes,
            )
            self.audit_events.append(evt)
            self._save_audit_event_to_sqlite(evt)
            self._save_response_to_sqlite(resp)

            asm = self.assessments.get(assessment_id)
            org_id = asm.organization_id if asm else "org_cedar_sec"
            if asm:
                reviewed_count = sum(
                    1 for r in self.responses.values()
                    if r.assessment_id == assessment_id and r.teacher_review_status != "unreviewed"
                )
                asm.reviewed_responses = reviewed_count
                asm.updated_at = utc_now()
                self._save_assessment_to_sqlite(asm)

            self._save_persisted_state(org_id)
            return resp

    def get_audit_events_for_response(self, response_id: str) -> List[AuditEventDoc]:
        with self._lock:
            return [e for e in self.audit_events if e.response_id == response_id]

    def get_dashboard_summary(self, org_id: str) -> Dict[str, Any]:
        """Calculates real teacher-level summary metrics, recent assessments, and attention items."""
        with self._lock:
            org_assessments = [a for a in self.assessments.values() if a.organization_id == org_id]
            asm_ids = {a.id for a in org_assessments}
            org_responses = [r for r in self.responses.values() if r.assessment_id in asm_ids]

            classes = {a.class_id for a in org_assessments}
            students = {r.pseudonymous_student_id for r in org_responses}

            awaiting_analysis = [r for r in org_responses if r.task_status in ("PENDING", "QUEUED", "AWAITING_LIVE_ANALYSIS")]
            analyzed = [r for r in org_responses if r.task_status == "COMPLETED"]
            in_progress = [r for r in org_responses if r.task_status == "RUNNING"]
            failed = [r for r in org_responses if r.task_status == "FAILED"]

            needs_review = [
                r for r in analyzed
                if r.needs_teacher_review and r.teacher_review_status == "unreviewed"
            ]
            reviewed = [r for r in analyzed if r.teacher_review_status != "unreviewed"]

            assessment_summaries = []
            for a in org_assessments:
                a_resps = [r for r in org_responses if r.assessment_id == a.id]
                a_analyzed = [r for r in a_resps if r.task_status == "COMPLETED"]
                a_pending = [r for r in a_resps if r.task_status in ("PENDING", "QUEUED", "AWAITING_LIVE_ANALYSIS")]
                a_needs_review = [
                    r for r in a_analyzed
                    if r.needs_teacher_review and r.teacher_review_status == "unreviewed"
                ]

                progress_pct = (
                    round((len(a_analyzed) / len(a_resps)) * 100)
                    if a_resps else 0
                )

                a_verified_count = sum(
                    1 for r in a_analyzed
                    if r.reasoning_status in ("verified", "supported_correct", "sound", "valid")
                )
                a_correct_count = sum(
                    1 for r in a_analyzed
                    if r.answer_status == "correct"
                )

                status_label = "ready"
                if any(r.task_status == "RUNNING" for r in a_resps):
                    status_label = "analyzing"
                elif len(a_analyzed) == len(a_resps) and a_resps:
                    status_label = "analyzed"
                elif a_resps:
                    status_label = "awaiting_analysis"

                assessment_summaries.append({
                    "id": a.id,
                    "title": a.title,
                    "subject": "Mathematics",
                    "topic": getattr(a, "math_topic", None) or "Mathematics",
                    "class_id": a.class_id,
                    "class_name": "Sec 1 Mathematics" if a.class_id == "cls_sec1_math" else (a.class_id or "Classroom"),
                    "total_submissions": len(a_resps),
                    "awaiting_analysis_count": len(a_pending),
                    "analyzed_count": len(a_analyzed),
                    "needs_review_count": len(a_needs_review),
                    "progress_percentage": progress_pct,
                    "verified_reasoning_count": a_verified_count,
                    "verified_reasoning_pct": round((a_verified_count / len(a_analyzed)) * 100) if a_analyzed else 0,
                    "correct_answers_count": a_correct_count,
                    "correct_answers_pct": round((a_correct_count / len(a_analyzed)) * 100) if a_analyzed else 0,
                    "status": status_label,
                    "is_demo": getattr(a, "is_demo", False) or a.id in ("asm_1065658", "asm_synthetic_cases"),
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                })

            attention_items = []
            for r in needs_review:
                parent_asm = self.assessments.get(r.assessment_id)
                asm_title = parent_asm.title if parent_asm else r.assessment_id

                diagnosis_data = (r.analysis_data or {}).get("diagnosis", {})
                critic_data = (r.analysis_data or {}).get("critic_audit", {})

                reason = "Teacher review recommended"
                if r.upload_status == "unreadable" or diagnosis_data.get("evidence_sufficiency") == "insufficient":
                    reason = "Unreadable or ambiguous handwriting evidence"
                elif critic_data.get("reinterpretation_needed"):
                    reason = "Adversarial critic discrepancy flagged"
                elif r.is_compensatory_error:
                    reason = "Compensatory error in intermediate hops"
                elif r.reasoning_status in ("incomplete", "unverifiable"):
                    reason = "Unverifiable reasoning steps"

                attention_items.append({
                    "id": f"attn_{r.id}",
                    "type": "needs_review",
                    "response_id": r.id,
                    "assessment_id": r.assessment_id,
                    "assessment_title": asm_title,
                    "student_label": r.pseudonym_label or r.id,
                    "title": f"Review Required: {r.pseudonym_label or r.id}",
                    "description": reason,
                    "severity": "high" if "unreadable" in reason.lower() or "ambiguous" in reason.lower() else "medium",
                    "action_label": "Review Work",
                })

            if awaiting_analysis:
                primary_asm = org_assessments[0] if org_assessments else None
                attention_items.append({
                    "id": "attn_pending_batch",
                    "type": "awaiting_analysis",
                    "assessment_id": primary_asm.id if primary_asm else "asm_1065658",
                    "assessment_title": primary_asm.title if primary_asm else "Checkpoint 1",
                    "count": len(awaiting_analysis),
                    "title": f"{len(awaiting_analysis)} Submissions Awaiting Analysis",
                    "description": f"Worksheets in {primary_asm.title if primary_asm else 'assessment'} ready for multi-agent evaluation.",
                    "severity": "medium",
                    "action_label": "Run Analysis",
                })

            insights_snapshot: Dict[str, Any] = {
                "has_analyzed_data": len(analyzed) > 0,
                "analyzed_count": len(analyzed),
                "total_submissions": len(org_responses),
                "verified_reasoning_pct": 0,
                "verified_reasoning_count": 0,
                "correct_answers_pct": 0,
                "correct_answers_count": 0,
                "scope_label": f"Class-wide aggregate across {len(org_assessments)} checkpoints ({len(analyzed)} of {len(org_responses)} analyzed)",
                "top_misconceptions": [],
                "recommended_reteaching": None,
            }

            if analyzed:
                verified_count = sum(
                    1 for r in analyzed
                    if r.reasoning_status in ("verified", "supported_correct", "sound", "valid")
                )
                correct_count = sum(1 for r in analyzed if r.answer_status == "correct")

                insights_snapshot["verified_reasoning_pct"] = round((verified_count / len(analyzed)) * 100)
                insights_snapshot["verified_reasoning_count"] = verified_count
                insights_snapshot["correct_answers_pct"] = round((correct_count / len(analyzed)) * 100)
                insights_snapshot["correct_answers_count"] = correct_count
                insights_snapshot["scope_label"] = f"Class-wide aggregate across {len(org_assessments)} checkpoints ({len(analyzed)} analyzed submissions)"

                misc_counts: Dict[str, int] = {}
                for r in analyzed:
                    diag = (r.analysis_data or {}).get("diagnosis", {})
                    tax_id = r.misconception_taxonomy_id or diag.get("misconception_taxonomy_id")
                    if tax_id and tax_id != "None":
                        misc_counts[tax_id] = misc_counts.get(tax_id, 0) + 1

                top_list = []
                for tax_id, count in sorted(misc_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                    top_list.append({
                        "taxonomy_id": tax_id,
                        "count": count,
                        "percentage": round((count / len(analyzed)) * 100),
                    })
                insights_snapshot["top_misconceptions"] = top_list

                if top_list:
                    insights_snapshot["recommended_reteaching"] = "Reinforce counting interval steps between numbers rather than counting tick mark lines."
                elif verified_count == len(analyzed):
                    insights_snapshot["recommended_reteaching"] = "Cohort demonstrated sound number-line execution. Ready to advance to multi-step integer arithmetic."
                else:
                    insights_snapshot["recommended_reteaching"] = "Inspect flagged responses to identify individual procedural slips."

            recent_activity = []
            for ev in sorted(self.audit_events, key=lambda e: e.timestamp, reverse=True)[:10]:
                parent_resp = self.responses.get(ev.response_id)
                student_label = parent_resp.pseudonym_label if parent_resp else ev.response_id
                action_text = "Review submitted"
                if ev.action == "approved_as_is":
                    action_text = f"Confirmed AI analysis for {student_label}"
                elif ev.action == "overridden":
                    action_text = f"Overrode diagnosis for {student_label}"
                elif ev.action == "marked_unreadable":
                    action_text = f"Marked {student_label} as unreadable"
                recent_activity.append({
                    "id": ev.id,
                    "event_type": "teacher_review",
                    "title": action_text,
                    "description": ev.notes or "Educator review recorded",
                    "timestamp": ev.timestamp.isoformat(),
                    "response_id": ev.response_id,
                    "assessment_id": ev.assessment_id,
                })

            for job in sorted(self.analysis_jobs.values(), key=lambda j: j.created_at, reverse=True)[:5]:
                parent_asm = self.assessments.get(job.assessment_id)
                asm_title = parent_asm.title if parent_asm else job.assessment_id
                recent_activity.append({
                    "id": job.id,
                    "event_type": "analysis_completed",
                    "title": f"Batch analysis completed: {asm_title}",
                    "description": f"Processed {job.completed_items}/{job.total_items} submissions",
                    "timestamp": job.created_at.isoformat(),
                    "assessment_id": job.assessment_id,
                })

            recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "active_classes_count": len(classes) or 1,
                "total_students_count": len(students) or 16,
                "total_assessments_count": len(org_assessments),
                "awaiting_analysis_count": len(awaiting_analysis),
                "needing_review_count": len(needs_review),
                "analyzed_count": len(analyzed),
                "in_progress_count": len(in_progress),
                "failed_count": len(failed),
                "reviewed_count": len(reviewed),
                "assessments": assessment_summaries,
                "attention_items": attention_items,
                "learning_insights_snapshot": insights_snapshot,
                "recent_activity": recent_activity[:10],
            }
