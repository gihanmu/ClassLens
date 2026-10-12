"""Unattended Task Queue and State Machine for ClassLens Autonomous Development.

Enforces:
- Strict Lifecycle: PENDING -> PREFLIGHT -> RUNNING -> VERIFYING -> PR_CREATED -> COMPLETE
- Ancillary States: BLOCKED, FAILED, AWAITING_APPROVAL, RETRYING
- Single-task working tree lock (fcntl.flock)
- Safe recovery of interrupted executions
- Dependency validation and duplicate execution prevention
- Bounded repair attempts and actionable reports
"""

from __future__ import annotations

import datetime
import fcntl
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.runner.config import (
    DEFAULT_TASK_TIMEOUT_SECONDS,
    MAX_REPAIR_ATTEMPTS,
    QUEUE_DIR,
    QUEUE_LOCK_FILE,
    QUEUE_STATE_FILE,
    REPO_ROOT,
    STATE_AWAITING_APPROVAL,
    STATE_BLOCKED,
    STATE_COMPLETE,
    STATE_FAILED,
    STATE_PENDING,
    STATE_PREFLIGHT,
    STATE_PR_CREATED,
    STATE_RETRYING,
    STATE_RUNNING,
    STATE_VERIFYING,
    VALID_QUEUE_STATES,
)
from automation.runner.orchestrator import AutonomousOrchestrator
from automation.runner.reporter import ExecutionReportData
from automation.runner.safety import SafetyViolationError
from automation.runner.task_parser import TaskParser, TaskSpec

logger = logging.getLogger("ClassLensTaskQueue")


class QueueLockError(Exception):
    """Raised when queue lock cannot be acquired or working tree is contested."""
    pass


@dataclass
class TaskQueueEntry:
    task_id: str
    state: str
    created_at: str
    updated_at: str
    dependencies: List[str] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = MAX_REPAIR_ATTEMPTS
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    branch: Optional[str] = None
    error_message: Optional[str] = None
    facts_observed: List[str] = field(default_factory=list)
    inferred_conclusions: List[str] = field(default_factory=list)


