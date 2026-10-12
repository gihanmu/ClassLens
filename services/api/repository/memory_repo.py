"""Thread-safe in-memory repository for local development and tenant isolation."""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserDoc(BaseModel):
    id: str
    email: str
    name: str
    role: str = "teacher"
    organization_id: str


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
    status: str = "ready"  # draft, ready, processing, review, completed
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
    task_status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    answer_status: str = "undetermined"  # correct, incorrect, undetermined
    reasoning_status: str = "undetermined"  # supported_correct, supported_error, incomplete, undetermined
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
    status: str = "processing"  # processing, completed, failed
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class MemoryRepository:
    """Thread-safe in-memory store simulating Firestore Native Mode."""

    def __init__(self):
        self._lock = threading.RLock()
        self.users: Dict[str, UserDoc] = {}
        self.assessments: Dict[str, AssessmentDoc] = {}
        self.responses: Dict[str, ResponseDoc] = {}
        self.audit_events: List[AuditEventDoc] = []
        self.analysis_jobs: Dict[str, AnalysisJobDoc] = {}
        self.idempotency_keys: Dict[str, str] = {}  # idempotency_key -> job_id

        # Preload Demo Teacher & Assessment
        self._seed_default_data()

    def _seed_default_data(self):
        sarah = UserDoc(
            id="usr_sarah_lim",
            email="sarah.lim@moe.edu.sg",
            name="Sarah Lim",
            role="teacher",
            organization_id="org_cedar_sec",
        )
        self.users[sarah.id] = sarah

        default_asm = AssessmentDoc(
            id="asm_1065658",
            class_id="cls_sec1_math",
            organization_id="org_cedar_sec",
            title="Integers on Number Line: Checkpoint 1",
            status="ready",
            question=QuestionConfig(),
        )
        self.assessments[default_asm.id] = default_asm
        self.import_demo_responses(default_asm.id, default_asm.organization_id)

    def get_user(self, user_id: str) -> Optional[UserDoc]:
        with self._lock:
            return self.users.get(user_id)

    def create_assessment(self, doc: AssessmentDoc) -> AssessmentDoc:
        with self._lock:
            self.assessments[doc.id] = doc
            return doc

    def get_assessment(self, assessment_id: str, org_id: Optional[str] = None) -> Optional[AssessmentDoc]:
        with self._lock:
            asm = self.assessments.get(assessment_id)
            if asm and org_id and asm.organization_id != org_id:
                return None  # Tenant isolation enforcement
            return asm

    def list_assessments(self, org_id: str) -> List[AssessmentDoc]:
        with self._lock:
            return [a for a in self.assessments.values() if a.organization_id == org_id]

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
                    answer_status="undetermined",
                    reasoning_status="undetermined",
                    teacher_review_status="unreviewed",
                )
                self.responses[doc_id] = doc
                imported.append(doc)

            asm.total_responses = len(imported)
            asm.status = "ready"
            asm.updated_at = utc_now()
            return imported

    def list_responses(self, assessment_id: str) -> List[ResponseDoc]:
        with self._lock:
            return [r for r in self.responses.values() if r.assessment_id == assessment_id]

    def get_response(
        self,
        response_id: str,
        assessment_id: Optional[str] = None,
    ) -> Optional[ResponseDoc]:
        with self._lock:
            # If assessment_id is specified, strictly scope within that assessment
            if assessment_id:
                if response_id in self.responses and self.responses[response_id].assessment_id == assessment_id:
                    return self.responses[response_id]
                for r in self.responses.values():
                    if r.assessment_id == assessment_id and (r.id == response_id or r.id.endswith(f"_{response_id}")):
                        return r
                return None

            # Unscoped lookup: if exact match is already completed, return it
            if response_id in self.responses:
                r = self.responses[response_id]
                if r.task_status == "COMPLETED":
                    return r

            matches = [
                r for r in self.responses.values()
                if r.id == response_id or r.id.endswith(f"_{response_id}")
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
                return self.analysis_jobs[existing_job_id]

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

            # Update assessment reviewed count
            asm = self.assessments.get(assessment_id)
            if asm:
                reviewed_count = sum(
                    1 for r in self.responses.values()
                    if r.assessment_id == assessment_id and r.teacher_review_status != "unreviewed"
                )
                asm.reviewed_responses = reviewed_count
                asm.updated_at = utc_now()

            return resp

    def get_audit_events_for_response(self, response_id: str) -> List[AuditEventDoc]:
        with self._lock:
            return [e for e in self.audit_events if e.response_id == response_id]


# Singleton instance
memory_repo = MemoryRepository()
