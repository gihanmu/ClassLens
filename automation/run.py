#!/usr/bin/env python3
"""CLI entrypoint for ClassLens autonomous development workflow runner."""

import argparse
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from automation.runner.agent_runner import AgyCliAgentRunner, DeterministicAgentRunner
from automation.runner.config import TASKS_DIR
from automation.runner.orchestrator import AutonomousOrchestrator
from automation.runner.safety import SafetyEnforcer, SafetyViolationError
from automation.runner.task_parser import TaskParser


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClassLens Autonomous Development Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--task",
        "-t",
        type=str,
        help="Task identifier (e.g. TASK-000-DRY-RUN) or file path to task YAML",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run verification and report generation without creating Git branches or pushing",
    )
    parser.add_argument(
        "--runner",
        choices=["deterministic", "agy"],
        default="deterministic",
        help="Agent runner engine to use (agy requires approved external spend token)",
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List all task specifications available in automation/tasks/",
    )

    args = parser.parse_args()

    task_parser = TaskParser()
    safety_enforcer = SafetyEnforcer()

    if args.list_tasks:
        print("\nAvailable Tasks in automation/tasks/:")
        print("---------------------------------------")
        for f in sorted(TASKS_DIR.glob("*.yaml")):
            try:
                task = task_parser.load_task(f)
                ext = f" [External: ${task.cost_restrictions.max_cost_usd:.2f}]" if task.cost_restrictions.allow_external_inference else " [Offline: $0.00]"
                print(f"• {task.task_id:<25} {task.title}{ext}")
            except Exception as e:
                print(f"• {f.name:<25} (Error loading: {e})")
        print()
        return 0

    if not args.task:
        parser.print_help()
        return 1

    # Select agent runner
    if args.runner == "agy":
        agent_runner = AgyCliAgentRunner(safety_enforcer=safety_enforcer)
    else:
        agent_runner = DeterministicAgentRunner(dry_run=args.dry_run)

    orchestrator = AutonomousOrchestrator(
        task_parser=task_parser,
        safety_enforcer=safety_enforcer,
        agent_runner=agent_runner,
        dry_run=args.dry_run,
    )

    print(f"\n🚀 Launching ClassLens Autonomous Task: {args.task}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE AUTOMATION'}")
    print(f"   Runner: {args.runner.upper()}")
    print("-" * 60)

    try:
        report = orchestrator.run_task(args.task)
        print("-" * 60)
        print(f"Status: {report.status}")
        print(f"Summary: {report.summary_of_changes}")
        print(f"Tests Passed: {len([t for t in report.test_results if t.get('passed')])}/{len(report.test_results)}")
        print(f"External Spend: ${report.estimated_external_cost_usd:.2f}")
        print(f"Reports saved to automation/reports/")
        return 0 if report.status in ["SUCCESS", "DRY_RUN"] else 1
    except SafetyViolationError as e:
        print(f"\n🛑 SAFETY ENFORCEMENT HALT: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\n❌ UNHANDLED RUNNER ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
