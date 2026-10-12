"""Safe Git and GitHub integration for ClassLens autonomous development."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from automation.runner.config import REPO_ROOT


class GitError(Exception):
    """Raised when a Git operation fails."""
    pass


class GitOps:
    """Safe wrapper around Git and GitHub CLI (`gh`)."""

    def __init__(self, repo_root: Path = REPO_ROOT, dry_run: bool = False) -> None:
        self.repo_root = repo_root
        self.dry_run = dry_run

    def _run(self, cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a git or gh command."""
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if check and res.returncode != 0:
            raise GitError(f"Command failed ({' '.join(cmd)}):\n{res.stderr.strip()}")
        return res.returncode, res.stdout.strip(), res.stderr.strip()

    def get_current_branch(self) -> str:
        _, out, _ = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return out

    def get_current_commit(self) -> str:
        _, out, _ = self._run(["git", "rev-parse", "HEAD"])
        return out

    def is_working_tree_clean(self) -> bool:
        _, out, _ = self._run(["git", "status", "--porcelain"])
        return len(out.strip()) == 0

    def get_modified_files(self) -> List[str]:
        """Return list of modified or untracked files."""
        _, out, _ = self._run(["git", "status", "--porcelain"])
        files = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # e.g. "M path/to/file", "?? newfile"
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                files.append(parts[1])
        return files

    def create_feature_branch(self, branch_name: str, base_branch: str = "main") -> None:
        """Create and checkout a new branch from base branch."""
        if self.dry_run:
            return

        # Fetch latest base
        self._run(["git", "fetch", "origin", base_branch], check=False)

        # Check if branch exists
        code, _, _ = self._run(["git", "rev-parse", "--verify", branch_name], check=False)
        if code == 0:
            self._run(["git", "checkout", branch_name])
        else:
            self._run(["git", "checkout", "-b", branch_name, f"origin/{base_branch}"])

    def stage_files(self, files: List[str]) -> None:
        """Stage specified files."""
        if self.dry_run or not files:
            return
        cmd = ["git", "add"] + files
        self._run(cmd)

    def commit(self, message: str) -> str:
        """Commit staged changes."""
        if self.dry_run:
            return "dry-run-commit-sha"
        self._run(["git", "commit", "-m", message])
        return self.get_current_commit()

    def push(self, branch_name: str) -> None:
        """Push branch to remote origin."""
        if self.dry_run:
            return
        self._run(["git", "push", "-u", "origin", branch_name])

    def create_or_update_pr(
        self,
        branch_name: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> Optional[str]:
        """Create or update a GitHub Pull Request using gh CLI."""
        if self.dry_run:
            return "https://github.com/gihanmu/ClassLens/pull/dry-run"

        # Check if gh CLI exists
        code, _, _ = self._run(["which", "gh"], check=False)
        if code != 0:
            return None

        # Check if PR already exists
        check_code, out, _ = self._run(
            ["gh", "pr", "view", branch_name, "--json", "url", "-q", ".url"],
            check=False,
        )
        if check_code == 0 and out:
            # Update existing PR
            self._run(["gh", "pr", "edit", branch_name, "--title", title, "--body", body], check=False)
            return out

        # Create new PR
        pr_code, pr_out, _ = self._run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base_branch,
                "--head",
                branch_name,
                "--title",
                title,
                "--body",
                body,
            ],
            check=False,
        )
        if pr_code == 0:
            return pr_out.strip()
        return None
