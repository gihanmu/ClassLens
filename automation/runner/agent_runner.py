"""Coding agent invocation interfaces for ClassLens autonomous development."""

from __future__ import annotations

import abc
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.runner.config import REPO_ROOT
from automation.runner.safety import SafetyEnforcer, SafetyViolationError
from automation.runner.task_parser import TaskSpec


@dataclass
class AgentExecutionResult:
    success: bool
    summary: str
    modified_files: List[str] = field(default_factory=list)
    output_log: str = ""
    external_calls_count: int = 0
    estimated_cost_usd: float = 0.0
    error_message: Optional[str] = None


class BaseAgentRunner(abc.ABC):
    """Abstract interface for autonomous coding agents."""

    @abc.abstractmethod
    def execute(self, task: TaskSpec, context: Dict[str, Any]) -> AgentExecutionResult:
        """Execute the primary task implementation."""
        pass

    @abc.abstractmethod
    def repair(self, task: TaskSpec, failure_context: Dict[str, Any], attempt: int) -> AgentExecutionResult:
        """Attempt a bounded corrective repair based on test/build failures."""
        pass


class DeterministicAgentRunner(BaseAgentRunner):
    """Offline, deterministic runner for verification, dry runs, and local automation.

    Guarantees $0.00 spending and zero external API calls.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def execute(self, task: TaskSpec, context: Dict[str, Any]) -> AgentExecutionResult:
        summary = f"Executed deterministic offline verification for task {task.task_id}."
        return AgentExecutionResult(
            success=True,
            summary=summary,
            modified_files=[],
            output_log="Deterministic runner executed successfully in offline mode.",
            external_calls_count=0,
            estimated_cost_usd=0.0,
        )

    def repair(self, task: TaskSpec, failure_context: Dict[str, Any], attempt: int) -> AgentExecutionResult:
        return AgentExecutionResult(
            success=False,
            summary=f"Deterministic runner cannot synthesize novel code repairs on attempt {attempt}.",
            modified_files=[],
            error_message="Automatic repair requires interactive review or configured repair strategy.",
            external_calls_count=0,
            estimated_cost_usd=0.0,
        )


class AgyCliAgentRunner(BaseAgentRunner):
    """Headless Antigravity CLI (`agy`) runner.

    Executes non-interactive sessions via `agy --print`.
    Strictly gated by SafetyEnforcer: will NOT execute unless explicit
    unexpired approval token and authorization are confirmed.
    """

    def __init__(self, safety_enforcer: Optional[SafetyEnforcer] = None, agy_binary: str = "agy") -> None:
        self.safety = safety_enforcer or SafetyEnforcer()
        self.agy_binary = agy_binary

    def execute(self, task: TaskSpec, context: Dict[str, Any]) -> AgentExecutionResult:
        # Agy CLI is an external LLM interface requiring network connectivity and metered quota.
        # It can NEVER run without explicit approval and external inference authorization.
        if not task.cost_restrictions.allow_external_inference or not task.cost_restrictions.approval_token:
            raise SafetyViolationError(
                f"AgyCliAgentRunner for task '{task.task_id}' requires external network access "
                f"and metered cloud LLM calls. Operation BLOCKED under mandatory safety policy "
                f"(DEFAULT_EXTERNAL_SPENDING_LIMIT_USD=$0.00). "
                f"An unexpired approval token in automation/approvals/ is strictly required."
            )

        # Pre-execution safety gate
        self.safety.validate_cost_authorization(task.cost_restrictions.__dict__, task_id=task.task_id)

        prompt = (
            f"You are executing ClassLens Task {task.task_id}: {task.title}\n\n"
            f"Objective:\n{task.objective}\n\n"
            f"Acceptance Criteria:\n" + "\n".join(f"- {ac}" for ac in task.acceptance_criteria) + "\n\n"
            f"Allowed Files:\n" + "\n".join(f"- {f}" for f in task.allowed_file_changes) + "\n\n"
            f"Constraints: Do not modify files outside allowed_file_changes. Keep CLASSLENS_AI_MODE=mock."
        )

        return self._run_agy(prompt, task)

    def repair(self, task: TaskSpec, failure_context: Dict[str, Any], attempt: int) -> AgentExecutionResult:
        if not task.cost_restrictions.allow_external_inference or not task.cost_restrictions.approval_token:
            raise SafetyViolationError(
                f"AgyCliAgentRunner repair for task '{task.task_id}' is BLOCKED without approval token."
            )

        # Pre-repair safety gate
        self.safety.validate_cost_authorization(task.cost_restrictions.__dict__, task_id=task.task_id)

        failures = failure_context.get("failures", [])
        prompt = (
            f"ClassLens Task {task.task_id} failed verification during repair attempt {attempt}/3.\n\n"
            f"Failure Details:\n" + "\n".join(failures) + "\n\n"
            f"Fix the issue while keeping changes strictly within allowed_file_changes."
        )

        return self._run_agy(prompt, task)

    def _run_agy(self, prompt: str, task: TaskSpec) -> AgentExecutionResult:
        cmd = [
            self.agy_binary,
            "--print",
            prompt,
            "--output-format",
            "text",
            "--mode",
            "accept-edits",
        ]

        try:
            res = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=600,
            )
            success = res.returncode == 0
            return AgentExecutionResult(
                success=success,
                summary=f"agy CLI execution completed with return code {res.returncode}.",
                output_log=res.stdout + ("\n" + res.stderr if res.stderr else ""),
                external_calls_count=1 if success else 0,
                estimated_cost_usd=0.01,  # Estimated per-turn cost
                error_message=res.stderr if not success else None,
            )
        except Exception as e:
            return AgentExecutionResult(
                success=False,
                summary=f"agy CLI invocation failed: {e}",
                error_message=str(e),
            )
