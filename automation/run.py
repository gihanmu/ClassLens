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
from automation.runner.task_queue import QueueLockError, TaskQueue


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
        "--queue",
        "-q",
        nargs="+",
        help="Execute a sequence of tasks in queue mode (e.g. --queue TASK-GATE-4B TASK-GATE-4C)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display current persistent queue state and task progress",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Recover any tasks interrupted during previous runs",
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

    # Handle status query
    if args.status:
        queue = TaskQueue(task_parser=task_parser)
        state = queue.load_state()
        print("\nClassLens Autonomous Task Queue State:")
        print("---------------------------------------")
        if not state:
            print("No tasks registered in queue state.")
        else:
            for tid, entry in sorted(state.items()):
                pr_str = f" | PR: {entry.pr_url}" if entry.pr_url else ""
                err_str = f" | Error: {entry.error_message}" if entry.error_message else ""
                print(f"• {entry.task_id:<22} [{entry.state:<14}] Attempts: {entry.attempts}/{entry.max_attempts}{pr_str}{err_str}")
        print()
        return 0

    # Handle queue recovery
    if args.recover:
        queue = TaskQueue(task_parser=task_parser)
        print("\nRecovering interrupted tasks in queue...")
        with queue:
            queue.recover_interrupted_tasks()
        print("Recovery complete.\n")
        return 0

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

    # Queue execution
    if args.queue:
        queue = TaskQueue(task_parser=task_parser, orchestrator=orchestrator)
        print(f"\n🚀 Launching ClassLens Task Queue: {', '.join(args.queue)}")
        print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE AUTOMATION'}")
        print(f"   Runner: {args.runner.upper()}")
        print("-" * 60)
        try:
            results = queue.run_queue(args.queue)
            all_complete = all(entry.state == "COMPLETE" for entry in results.values())
            print("-" * 60)
            print("Queue Execution Finished:")
            for tid, entry in results.items():
                print(f"• {tid}: {entry.state}")
            return 0 if all_complete else 1
        except QueueLockError as e:
            print(f"\n🛑 QUEUE LOCK ERROR: {e}", file=sys.stderr)
            return 3
        except Exception as e:
            print(f"\n💥 UNEXPECTED QUEUE FAILURE: {e}", file=sys.stderr)
            return 1

    # Single task execution
    if not args.task:
        parser.print_help()
        return 1

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
        print(f"\n💥 UNEXPECTED RUNNER FAILURE: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
