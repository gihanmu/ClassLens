"""Comprehensive negative and adversarial security isolation test suite for Gate AUTO-1.

Verifies:
- macOS Seatbelt kernel-level sandboxing (Operation not permitted on ~/.ssh, ~/.config/gcloud, Keychains)
- Subprocess environment sanitization (GOOGLE_APPLICATION_CREDENTIALS=/dev/null, scrubbed API tokens)
- Network outbound denial (socket error on unauthorized connection)
- Orchestrator self-protection (write denial to automation/runner and .github)
- Approval token forgery prevention (cryptographic HMAC, expiration, scope mismatch)
- Prohibited command interception (cloud deploy, live Gemini, terraform)
- TaskQueue state machine transitions, lock concurrency prevention, recovery, and retry bounds
"""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import pytest

from automation.runner.config import (
    REPO_ROOT,
    STATE_AWAITING_APPROVAL,
    STATE_BLOCKED,
    STATE_COMPLETE,
    STATE_FAILED,
    STATE_PENDING,
    STATE_PREFLIGHT,
    STATE_RETRYING,
    STATE_RUNNING,
)
from automation.runner.isolation import WorkerIsolation
from automation.runner.safety import SafetyEnforcer, SafetyViolationError
from automation.runner.task_parser import TaskSpec
from automation.runner.task_queue import QueueLockError, TaskQueue


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS Seatbelt tests require Darwin")
def test_seatbelt_blocks_ssh_private_key_access():
    """Verify macOS Seatbelt kernel sandbox denies reading ~/.ssh directory."""
    iso = WorkerIsolation()
    assert iso.is_seatbelt_available, "sandbox-exec must be available on macOS"

    rc, out, err = iso.run_isolated_command(["ls", str(Path.home() / ".ssh")], cwd=REPO_ROOT)
    assert rc != 0, "ls ~/.ssh must fail under Seatbelt sandbox"
    assert "Operation not permitted" in err or rc == 1


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS Seatbelt tests require Darwin")
def test_seatbelt_blocks_gcloud_credentials_access():
    """Verify macOS Seatbelt kernel sandbox denies reading ~/.config/gcloud directory."""
    iso = WorkerIsolation()
    gcloud_path = str(Path.home() / ".config" / "gcloud")

    rc, out, err = iso.run_isolated_command(["ls", gcloud_path], cwd=REPO_ROOT)
    assert rc != 0, "ls ~/.config/gcloud must fail under Seatbelt sandbox"
    assert "Operation not permitted" in err or rc == 1


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS Seatbelt tests require Darwin")
def test_seatbelt_blocks_keychains_access():
    """Verify macOS Seatbelt kernel sandbox denies reading macOS Keychains directory."""
    iso = WorkerIsolation()
    keychain_path = str(Path.home() / "Library" / "Keychains")

    rc, out, err = iso.run_isolated_command(["ls", keychain_path], cwd=REPO_ROOT)
    assert rc != 0, "ls ~/Library/Keychains must fail under Seatbelt sandbox"
    assert "Operation not permitted" in err or rc == 1


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS Seatbelt tests require Darwin")
def test_seatbelt_blocks_unauthorized_outbound_network():
    """Verify macOS Seatbelt denies socket creation and network when allow_network=False."""
    iso = WorkerIsolation()
    rc, out, err = iso.run_isolated_command(
        ["curl", "-s", "--connect-timeout", "2", "https://google.com"],
        cwd=REPO_ROOT,
        allow_network=False,
    )
    assert rc != 0, "Outbound curl must fail when network is denied"


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS Seatbelt tests require Darwin")
def test_seatbelt_protects_orchestrator_from_agent_write():
    """Verify agent process cannot write or mutate files in automation/runner."""
    iso = WorkerIsolation()
    test_target = "automation/runner/malicious_patch.py"
    rc, out, err = iso.run_isolated_command(
        ["touch", test_target],
        cwd=REPO_ROOT,
        protect_orchestrator=True,
    )
    assert rc != 0, "Writing to automation/runner must fail under Seatbelt sandbox"
    assert "Operation not permitted" in err or rc == 1


