"""Unit tests for ClassLens Autonomous Development Workflow and Safety Enforcer."""

import json
import tempfile
from pathlib import Path

import pytest

from automation.runner.config import TASKS_DIR
from automation.runner.orchestrator import AutonomousOrchestrator
from automation.runner.reporter import ExecutionReportData, ReportGenerator
from automation.runner.safety import SafetyEnforcer, SafetyViolationError
from automation.runner.task_parser import TaskParser, TaskSpec
from automation.runner.verifier import QualityVerifier, TestCommand


def test_task_schema_validation_valid_tasks():
    """Verify all repository tasks conform to task_schema.json."""
    parser = TaskParser()
    tasks = list(TASKS_DIR.glob("*.yaml"))
    assert len(tasks) >= 3, "Expected at least 3 task specifications"

    for task_file in tasks:
        task = parser.load_task(task_file)
        assert task.task_id
        assert task.title
        assert task.objective
        assert isinstance(task.acceptance_criteria, list)
        assert isinstance(task.allowed_file_changes, list)


def test_safety_enforcer_rejects_unapproved_spend():
    """Verify deny-by-default policy rejects spend even below the $0.50 approval threshold."""
    enforcer = SafetyEnforcer()

    # Spend below $0.50 without token
    with pytest.raises(SafetyViolationError, match="without an approval token"):
        enforcer.validate_cost_authorization({
            "max_cost_usd": 0.25,
            "allow_external_inference": True,
            "requires_cloud_provisioning": False,
        })


def test_safety_enforcer_rejects_cloud_provisioning():
    """Verify paid cloud provisioning is unconditionally blocked."""
    enforcer = SafetyEnforcer()

    with pytest.raises(SafetyViolationError, match="paid cloud provisioning"):
        enforcer.validate_cost_authorization({
            "max_cost_usd": 0.00,
            "allow_external_inference": False,
            "requires_cloud_provisioning": True,
        })


def test_safety_enforcer_rejects_protected_files():
    """Verify modifications to .env, safety.py, or credentials raise safety violations."""
    enforcer = SafetyEnforcer()

    # Attempt to modify .env
    with pytest.raises(SafetyViolationError, match="protected file"):
        enforcer.validate_file_changes([".env"], ["*"])

    # Attempt to modify safety.py
    with pytest.raises(SafetyViolationError, match="protected file"):
        enforcer.validate_file_changes(["automation/runner/safety.py"], ["automation/**"])


def test_safety_enforcer_rejects_files_outside_scope():
    """Verify files outside allowed_file_changes raise safety violations."""
    enforcer = SafetyEnforcer()

    with pytest.raises(SafetyViolationError, match="outside the task's allowed_file_changes scope"):
        enforcer.validate_file_changes(["services/api/main.py"], ["tests/unit/*"])


def test_safety_enforcer_verifies_valid_approval_token():
    """Verify a valid approval token permits authorized spend within cap."""
    with tempfile.TemporaryDirectory() as tmpdir:
        approvals_dir = Path(tmpdir)
        token_data = {
            "token_id": "TEST-TOKEN",
            "provider": "google-vertex-ai",
            "purpose": "Unit testing",
            "max_authorized_calls": 3,
            "authorized_cost_usd": 0.10,
            "expires_at": "2099-01-01T00:00:00Z",
            "approved_by": "test-admin",
        }
        token_file = approvals_dir / "TEST-TOKEN.json"
        with open(token_file, "w") as f:
            json.dump(token_data, f)

        enforcer = SafetyEnforcer(approvals_dir=approvals_dir)

        # Within cap -> should not raise
        enforcer.validate_cost_authorization({
            "max_cost_usd": 0.05,
            "allow_external_inference": True,
            "requires_cloud_provisioning": False,
            "approval_token": "TEST-TOKEN",
        })

        # Exceeds cap -> should raise
        with pytest.raises(SafetyViolationError, match="exceeds authorized cost"):
            enforcer.validate_cost_authorization({
                "max_cost_usd": 0.20,
                "allow_external_inference": True,
                "requires_cloud_provisioning": False,
                "approval_token": "TEST-TOKEN",
            })


def test_safety_enforcer_rejects_expired_token():
    """Verify expired tokens are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        approvals_dir = Path(tmpdir)
        token_data = {
            "token_id": "EXPIRED-TOKEN",
            "provider": "google-vertex-ai",
            "purpose": "Unit testing",
            "max_authorized_calls": 3,
            "authorized_cost_usd": 0.10,
            "expires_at": "2020-01-01T00:00:00Z",
            "approved_by": "test-admin",
        }
        token_file = approvals_dir / "EXPIRED-TOKEN.json"
        with open(token_file, "w") as f:
            json.dump(token_data, f)

        enforcer = SafetyEnforcer(approvals_dir=approvals_dir)

        with pytest.raises(SafetyViolationError, match="expired"):
            enforcer.validate_cost_authorization({
                "max_cost_usd": 0.05,
                "allow_external_inference": True,
                "requires_cloud_provisioning": False,
                "approval_token": "EXPIRED-TOKEN",
            })


def test_quality_verifier_command_execution():
    """Verify command execution returns output and handles exit codes."""
    verifier = QualityVerifier()
    cmd = TestCommand(name="echo test", command="echo 'ClassLens Safe Runner'", timeout_seconds=5)
    res = verifier.run_command(cmd)

    assert res.passed
    assert res.exit_code == 0
    assert "ClassLens Safe Runner" in res.stdout


def test_orchestrator_dry_run():
    """Verify autonomous orchestrator completes dry run successfully."""
    orchestrator = AutonomousOrchestrator(dry_run=True)
    report = orchestrator.run_task("TASK-000-DRY-RUN")

    assert report.status == "DRY_RUN"
    assert report.external_api_calls_made == 0
    assert report.estimated_external_cost_usd == 0.0
    assert report.all_tests_passed if hasattr(report, "all_tests_passed") else True
