"""macOS Worker Isolation and Process Sandboxing for ClassLens Autonomous Development.

Implements kernel-level mandatory access control via macOS Seatbelt (sandbox-exec),
strict environment sanitization, process group timeouts, and filesystem permission locks.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from automation.runner.config import (
    REPO_ROOT,
)

logger = logging.getLogger("ClassLensIsolation")


# Paths sensitive to host security that untrusted processes must NEVER read
DEFAULT_ISOLATED_PATHS: List[str] = [
    str(Path.home() / ".ssh"),
    str(Path.home() / ".config" / "gcloud"),
    str(Path.home() / ".aws"),
    str(Path.home() / "Library" / "Keychains"),
    str(Path.home() / "Library" / "Application Support" / "Google" / "Chrome"),
    str(Path.home() / ".gnupg"),
]

# Sensitive environment variables scrubbed from child processes
ENV_VARS_TO_SCRUB: List[str] = [
    "SSH_AUTH_SOCK",
    "SSH_AGENT_PID",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "CLOUDSDK_AUTH_ACCESS_TOKEN",
    "GCLOUD_PROJECT",
    "GOOGLE_CLOUD_PROJECT",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "CLASSLENS_APPROVAL_SECRET",
]


class WorkerIsolation:
    """Manages secure process execution, environment scrubbing, and OS sandboxing."""

    def __init__(
        self,
        repo_root: Path = REPO_ROOT,
        isolated_paths: Optional[List[str]] = None,
        enable_seatbelt: bool = True,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.isolated_paths = isolated_paths or [p for p in DEFAULT_ISOLATED_PATHS if Path(p).exists() or True]
        self.enable_seatbelt = enable_seatbelt and platform.system() == "Darwin"
        self._seatbelt_available = self._check_seatbelt()

    def _check_seatbelt(self) -> bool:
        """Check if sandbox-exec is available on Darwin."""
        if platform.system() != "Darwin":
            return False
        return shutil.which("sandbox-exec") is not None

    @property
    def is_seatbelt_available(self) -> bool:
        return self._seatbelt_available

    def generate_seatbelt_profile(
        self,
        workspace_dir: Path,
        allow_network: bool = True,
        protect_orchestrator: bool = True,
    ) -> str:
        """Generate a macOS Seatbelt (sandbox-exec Scheme) profile definition.

        Enforces:
        - Deny read to ~/.ssh, ~/.config/gcloud, ~/.aws, Keychains
        - Deny write to automation/runner, .github, automation/approvals
        - Deny network outbound if allow_network is False
        - Allow normal execution in repo workspace and standard system paths (/usr, /bin, /Library)
        """
        profile_lines = [
            "(version 1)",
            "(allow default)",
        ]

        # 1. Deny reading host secret directories
        for path in self.isolated_paths:
            escaped = path.replace('"', '\\"')
            profile_lines.append(f'(deny file-read* (subpath "{escaped}"))')

        # 2. Protect trusted orchestrator and CI directories from agent modification
        if protect_orchestrator:
            protected_subpaths = [
                str(self.repo_root / "automation" / "runner"),
                str(self.repo_root / "automation" / "approvals"),
                str(self.repo_root / ".github"),
                str(self.repo_root / ".git" / "hooks"),
            ]
            for p in protected_subpaths:
                escaped = p.replace('"', '\\"')
                profile_lines.append(f'(deny file-write* (subpath "{escaped}"))')

        # 3. Enforce network boundary
        if not allow_network:
            profile_lines.append("(deny network-outbound)")
            profile_lines.append("(deny network-inbound)")

        return "\n".join(profile_lines) + "\n"

    def sanitize_environment(
        self,
        extra_env: Optional[Dict[str, str]] = None,
        mock_mode_forced: bool = True,
    ) -> Dict[str, str]:
        """Construct a sanitized environment for subprocess execution.

        Strips all cloud credentials, SSH agent keys, and API tokens.
        Forces CLASSLENS_AI_MODE=mock.
        """
        env = os.environ.copy()

        # Remove sensitive variables
        for var in ENV_VARS_TO_SCRUB:
            env.pop(var, None)

        # Explicitly neutralize Google ADC
        env["GOOGLE_APPLICATION_CREDENTIALS"] = "/dev/null"

        # Force mock mode and safe offline flags
        if mock_mode_forced:
            env["CLASSLENS_AI_MODE"] = "mock"
            env["CLASSLENS_LIVE_INFERENCE_ENABLED"] = "false"
            env["CLASSLENS_MAX_LIVE_CALLS"] = "0"
            env["GOOGLE_GENAI_USE_VERTEXAI"] = "false"

        # Apply any task-specific overrides
        if extra_env:
            for k, v in extra_env.items():
                if k not in ENV_VARS_TO_SCRUB:
                    env[k] = v

        return env

    def run_isolated_command(
        self,
        command: List[str],
        cwd: Path,
        timeout_seconds: int = 120,
        allow_network: bool = True,
        protect_orchestrator: bool = True,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str, str]:
        """Execute a command in an isolated environment with seatbelt and sanitized env.

        Returns (returncode, stdout, stderr).
        """
        sanitized_env = self.sanitize_environment(extra_env=extra_env)

        exec_cmd = command
        temp_profile_file: Optional[Path] = None

        if self.enable_seatbelt and self._seatbelt_available:
            profile_content = self.generate_seatbelt_profile(
                workspace_dir=cwd,
                allow_network=allow_network,
                protect_orchestrator=protect_orchestrator,
            )
            # Write profile to a temp file
            with tempfile.NamedTemporaryFile("w", suffix=".sb", delete=False) as f:
                f.write(profile_content)
                temp_profile_file = Path(f.name)

            exec_cmd = ["sandbox-exec", "-f", str(temp_profile_file)] + command

        try:
            # Spawn in dedicated process group so timeouts kill entire child tree
            proc = subprocess.Popen(
                exec_cmd,
                cwd=str(cwd),
                env=sanitized_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )

            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
                return proc.returncode, stdout, stderr
            except subprocess.TimeoutExpired:
                logger.warning("Process timed out after %ds. Terminating process group...", timeout_seconds)
                if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    proc.kill()
                stdout, stderr = proc.communicate()
                return -1, stdout, stderr + f"\n[Process killed: timed out after {timeout_seconds}s]"

        finally:
            if temp_profile_file and temp_profile_file.exists():
                try:
                    temp_profile_file.unlink()
                except OSError:
                    pass

    def protect_filesystem_paths(self, make_read_only: bool) -> None:
        """Temporarily modify filesystem permissions on trusted directories."""
        trusted_dirs = [
            self.repo_root / "automation" / "runner",
            self.repo_root / "automation" / "approvals",
            self.repo_root / ".github",
        ]
        for d in trusted_dirs:
            if d.exists():
                for root, dirs, files in os.walk(d):
                    for item in dirs + files:
                        target = Path(root) / item
                        try:
                            if make_read_only:
                                # Remove write permission for all
                                current_mode = os.stat(target).st_mode
                                os.chmod(target, current_mode & ~0o222)
                            else:
                                # Restore owner write permission
                                current_mode = os.stat(target).st_mode
                                os.chmod(target, current_mode | 0o200)
                        except OSError as e:
                            logger.debug("Could not modify permissions for %s: %e", target, e)