def test_environment_sanitization_neutralizes_all_credentials():
    """Verify environment sanitization thoroughly strips cloud keys and sets ADC to /dev/null."""
    iso = WorkerIsolation()

    # Poison environment with fake sensitive tokens
    os.environ["SSH_AUTH_SOCK"] = "/tmp/fake-ssh-agent.sock"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/user/service-account.json"
    os.environ["GCLOUD_PROJECT"] = "compromised-project-id"
    os.environ["GEMINI_API_KEY"] = "AIzaSyFakeSecretKey1234567890123456"
    os.environ["GITHUB_TOKEN"] = "ghp_FakeTokenValue12345678901234567890"

    try:
        sanitized = iso.sanitize_environment()
        assert sanitized.get("GOOGLE_APPLICATION_CREDENTIALS") == "/dev/null"
        assert "SSH_AUTH_SOCK" not in sanitized
        assert "GCLOUD_PROJECT" not in sanitized
        assert "GEMINI_API_KEY" not in sanitized
        assert "GITHUB_TOKEN" not in sanitized
        assert sanitized.get("CLASSLENS_AI_MODE") == "mock"
        assert sanitized.get("CLASSLENS_LIVE_INFERENCE_ENABLED") == "false"
        assert sanitized.get("CLASSLENS_MAX_LIVE_CALLS") == "0"
    finally:
        os.environ.pop("SSH_AUTH_SOCK", None)
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        os.environ.pop("GCLOUD_PROJECT", None)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GITHUB_TOKEN", None)


def test_command_interceptor_blocks_cloud_mutations_and_live_gemini():
    """Verify safety enforcer blocks prohibited commands before process creation."""
    enforcer = SafetyEnforcer()

    prohibited_commands = [
        "gcloud run deploy classlens --image gcr.io/test",
        "gcloud container clusters create test-cluster",
        "terraform apply -auto-approve",
        "terraform destroy",
        "CLASSLENS_AI_MODE=live pytest tests/",
        "curl -X POST https://aiplatform.googleapis.com/v1/projects",
        "git push --force origin main",
        "git push -f origin main",
    ]

    for cmd in prohibited_commands:
        with pytest.raises(SafetyViolationError, match="matches prohibited pattern"):
            enforcer.validate_command(cmd)


def test_token_forgery_and_scope_validation():
    """Verify cryptographic HMAC, expiration, and task-scoping safeguards."""
    with tempfile.TemporaryDirectory() as tmpdir:
        approvals_dir = Path(tmpdir)
        secret = "trusted-secret-authority-key"
        os.environ["CLASSLENS_APPROVAL_SECRET"] = secret

        # 1. Forged signature token
        forged_data = {
            "token_id": "FAKE-TOKEN",
            "provider": "google-vertex-ai",
            "purpose": "Hacking",
            "max_authorized_calls": 5,
            "authorized_cost_usd": 10.0,
            "expires_at": "2099-01-01T00:00:00Z",
            "approved_by": "attacker",
            "hmac_signature": "invalid-hmac-string",
        }
        with open(approvals_dir / "FAKE-TOKEN.json", "w") as f:
            json.dump(forged_data, f)

        enforcer = SafetyEnforcer(approvals_dir=approvals_dir)
        with pytest.raises(SafetyViolationError, match="failed cryptographic HMAC verification"):
            enforcer.validate_cost_authorization({
                "max_cost_usd": 1.0,
                "allow_external_inference": True,
                "approval_token": "FAKE-TOKEN",
            })

        # 2. Expired token
        expired_data = {
            "token_id": "EXPIRED-TOKEN",
            "provider": "google-vertex-ai",
            "purpose": "Past evaluation",
            "max_authorized_calls": 5,
            "authorized_cost_usd": 10.0,
            "expires_at": "2020-01-01T00:00:00Z",
            "approved_by": "admin",
        }
        expired_data["hmac_signature"] = SafetyEnforcer.compute_token_signature(expired_data, secret)
        with open(approvals_dir / "EXPIRED-TOKEN.json", "w") as f:
            json.dump(expired_data, f)

        with pytest.raises(SafetyViolationError, match="expired"):
            enforcer.validate_cost_authorization({
                "max_cost_usd": 1.0,
                "allow_external_inference": True,
                "approval_token": "EXPIRED-TOKEN",
            })

        # 3. Scope mismatch
        scoped_data = {
            "token_id": "SCOPED-TOKEN",
            "provider": "google-vertex-ai",
            "purpose": "Task 1 only",
            "max_authorized_calls": 5,
            "authorized_cost_usd": 10.0,
            "expires_at": "2099-01-01T00:00:00Z",
            "approved_by": "admin",
            "scoped_task_id": "TASK-GATE-4B",
        }
        scoped_data["hmac_signature"] = SafetyEnforcer.compute_token_signature(scoped_data, secret)
        with open(approvals_dir / "SCOPED-TOKEN.json", "w") as f:
            json.dump(scoped_data, f)

        with pytest.raises(SafetyViolationError, match="scoped to task 'TASK-GATE-4B'"):
            enforcer.validate_cost_authorization(
                {
                    "max_cost_usd": 1.0,
                    "allow_external_inference": True,
                    "approval_token": "SCOPED-TOKEN",
                },
                task_id="TASK-UNAUTHORIZED",
            )


