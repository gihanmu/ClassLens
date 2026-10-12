"""Unit and regression tests for ClassLens Gate 4B.2:
Metric Consistency, Durable Local Persistence, and Qualitative Confidence.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from services.api.repository.local_persistence import LocalStatePersistence
from services.api.repository.memory_repo import MemoryRepository
from services.worker.agents.pipeline import MultiAgentPipeline


@pytest.fixture
def temp_storage():
    """Provides an isolated temporary directory for local persistence testing."""
    temp_dir = tempfile.mkdtemp(prefix="classlens_test_store_")
    old_env = os.environ.get("CLASSLENS_DATA_DIR")
    os.environ["CLASSLENS_DATA_DIR"] = temp_dir
    yield Path(temp_dir)
    # Cleanup
    if old_env is not None:
        os.environ["CLASSLENS_DATA_DIR"] = old_env
    else:
        os.environ.pop("CLASSLENS_DATA_DIR", None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_metric_consistency_and_scope_definitions(temp_storage):
    """Verifies metric consistency between Active Checkpoint (13 responses) and Class-Wide Scope (16 responses)."""
    repo = MemoryRepository()

    # Pre-analyze Checkpoint 1 (asm_1065658) responses deterministically via the multi-agent pipeline
    for r in list(repo.responses.values()):
        if r.assessment_id == "asm_1065658":
            analysis = MultiAgentPipeline.analyze_response(response_id=r.id)
            r.task_status = "COMPLETED"
            r.answer_status = str(analysis.answer_status.value) if hasattr(analysis.answer_status, "value") else str(analysis.answer_status)
            r.reasoning_status = str(analysis.reasoning_status.value) if hasattr(analysis.reasoning_status, "value") else str(analysis.reasoning_status)
            r.is_compensatory_error = analysis.is_compensatory_error
            r.needs_teacher_review = analysis.needs_teacher_review
            r.misconception_taxonomy_id = analysis.diagnosis.misconception_taxonomy_id
            r.analysis_data = analysis.model_dump()
            repo.update_response(r)

    summary = repo.get_dashboard_summary("org_cedar_sec")

    # 1. Total counts across all assessments
    assert summary["total_assessments_count"] == 2
    assert summary["total_students_count"] == 16
    assert summary["awaiting_analysis_count"] == 0
    assert summary["needing_review_count"] == 4  # 3 in Checkpoint 1 + 1 in Synthetic Case 3

    # 2. Per-assessment breakdown in assessment_summaries
    summaries = {a["id"]: a for a in summary["assessments"]}
    assert "asm_1065658" in summaries
    assert "asm_synthetic_cases" in summaries

    # Checkpoint 1 (asm_1065658): 13 submissions
    cp1 = summaries["asm_1065658"]
    assert cp1["total_submissions"] == 13
    assert cp1["analyzed_count"] == 13
    assert cp1["needs_review_count"] == 3
    assert cp1["correct_answers_count"] == 9
    assert cp1["correct_answers_pct"] == 69  # round(9/13 * 100) = 69%
    assert cp1["verified_reasoning_count"] == 8
    assert cp1["verified_reasoning_pct"] == 62  # round(8/13 * 100) = 62%

    # Synthetic Cases (asm_synthetic_cases): 3 submissions
    synth = summaries["asm_synthetic_cases"]
    assert synth["total_submissions"] == 3
    assert synth["analyzed_count"] == 3
    assert synth["needs_review_count"] == 1
    assert synth["correct_answers_count"] == 1  # Case 1 only
    assert synth["verified_reasoning_count"] == 1  # Case 1 only

    # 3. Class-Wide Learning Insights Snapshot (Cohort of 16 submissions)
    snapshot = summary["learning_insights_snapshot"]
    assert snapshot["analyzed_count"] == 16
    assert snapshot["total_submissions"] == 16
    assert snapshot["correct_answers_count"] == 10  # 9 + 1 = 10
    assert snapshot["correct_answers_pct"] == 62    # round(10/16 * 100) = 62%
    assert snapshot["verified_reasoning_count"] == 9 # 8 + 1 = 9
    assert snapshot["verified_reasoning_pct"] == 56   # round(9/16 * 100) = 56%
    assert "Class-wide aggregate across 2 checkpoints" in snapshot["scope_label"]


def test_durable_persistence_across_process_restart(temp_storage):
    """Simulates backend server restart (fresh MemoryRepository instantiation) to verify persistence."""
    # 1. Initialize first repo instance and perform teacher override on an analyzed synthetic case
    repo1 = MemoryRepository()
    target_resp_id = "case_02_off_by_one_error"
    original_resp = repo1.get_response(target_resp_id)
    assert original_resp is not None
    assert original_resp.teacher_review_status == "unreviewed"

    # Teacher reviews and records an override
    updated = repo1.record_teacher_override(
        assessment_id="asm_synthetic_cases",
        response_id=target_resp_id,
        teacher_id="usr_sarah_lim",
        action="overridden",
        override_taxonomy="MISC-OFF-BY-ONE-DIR-REV",
        notes="Verified compensatory steps manually. Student flipped sign on intermediate jump.",
    )
    assert updated.teacher_review_status == "overridden"
    assert updated.teacher_override_taxonomy_id == "MISC-OFF-BY-ONE-DIR-REV"
    assert "Verified compensatory steps" in updated.teacher_notes

    # Verify audit event was logged in repo1
    events1 = repo1.get_audit_events_for_response(target_resp_id)
    assert len(events1) >= 1
    assert any(e.action == "overridden" for e in events1)

    # 2. Simulate complete process termination & reboot by creating new repo instance
    repo2 = MemoryRepository()

    # Check that persisted state was restored on startup
    restored_resp = repo2.get_response(target_resp_id)
    assert restored_resp is not None
    assert restored_resp.teacher_review_status == "overridden"
    assert restored_resp.teacher_override_taxonomy_id == "MISC-OFF-BY-ONE-DIR-REV"
    assert "Verified compensatory steps" in restored_resp.teacher_notes

    # Check that audit events survived restart
    events2 = repo2.get_audit_events_for_response(target_resp_id)
    assert len(events2) >= 1
    assert any(e.action == "overridden" for e in events2)

    # Check tenant file exists on disk
    tenant_file = temp_storage / "org_cedar_sec_state.json"
    assert tenant_file.exists()


def test_original_ai_findings_preserved_after_override(temp_storage):
    """Ensures three-way separation of concerns: AI findings remain intact when educator overrides."""
    repo = MemoryRepository()
    target_resp_id = "case_03_ambiguous_incomplete"  # Ambiguous Case 3
    original_resp = repo.get_response(target_resp_id)
    assert original_resp is not None

    ai_diagnosis_original = dict(original_resp.analysis_data["diagnosis"])
    ai_critic_original = dict(original_resp.analysis_data["critic_audit"])

    # Teacher confirms as unreadable
    repo.record_teacher_override(
        assessment_id="asm_synthetic_cases",
        response_id=target_resp_id,
        teacher_id="usr_sarah_lim",
        action="marked_unreadable",
        notes="Worksheet is indeed too faint for evaluation.",
    )

    # Reload response
    current_resp = repo.get_response(target_resp_id)
    assert current_resp.teacher_review_status == "marked_unreadable"

    # AI diagnosis and critic data must be unmodified
    assert current_resp.analysis_data["diagnosis"]["reasoning_status"] == ai_diagnosis_original["reasoning_status"]
    assert current_resp.analysis_data["critic_audit"]["audit_verdict"] == ai_critic_original["audit_verdict"]
    assert current_resp.analysis_data["diagnosis"]["evidence_sufficiency"] == "insufficient"


def test_confidence_is_heuristic_indicator_not_calibrated():
    """Validates that Critic and visual confidence scores are qualitative heuristic indicators."""
    analysis = MultiAgentPipeline.analyze_response("case_03_ambiguous_incomplete")

    # Heuristic rules: confidence is bounded by min(visual, diag, 0.65)
    assert analysis.critic_audit.confidence <= 0.65
    assert analysis.critic_audit.audit_verdict == "review_required"
    assert analysis.needs_teacher_review is True
    # Ensure audit passes evidence_grounded=False due to insufficient evidence
    assert analysis.critic_audit.evidence_grounded is False
