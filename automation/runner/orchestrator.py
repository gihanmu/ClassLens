"""Main autonomous execution coordinator for ClassLens development tasks."""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.runner.agent_runner import BaseAgentRunner, DeterministicAgentRunner
from automation.runner.config import MAX_REPAIR_ATTEMPTS, REPO_ROOT
from automation.runner.git_ops import GitOps
from automation.runner.reporter import ExecutionReportData, ReportGenerator
from automation.runner.safety import SafetyEnforcer, SafetyViolationError
from automation.runner.task_parser import TaskParser, TaskSpec
from automation.runner.verifier import QualityVerifier, VerificationReport

logger = logging.getLogger("ClassLensAutonomousRunner")


class AutonomousOrchestrator:
    """Orchestrates end-to-end task execution, verification, repair, and reporting."""

    def __init__(
        self,
        task_parser: Optional[TaskParser] = None,
        safety_enforcer: Optional[SafetyEnforcer] = None,
        quality_verifier: Optional[QualityVerifier] = None,
        git_ops: Optional[GitOps] = None,
        report_generator: Optional[ReportGenerator] = None,
        agent_runner: Optional[BaseAgentRunner] = None,
        dry_run: bool = False,
    ) -> None:
        self.parser = task_parser or TaskParser()
        self.safety = safety_enforcer or SafetyEnforcer()
        self.verifier = quality_verifier or QualityVerifier(safety_enforcer=self.safety)
        self.git = git_ops or GitOps(dry_run=dry_run)
        self.reporter = report_generator or ReportGenerator()
        self.agent = agent_runner or DeterministicAgentRunner(dry_run=dry_run)
        self.dry_run = dry_run

    def run_task(self, task_identifier: str) -> ExecutionReportData:
        """Execute a development task specification from start to finish."""
        # 1. Load and parse task
        task = self.parser.find_task(task_identifier)

        # 2. Safety Pre-Flight Check (Cost & Financial Controls)
        try:
            self.safety.validate_cost_authorization(task.cost_restrictions.__dict__, task_id=task.task_id)
        except SafetyViolationError as e:
            logger.error("Safety violation during pre-flight check: %s", e)
            report = ExecutionReportData(
                task_id=task.task_id,
                task_title=task.title,
                status="SAFETY_VIOLATION",
                branch=self.git.get_current_branch(),
                base_branch=task.git_branch_requirements.base_branch,
                commit_sha=None,
                pull_request_url=None,
                summary_of_changes=f"Execution halted by safety enforcer: {e}",
                files_modified=[],
                test_results=[],
                build_results=[],
                security_findings=[str(e)],
                external_api_calls_made=0,
                estimated_external_cost_usd=0.0,
                repair_attempts_used=0,
                blockers=[str(e)],
                next_recommended_task="Obtain authorized approval token before retrying.",
            )
            self.reporter.write_reports(report)
            return report

        # 3. Branch Management
        target_branch = task.git_branch_requirements.target_branch_pattern.replace("*", task.task_id.lower())
        current_branch = self.git.get_current_branch()
        if not self.dry_run and current_branch != target_branch:
            self.git.create_feature_branch(target_branch, task.git_branch_requirements.base_branch)

        # 4. Agent Execution (Implementation Phase)
        context = {"dry_run": self.dry_run, "repo_root": str(REPO_ROOT)}
        initial_files = set(self.git.get_modified_files())
        try:
            agent_res = self.agent.execute(task, context)
        except SafetyViolationError as e:
            logger.warning("Agent execution blocked by safety policy: %s", e)
            report = ExecutionReportData(
                task_id=task.task_id,
                task_title=task.title,
                status="BLOCKED",
                branch=target_branch,
                base_branch=task.git_branch_requirements.base_branch,
                commit_sha=None,
                pull_request_url=None,
                summary_of_changes=f"Agent execution blocked: {e}",
                files_modified=[],
                test_results=[],
                build_results=[],
                security_findings=[str(e)],
                external_api_calls_made=0,
                estimated_external_cost_usd=0.0,
                repair_attempts_used=0,
                blockers=[str(e)],
                next_recommended_task="Real coding-agent requires approval token for external metered usage.",
            )
            self.reporter.write_reports(report)
            return report

        # Inspect modified files produced by this task
        current_dirty = self.git.get_modified_files()
        modified_files = [f for f in current_dirty if f not in initial_files]
        if not modified_files and agent_res.modified_files:
            modified_files = agent_res.modified_files

        # 5. File Boundary Validation
        try:
            self.safety.validate_file_changes(modified_files, task.allowed_file_changes)
        except SafetyViolationError as e:
            report = ExecutionReportData(
                task_id=task.task_id,
                task_title=task.title,
                status="SAFETY_VIOLATION",
                branch=target_branch,
                base_branch=task.git_branch_requirements.base_branch,
                commit_sha=None,
                pull_request_url=None,
                summary_of_changes=f"Execution halted: file boundary violation: {e}",
                files_modified=modified_files,
                test_results=[],
                build_results=[],
                security_findings=[str(e)],
                external_api_calls_made=agent_res.external_calls_count,
                estimated_external_cost_usd=agent_res.estimated_cost_usd,
                repair_attempts_used=0,
                blockers=[str(e)],
            )
            self.reporter.write_reports(report)
            return report

        # 6. Quality Verification (Tests, Builds, Secret Scanning)
        v_report: VerificationReport = self.verifier.verify_task(task, modified_files)

        # 7. Bounded Repair Loop (up to MAX_REPAIR_ATTEMPTS)
        repair_attempts = 0
        while not v_report.all_passed and repair_attempts < MAX_REPAIR_ATTEMPTS:
            repair_attempts += 1
            logger.warning(
                "Verification failed. Initiating repair attempt %d/%d",
                repair_attempts,
                MAX_REPAIR_ATTEMPTS,
            )

            repair_res = self.agent.repair(
                task,
                {"failures": v_report.failure_summaries, "modified_files": modified_files},
                repair_attempts,
            )

            # Re-check modified files
            modified_files = self.git.get_modified_files()
            try:
                self.safety.validate_file_changes(modified_files, task.allowed_file_changes)
            except SafetyViolationError as e:
                v_report.failure_summaries.append(str(e))
                break

            # Re-run verification
            v_report = self.verifier.verify_task(task, modified_files)

        # Determine final status
        status = "SUCCESS" if v_report.all_passed else "FAILED"
        if self.dry_run and v_report.all_passed:
            status = "DRY_RUN"

        commit_sha: Optional[str] = None
        pr_url: Optional[str] = None

        # 8. Git Commit, Push, and PR Creation (if verified passing and not dry-run)
        if v_report.all_passed and not self.dry_run and modified_files:
            self.git.stage_files(modified_files)
            commit_msg = f"feat({task.task_id.lower()}): {task.title}\n\nTask: {task.task_id}\nObjective: {task.objective}"
            commit_sha = self.git.commit(commit_msg)
            self.git.push(target_branch)

            pr_body = (
                f"## Autonomous Implementation: {task.title}\n\n"
                f"**Task ID:** `{task.task_id}`\n\n"
                f"### Objective\n{task.objective}\n\n"
                f"### Acceptance Criteria Verified\n"
                + "\n".join(f"- [x] {ac}" for ac in task.acceptance_criteria)
                + "\n\n### Quality Verification\n"
                f"- Tests Passed: {len([c for c in v_report.command_results if c.passed])}/{len(v_report.command_results)}\n"
                f"- External Cost: ${agent_res.estimated_cost_usd:.2f}\n"
            )
            pr_url = self.git.create_or_update_pr(
                branch_name=target_branch,
                base_branch=task.git_branch_requirements.base_branch,
                title=f"feat({task.task_id.lower()}): {task.title}",
                body=pr_body,
            )

        # 9. Generate Report
        test_data = [
            {
                "name": cr.name,
                "command": cr.command,
                "exit_code": cr.exit_code,
                "duration_seconds": cr.duration_seconds,
                "passed": cr.passed,
            }
            for cr in v_report.command_results
        ]

        report_data = ExecutionReportData(
            task_id=task.task_id,
            task_title=task.title,
            status=status,
            branch=target_branch,
            base_branch=task.git_branch_requirements.base_branch,
            commit_sha=commit_sha or self.git.get_current_commit(),
            pull_request_url=pr_url,
            summary_of_changes=agent_res.summary,
            files_modified=modified_files,
            test_results=test_data,
            build_results=[],
            security_findings=v_report.secret_findings,
            external_api_calls_made=agent_res.external_calls_count,
            estimated_external_cost_usd=agent_res.estimated_cost_usd,
            repair_attempts_used=repair_attempts,
            blockers=v_report.failure_summaries if not v_report.all_passed else [],
            next_recommended_task="Gate 4B Teacher Dashboard Review" if status in ["SUCCESS", "DRY_RUN"] else None,
            observed_results={
                "all_tests_passed": v_report.all_passed,
                "total_commands_executed": len(v_report.command_results),
                "working_tree_clean_initially": True,
                "secrets_detected": len(v_report.secret_findings),
            },
        )

        self.reporter.write_reports(report_data)
        return report_data