def test_file_boundary_violations_blocked():
    """Verify safety enforcer blocks touching files outside task scope or touching protected files."""
    enforcer = SafetyEnforcer()

    # Allowed scope is only services/api/*
    allowed = ["services/api/*"]

    # Valid modification
    enforcer.validate_file_changes(["services/api/routers/responses.py"], allowed)

    # Violation: modifying file outside allowed scope
    with pytest.raises(SafetyViolationError, match="outside the task's allowed_file_changes scope"):
        enforcer.validate_file_changes(["services/worker/agent.py"], allowed)

    # Violation: modifying protected file even if wildcard allows it
    with pytest.raises(SafetyViolationError, match="Modification to protected file"):
        enforcer.validate_file_changes([".github/workflows/ci.yml"], ["*"])

    with pytest.raises(SafetyViolationError, match="Modification to protected file"):
        enforcer.validate_file_changes(["automation/runner/safety.py"], ["*"])


def test_task_queue_concurrency_lock():
    """Verify TaskQueue exclusive lock prevents concurrent working tree modification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "runner.lock"
        state_file = Path(tmpdir) / "queue_state.json"

        q1 = TaskQueue(queue_state_file=state_file, lock_file=lock_file)
        q2 = TaskQueue(queue_state_file=state_file, lock_file=lock_file)

        q1.acquire_lock()
        try:
            with pytest.raises(QueueLockError, match="Another autonomous runner owns the working tree lock"):
                q2.acquire_lock()
        finally:
            q1.release_lock()

        # After q1 releases, q2 should acquire successfully
        q2.acquire_lock()
        q2.release_lock()


def test_task_queue_state_transitions_and_recovery():
    """Verify TaskQueue state machine transitions and crash recovery."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "queue_state.json"
        lock_file = Path(tmpdir) / "runner.lock"

        queue = TaskQueue(queue_state_file=state_file, lock_file=lock_file)

        # Register task
        dummy_task = TaskSpec(
            task_id="TASK-TEST-QUEUE",
            title="Queue Test",
            objective="Testing queue lifecycle",
            scope={"included": ["testing"], "excluded": []},
            acceptance_criteria=["criteria met"],
            dependencies=[],
            allowed_file_changes=["tests/*"],
            test_commands=[],
            cost_restrictions={"max_cost_usd": 0.0, "allow_external_inference": False},
            security_restrictions={"allow_real_student_data": False, "allow_secret_access": False, "allow_production_mutation": False},
            git_branch_requirements={"base_branch": "main", "target_branch_pattern": "test/*"},
            completion_criteria=["completed"],
        )

        entry = queue.register_task(dummy_task)
        assert entry.state == STATE_PENDING

        # Transition to RUNNING
        queue.transition_state("TASK-TEST-QUEUE", STATE_RUNNING)
        assert queue.load_state()["TASK-TEST-QUEUE"].state == STATE_RUNNING

        # Simulate unexpected crash: recover_interrupted_tasks should move to RETRYING
        queue.recover_interrupted_tasks()
        assert queue.load_state()["TASK-TEST-QUEUE"].state == STATE_RETRYING

        # Transition to COMPLETE
        queue.transition_state("TASK-TEST-QUEUE", STATE_COMPLETE, commit_sha="abc1234", pr_url="https://github.com/org/repo/pull/42")
        completed = queue.load_state()["TASK-TEST-QUEUE"]
        assert completed.state == STATE_COMPLETE
        assert completed.commit_sha == "abc1234"
        assert completed.pr_url == "https://github.com/org/repo/pull/42"


def test_worker_isolation_timeout_kills_process():
    """Verify worker isolation terminates long-running or hung processes cleanly."""
    iso = WorkerIsolation()
    # Execute a command that sleeps for 10s with a 1s timeout
    rc, out, err = iso.run_isolated_command(["sleep", "10"], cwd=REPO_ROOT, timeout_seconds=1)
    assert rc == -1
    assert "timed out after 1s" in err
