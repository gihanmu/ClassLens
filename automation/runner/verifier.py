"""Test, build, and quality gate verifier for ClassLens autonomous development."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from automation.runner.config import REPO_ROOT
from automation.runner.safety import SafetyEnforcer
from automation.runner.task_parser import TaskSpec, TestCommand


@dataclass
class CommandResult:
    name: str
    command: str
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


@dataclass
class VerificationReport:
    all_passed: bool
    command_results: List[CommandResult] = field(default_factory=list)
    secret_findings: List[str] = field(default_factory=list)
    failure_summaries: List[str] = field(default_factory=list)


class QualityVerifier:
    """Runs test commands, build steps, and quality checks defined in a task."""

    def __init__(self, repo_root: Path = REPO_ROOT, safety_enforcer: Optional[SafetyEnforcer] = None) -> None:
        self.repo_root = repo_root
        self.safety = safety_enforcer or SafetyEnforcer()

    def run_command(self, cmd: TestCommand) -> CommandResult:
        """Run a single test command with working directory and timeout."""
        cwd = self.repo_root / cmd.working_directory
        start_time = time.time()

        env = os.environ.copy()
        # Enforce mock mode in verification environment
        env["CLASSLENS_AI_MODE"] = "mock"
        env["CLASSLENS_LIVE_INFERENCE_ENABLED"] = "false"

        try:
            res = subprocess.run(
                cmd.command,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=cmd.timeout_seconds,
                env=env,
            )
            duration = time.time() - start_time
            return CommandResult(
                name=cmd.name,
                command=cmd.command,
                exit_code=res.returncode,
                duration_seconds=round(duration, 2),
                stdout=res.stdout,
                stderr=res.stderr,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return CommandResult(
                name=cmd.name,
                command=cmd.command,
                exit_code=124,
                duration_seconds=round(duration, 2),
                stdout=e.stdout or "",
                stderr=(e.stderr or "") + f"\nCommand timed out after {cmd.timeout_seconds} seconds.",
                timed_out=True,
            )
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                name=cmd.name,
                command=cmd.command,
                exit_code=1,
                duration_seconds=round(duration, 2),
                stdout="",
                stderr=f"Execution failed: {e}",
            )

    def verify_task(self, task: TaskSpec, modified_files: Optional[List[str]] = None) -> VerificationReport:
        """Run all verification commands for a task and perform secret scanning."""
        results: List[CommandResult] = []
        failures: List[str] = []

        # 1. Run test and build commands
        for cmd in task.test_commands:
            res = self.run_command(cmd)
            results.append(res)
            if not res.passed:
                err_detail = res.stderr[-500:] if len(res.stderr) > 500 else res.stderr
                failures.append(f"Command '{cmd.name}' failed with code {res.exit_code}:\n{err_detail.strip()}")

        # 2. Run secret scanning on modified files
        scan_paths: List[Path] = []
        if modified_files:
            scan_paths = [self.repo_root / f for f in modified_files]
        else:
            # Fall back to task allowed files if none explicitly provided
            for pat in task.allowed_file_changes:
                if "*" not in pat:
                    p = self.repo_root / pat
                    if p.exists() and p.is_file():
                        scan_paths.append(p)

        secret_findings = self.safety.scan_for_secrets(scan_paths)
        if secret_findings:
            failures.extend(secret_findings)

        all_passed = len(failures) == 0
        return VerificationReport(
            all_passed=all_passed,
            command_results=results,
            secret_findings=secret_findings,
            failure_summaries=failures,
        )
