"""Safety enforcement layer for ClassLens autonomous development workflow.

Enforces deny-by-default external spending controls, approval tokens,
file-boundary restrictions, and secret scanning independent of any coding agent.
"""

from __future__ import annotations

import datetime
import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.runner.config import (
    APPROVALS_DIR,
    DEFAULT_EXTERNAL_SPENDING_LIMIT_USD,
    PROTECTED_FILE_PATTERNS,
    REPO_ROOT,
    USER_APPROVAL_THRESHOLD_USD,
)


class SafetyViolationError(Exception):
    """Raised when an operation violates ClassLens safety, cost, or security policies."""
    pass


class SafetyEnforcer:
    """Independent policy enforcement engine for autonomous tasks."""

    def __init__(self, approvals_dir: Path = APPROVALS_DIR) -> None:
        self.approvals_dir = approvals_dir

    def validate_cost_authorization(self, cost_restrictions: Dict[str, Any]) -> None:
        """Validate whether the task's cost profile is authorized.

        Policy rules:
        - DEFAULT_EXTERNAL_SPENDING_LIMIT_USD is 0.00.
        - Any task requesting external inference or cost > 0.00 requires an explicit,
          unexpired approval token file.
        - The $0.50 threshold is NOT permission to spend automatically; it is the boundary
          above which high-level executive approval is required.
        """
        max_cost = float(cost_restrictions.get("max_cost_usd", 0.0))
        allow_external = bool(cost_restrictions.get("allow_external_inference", False))
        requires_cloud = bool(cost_restrictions.get("requires_cloud_provisioning", False))
        approval_token = cost_restrictions.get("approval_token")

        if requires_cloud:
            raise SafetyViolationError(
                "Task requests paid cloud provisioning or infrastructure mutation. "
                "Cloud infrastructure provisioning is strictly prohibited in autonomous workflows."
            )

        if not allow_external and max_cost == 0.0:
            # Fully offline, safe to proceed
            return

        # External spend requested: require valid approval token
        if not approval_token:
            raise SafetyViolationError(
                f"Task requests external inference (max_cost_usd=${max_cost:.2f}) "
                f"without an approval token. Autonomous default limit is ${DEFAULT_EXTERNAL_SPENDING_LIMIT_USD:.2f}. "
                "Explicit approval file in automation/approvals/ is required."
            )

        self._verify_approval_token(approval_token, max_cost)

    def _verify_approval_token(self, token_id: str, requested_cost: float) -> None:
        """Verify an approval token on disk."""
        token_file = self.approvals_dir / f"{token_id}.json"
        if not token_file.exists():
            raise SafetyViolationError(
                f"Approval token file '{token_file.name}' not found in {self.approvals_dir}. "
                "Operation denied."
            )

        try:
            with open(token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise SafetyViolationError(f"Failed to read approval token file: {e}") from e

        required_fields = ["provider", "purpose", "max_authorized_calls", "authorized_cost_usd", "expires_at", "approved_by"]
        for field in required_fields:
            if field not in data:
                raise SafetyViolationError(f"Approval token missing required field '{field}'.")

        # Check expiration
        expires_at_str = data["expires_at"]
        try:
            expires_at = datetime.datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            if now > expires_at:
                raise SafetyViolationError(
                    f"Approval token '{token_id}' expired at {expires_at_str}. Operation denied."
                )
        except ValueError as e:
            raise SafetyViolationError(f"Invalid expires_at timestamp in approval token: {e}") from e

        authorized_cost = float(data["authorized_cost_usd"])
        if requested_cost > authorized_cost:
            raise SafetyViolationError(
                f"Requested cost (${requested_cost:.2f}) exceeds authorized cost (${authorized_cost:.2f}) "
                f"in token '{token_id}'."
            )

    def validate_file_changes(self, modified_files: List[str], allowed_patterns: List[str]) -> None:
        """Ensure modified files strictly adhere to allowed patterns and never touch protected files."""
        for file_path in modified_files:
            # Normalize path relative to REPO_ROOT
            norm_path = os.path.normpath(file_path)
            if norm_path.startswith("./"):
                norm_path = norm_path[2:]
            norm_path = norm_path.lstrip("/")

            # 1. Check against protected files
            for protected in PROTECTED_FILE_PATTERNS:
                if fnmatch.fnmatch(norm_path, protected) or fnmatch.fnmatch(os.path.basename(norm_path), protected):
                    raise SafetyViolationError(
                        f"Modification to protected file '{norm_path}' is prohibited by safety policy."
                    )

            # 2. Check against task allowed patterns
            is_allowed = False
            for pattern in allowed_patterns:
                clean_pattern = os.path.normpath(pattern)
                if clean_pattern.startswith("./"):
                    clean_pattern = clean_pattern[2:]
                clean_pattern = clean_pattern.lstrip("/")
                if fnmatch.fnmatch(norm_path, clean_pattern) or norm_path.startswith(clean_pattern.rstrip("*")):
                    is_allowed = True
                    break

            if not is_allowed:
                raise SafetyViolationError(
                    f"File '{norm_path}' is outside the task's allowed_file_changes scope."
                )

    def scan_for_secrets(self, file_paths: List[Path]) -> List[str]:
        """Scan a set of files for leaked secrets or credential patterns."""
        findings: List[str] = []

        patterns = [
            (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
            (r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----", "Private Key"),
            (r"ghp_[0-9A-Za-z]{36}", "GitHub Personal Access Token"),
            (r"gho_[0-9A-Za-z]{36}", "GitHub OAuth Token"),
            (r"\"type\": \"service_account\"", "Google Service Account JSON"),
            (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token"),
        ]

        for path in file_paths:
            if not path.exists() or not path.is_file():
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for regex, label in patterns:
                    if re.search(regex, content):
                        findings.append(f"Potential {label} detected in {path.relative_to(REPO_ROOT)}")
            except Exception as e:
                findings.append(f"Could not scan {path}: {e}")

        return findings
