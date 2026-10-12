"""Task specification parser and validator for ClassLens autonomous development."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

from automation.runner.config import SCHEMA_PATH, TASKS_DIR


@dataclass
class TestCommand:
    __test__ = False
    name: str
    command: str
    working_directory: str = "."
    timeout_seconds: int = 120


@dataclass
class CostRestrictions:
    max_cost_usd: float = 0.0
    allow_external_inference: bool = False
    requires_cloud_provisioning: bool = False
    approval_token: Optional[str] = None


@dataclass
class SecurityRestrictions:
    allow_real_student_data: bool = False
    allow_secret_access: bool = False
    allow_production_mutation: bool = False
    prohibited_patterns: List[str] = field(default_factory=list)


@dataclass
class GitBranchRequirements:
    base_branch: str = "main"
    target_branch_pattern: str = "feature/auto-*"


@dataclass
class Scope:
    included: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)


@dataclass
class TaskSpec:
    task_id: str
    title: str
    objective: str
    scope: Scope
    acceptance_criteria: List[str]
    dependencies: List[str]
    allowed_file_changes: List[str]
    test_commands: List[TestCommand]
    cost_restrictions: CostRestrictions
    security_restrictions: SecurityRestrictions
    git_branch_requirements: GitBranchRequirements
    completion_criteria: List[str]
    raw_data: Dict[str, Any] = field(default_factory=dict)


class TaskParser:
    """Loads and validates ClassLens task specifications."""

    def __init__(self, schema_path: Path = SCHEMA_PATH) -> None:
        self.schema_path = schema_path
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def load_task(self, file_path: Path) -> TaskSpec:
        """Load and validate a task file from path."""
        if not file_path.exists():
            raise FileNotFoundError(f"Task file '{file_path}' does not exist.")

        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        # Validate against schema
        jsonschema.validate(instance=data, schema=self.schema)

        # Build dataclass
        test_cmds = [
            TestCommand(
                name=c["name"],
                command=c["command"],
                working_directory=c.get("working_directory", "."),
                timeout_seconds=c.get("timeout_seconds", 120),
            )
            for c in data["test_commands"]
        ]

        cost = CostRestrictions(
            max_cost_usd=float(data["cost_restrictions"].get("max_cost_usd", 0.0)),
            allow_external_inference=bool(data["cost_restrictions"].get("allow_external_inference", False)),
            requires_cloud_provisioning=bool(data["cost_restrictions"].get("requires_cloud_provisioning", False)),
            approval_token=data["cost_restrictions"].get("approval_token"),
        )

        sec = SecurityRestrictions(
            allow_real_student_data=bool(data["security_restrictions"].get("allow_real_student_data", False)),
            allow_secret_access=bool(data["security_restrictions"].get("allow_secret_access", False)),
            allow_production_mutation=bool(data["security_restrictions"].get("allow_production_mutation", False)),
            prohibited_patterns=data["security_restrictions"].get("prohibited_patterns", []),
        )

        git_req = GitBranchRequirements(
            base_branch=data["git_branch_requirements"].get("base_branch", "main"),
            target_branch_pattern=data["git_branch_requirements"].get("target_branch_pattern", "feature/auto-*"),
        )

        scope = Scope(
            included=data["scope"].get("included", []),
            excluded=data["scope"].get("excluded", []),
        )

        return TaskSpec(
            task_id=data["task_id"],
            title=data["title"],
            objective=data["objective"],
            scope=scope,
            acceptance_criteria=data["acceptance_criteria"],
            dependencies=data["dependencies"],
            allowed_file_changes=data["allowed_file_changes"],
            test_commands=test_cmds,
            cost_restrictions=cost,
            security_restrictions=sec,
            git_branch_requirements=git_req,
            completion_criteria=data["completion_criteria"],
            raw_data=data,
        )

    def find_task(self, task_id_or_path: str, search_dir: Path = TASKS_DIR) -> TaskSpec:
        """Find a task by filename or task_id."""
        candidate = Path(task_id_or_path)
        if candidate.exists():
            return self.load_task(candidate)

        # Search by file name in tasks_dir
        for ext in [".yaml", ".yml", ".json"]:
            path = search_dir / f"{task_id_or_path}{ext}"
            if path.exists():
                return self.load_task(path)

        # Search by task_id within files
        for f in search_dir.glob("*.yaml"):
            try:
                task = self.load_task(f)
                if task.task_id == task_id_or_path:
                    return task
            except Exception:
                continue

        raise FileNotFoundError(f"No task specification found matching '{task_id_or_path}' in {search_dir}.")
