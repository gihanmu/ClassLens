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

        # Seed Synthetic Benchmark Checkpoint for Gate 4B Evaluation (Cases 1, 2, and 3)
        synthetic_asm = AssessmentDoc(
            id="asm_synthetic_cases",
            class_id="cls_sec1_math",
            organization_id="org_cedar_sec",
            title="Synthetic Feasibility Benchmark: Cases 1–3",
            status="ready",
            question=QuestionConfig(
                problem_reference_id="synthetic_benchmark",
                question_text="Evaluate -6 + 12 - 4 on the number line (Evaluation Benchmark).",
                latex_formula="-6 + 12 - 4",
                expected_answer="2",
            ),
        )
        self.assessments[synthetic_asm.id] = synthetic_asm
        self.import_synthetic_demo_cases(synthetic_asm.id, synthetic_asm.organization_id)

    def import_synthetic_demo_cases(self, assessment_id: str, org_id: str) -> List[ResponseDoc]:
        """Imports and deterministically analyzes the 3 authorized synthetic cases."""
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

            imported: List[ResponseDoc] = []
            for cid, label, filename in cases:
                doc_id = cid if assessment_id == "asm_synthetic_cases" else f"{assessment_id}_{cid}"
                analysis = MultiAgentPipeline.analyze_response(response_id=cid)
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
                imported.append(doc)

            asm.total_responses = len(imported)
            asm.status = "ready"
            asm.updated_at = utc_now()
            return imported

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
                    answer_status="not_assessed",
                    reasoning_status="not_assessed",
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
                    if r.assessment_id == assessment_id and (
                        r.id == response_id
                        or r.id.endswith(f"_{response_id}")
                        or response_id in r.id
                        or r.id.replace("resp_", "") == response_id.replace("resp_", "")
                    ):
                        return r
                return None

            # Unscoped lookup: if exact match is already completed, return it
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

    def get_dashboard_summary(self, org_id: str) -> Dict[str, Any]:
        """Calculates real teacher-level summary metrics, recent assessments, and attention items."""
        with self._lock:
            org_assessments = [a for a in self.assessments.values() if a.organization_id == org_id]
            asm_ids = {a.id for a in org_assessments}
            org_responses = [r for r in self.responses.values() if r.assessment_id in asm_ids]

            # 1. Classes and student counts
            classes = {a.class_id for a in org_assessments}
            students = {r.pseudonymous_student_id for r in org_responses}

            # 2. Processing lifecycle buckets
            awaiting_analysis = [r for r in org_responses if r.task_status in ("PENDING", "QUEUED")]
            analyzed = [r for r in org_responses if r.task_status == "COMPLETED"]
            in_progress = [r for r in org_responses if r.task_status == "RUNNING"]
            failed = [r for r in org_responses if r.task_status == "FAILED"]

            needs_review = [
                r for r in analyzed
                if r.needs_teacher_review and r.teacher_review_status == "unreviewed"
            ]
            reviewed = [r for r in analyzed if r.teacher_review_status != "unreviewed"]

            # 3. Assessment Summaries
            assessment_summaries = []
            for a in org_assessments:
                a_resps = [r for r in org_responses if r.assessment_id == a.id]
                a_analyzed = [r for r in a_resps if r.task_status == "COMPLETED"]
                a_pending = [r for r in a_resps if r.task_status in ("PENDING", "QUEUED")]
                a_needs_review = [
                    r for r in a_analyzed
                    if r.needs_teacher_review and r.teacher_review_status == "unreviewed"
                ]

                progress_pct = (
                    round((len(a_analyzed) / len(a_resps)) * 100)
                    if a_resps else 0
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
                    "topic": "Integers & Number Lines",
                    "class_id": a.class_id,
                    "class_name": "Sec 1 Mathematics",
                    "total_submissions": len(a_resps),
                    "awaiting_analysis_count": len(a_pending),
                    "analyzed_count": len(a_analyzed),
                    "needs_review_count": len(a_needs_review),
                    "progress_percentage": progress_pct,
                    "status": status_label,
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                })

            # 4. Teacher Attention Items (no fabricated items)
            attention_items = []
            # High priority: analyzed submissions requiring manual teacher review
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

            # Submissions awaiting analysis item (grouped)
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

            # 5. Learning Insights Snapshot
            insights_snapshot: Dict[str, Any] = {
                "has_analyzed_data": len(analyzed) > 0,
                "analyzed_count": len(analyzed),
                "total_submissions": len(org_responses),
                "verified_reasoning_pct": 0,
                "correct_answers_pct": 0,
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
                insights_snapshot["correct_answers_pct"] = round((correct_count / len(analyzed)) * 100)

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

            # 6. Recent Activity
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
                    "description": ev.notes or f"Educator review recorded",
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


# Singleton instance
memory_repo = MemoryRepository()