class TaskQueue:
    """Coordinates sequential, unattended task execution with state persistence and concurrency locks."""

    def __init__(
        self,
        queue_state_file: Path = QUEUE_STATE_FILE,
        lock_file: Path = QUEUE_LOCK_FILE,
        task_parser: Optional[TaskParser] = None,
        orchestrator: Optional[AutonomousOrchestrator] = None,
    ) -> None:
        self.state_file = queue_state_file
        self.lock_file = lock_file
        self.parser = task_parser or TaskParser()
        self.orchestrator = orchestrator or AutonomousOrchestrator(task_parser=self.parser)
        self._lock_fd: Optional[int] = None

        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    # Context manager for acquiring exclusive file lock
    def acquire_lock(self) -> None:
        """Acquire non-blocking exclusive lock on working tree."""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_fd = fd
        except (BlockingIOError, OSError) as e:
            os.close(fd)
            raise QueueLockError(
                f"Another autonomous runner owns the working tree lock ({self.lock_file}). "
                "Concurrent executions are prohibited to prevent working tree corruption."
            ) from e

    def release_lock(self) -> None:
        """Release exclusive lock."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None

    def __enter__(self) -> "TaskQueue":
        self.acquire_lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release_lock()

    def load_state(self) -> Dict[str, TaskQueueEntry]:
        """Load persistent queue state from disk."""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            entries: Dict[str, TaskQueueEntry] = {}
            for tid, data in raw.items():
                entries[tid] = TaskQueueEntry(**data)
            return entries
        except Exception as e:
            logger.error("Failed to load queue state file: %s. Re-initializing empty state.", e)
            return {}

    def save_state(self, state: Dict[str, TaskQueueEntry]) -> None:
        """Atomically persist queue state to disk."""
        tmp_file = self.state_file.with_suffix(".tmp")
        data = {tid: asdict(entry) for tid, entry in state.items()}
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp_file.replace(self.state_file)

    def register_task(self, task_spec: TaskSpec) -> TaskQueueEntry:
        """Register a task into the queue if not already present."""
        state = self.load_state()
        if task_spec.task_id in state:
            return state[task_spec.task_id]

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = TaskQueueEntry(
            task_id=task_spec.task_id,
            state=STATE_PENDING,
            created_at=now,
            updated_at=now,
            dependencies=task_spec.dependencies,
            attempts=0,
            max_attempts=MAX_REPAIR_ATTEMPTS,
        )
        state[task_spec.task_id] = entry
        self.save_state(state)
        return entry

    def transition_state(
        self,
        task_id: str,
        new_state: str,
        error_message: Optional[str] = None,
        commit_sha: Optional[str] = None,
        pr_url: Optional[str] = None,
        branch: Optional[str] = None,
        observed_facts: Optional[List[str]] = None,
        inferred_conclusions: Optional[List[str]] = None,
    ) -> TaskQueueEntry:
        """Transition a task to a new lifecycle state."""
        if new_state not in VALID_QUEUE_STATES:
            raise ValueError(f"Invalid queue state '{new_state}'.")

        state = self.load_state()
        if task_id not in state:
            raise KeyError(f"Task '{task_id}' not found in queue.")

        entry = state[task_id]
        logger.info("Task %s: %s -> %s", task_id, entry.state, new_state)

        entry.state = new_state
        entry.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if new_state == STATE_COMPLETE:
            entry.error_message = None
        elif error_message is not None:
            entry.error_message = error_message
        if commit_sha:
            entry.commit_sha = commit_sha
        if pr_url:
            entry.pr_url = pr_url
        if branch:
            entry.branch = branch
        if observed_facts:
            entry.facts_observed.extend(observed_facts)
        if inferred_conclusions:
            entry.inferred_conclusions.extend(inferred_conclusions)

        self.save_state(state)
        return entry

    def recover_interrupted_tasks(self) -> None:
        """Recover any tasks left in transient RUNNING or VERIFYING state by a crash/reboot."""
        state = self.load_state()
        modified = False
        for tid, entry in state.items():
            if entry.state in [STATE_RUNNING, STATE_VERIFYING]:
                logger.warning("Found interrupted task %s in state %s. Recovering...", tid, entry.state)
                if entry.attempts < entry.max_attempts:
                    entry.state = STATE_RETRYING
                    entry.error_message = "Execution was interrupted unexpectedly; recovered to RETRYING."
                else:
                    entry.state = STATE_FAILED
                    entry.error_message = "Execution was interrupted and retry limit exhausted."
                entry.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                modified = True
        if modified:
            self.save_state(state)

    def execute_task(self, task_id: str) -> TaskQueueEntry:
        """Execute a single task through the full lifecycle with state machine checks."""
        state = self.load_state()
        if task_id not in state:
            task_spec = self.parser.find_task(task_id)
            self.register_task(task_spec)
            state = self.load_state()

        entry = state[task_id]

        # Prevent duplicate execution of completed tasks
        if entry.state == STATE_COMPLETE:
            logger.info("Task %s is already COMPLETE. Skipping execution.", task_id)
            return entry

        task_spec = self.parser.find_task(task_id)

        # 1. Dependency Resolution
        for dep in task_spec.dependencies:
            # Check if dependency corresponds to another task_id in state
            if dep in state and state[dep].state != STATE_COMPLETE:
                msg = f"Dependency '{dep}' is in state '{state[dep].state}', not COMPLETE."
                self.transition_state(
                    task_id,
                    STATE_BLOCKED,
                    error_message=msg,
                    observed_facts=[f"Dependency {dep} state is {state[dep].state}"],
                    inferred_conclusions=[f"Task {task_id} cannot proceed until {dep} completes."],
                )
                return self.load_state()[task_id]

        # 2. Transition to PREFLIGHT
        entry.attempts += 1
        self.transition_state(
            task_id,
            STATE_PREFLIGHT,
            observed_facts=[f"Initiated execution attempt {entry.attempts}/{entry.max_attempts}"],
        )

        # 3. Check for Approval Requirements
        if task_spec.cost_restrictions.allow_external_inference or task_spec.cost_restrictions.max_cost_usd > 0.0:
            if not task_spec.cost_restrictions.approval_token:
                msg = "Task requests external inference but lacks an approval token."
                self.transition_state(
                    task_id,
                    STATE_AWAITING_APPROVAL,
                    error_message=msg,
                    observed_facts=["Zero approval token specified in task configuration."],
                    inferred_conclusions=["Human authorizer must provide cryptographic approval token."],
                )
                return self.load_state()[task_id]

        # 4. Transition to RUNNING
        self.transition_state(task_id, STATE_RUNNING)

        # 5. Run Orchestrator
        try:
            report: ExecutionReportData = self.orchestrator.run_task(task_id)
        except Exception as e:
            logger.exception("Task %s failed during orchestrator run: %s", task_id, e)
            if entry.attempts < entry.max_attempts:
                self.transition_state(
                    task_id,
                    STATE_RETRYING,
                    error_message=str(e),
                    observed_facts=[f"Exception occurred: {e}"],
                )
            else:
                self.transition_state(
                    task_id,
                    STATE_FAILED,
                    error_message=str(e),
                    observed_facts=[f"Exception occurred: {e}"],
                    inferred_conclusions=["Retry limit reached; task failed."],
                )
            return self.load_state()[task_id]

        # 6. Process Report Results
        observed_facts = [
            f"Orchestrator reported status: {report.status}",
            f"Tests passed: {len([t for t in report.test_results if t.get('passed')])}/{len(report.test_results)}",
            f"External spend incurred: ${report.estimated_external_cost_usd:.2f}",
        ]
        inferred_conclusions = [report.summary_of_changes]

        if report.status in ["SUCCESS", "DRY_RUN"]:
            if report.pull_request_url:
                self.transition_state(
                    task_id,
                    STATE_PR_CREATED,
                    commit_sha=report.commit_sha,
                    pr_url=report.pull_request_url,
                    branch=report.branch,
                    observed_facts=observed_facts,
                    inferred_conclusions=inferred_conclusions,
                )
            self.transition_state(
                task_id,
                STATE_COMPLETE,
                commit_sha=report.commit_sha,
                pr_url=report.pull_request_url,
                branch=report.branch,
                observed_facts=observed_facts,
                inferred_conclusions=inferred_conclusions,
            )
        elif report.status == "BLOCKED":
            self.transition_state(
                task_id,
                STATE_BLOCKED,
                error_message=report.summary_of_changes,
                observed_facts=observed_facts,
                inferred_conclusions=inferred_conclusions,
            )
        elif report.status == "SAFETY_VIOLATION":
            self.transition_state(
                task_id,
                STATE_FAILED,
                error_message=report.summary_of_changes,
                observed_facts=observed_facts,
                inferred_conclusions=["Safety enforcer halted execution."],
            )
        else:
            if entry.attempts < entry.max_attempts:
                self.transition_state(
                    task_id,
                    STATE_RETRYING,
                    error_message=report.summary_of_changes,
                    observed_facts=observed_facts,
                )
            else:
                self.transition_state(
                    task_id,
                    STATE_FAILED,
                    error_message=report.summary_of_changes,
                    observed_facts=observed_facts,
                    inferred_conclusions=["Retry limit reached; task failed."],
                )

        return self.load_state()[task_id]

    def run_queue(self, task_ids: List[str]) -> Dict[str, TaskQueueEntry]:
        """Execute a sequential queue of tasks stopping on any blocking condition."""
        results: Dict[str, TaskQueueEntry] = {}
        with self:
            self.recover_interrupted_tasks()
            for tid in task_ids:
                logger.info("TaskQueue: Starting task %s", tid)
                entry = self.execute_task(tid)
                results[tid] = entry
                if entry.state in [STATE_FAILED, STATE_BLOCKED, STATE_AWAITING_APPROVAL]:
                    logger.warning("Task %s entered terminal or blocking state %s. Stopping queue.", tid, entry.state)
                    break
        return results
