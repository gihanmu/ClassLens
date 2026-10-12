"""Automated unit tests verifying .env configuration loading, precedence, and mock safety.

Validates:
- Reliable loading of project-root .env file via python-dotenv.
- Resolution regardless of process starting working directory.
- Process environment variable precedence (exported variables override .env).
- Safe offline mock mode defaults.
- Gitignore enforcement ensuring .env is never tracked or committed.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from services.api.config import (
    DEFAULT_DOTENV_PATH,
    PROJECT_ROOT,
    Settings,
    load_project_env,
    reload_settings,
)


class TestDotenvConfiguration:
    """Tests for project-level .env loading and process-environment precedence."""

    def test_default_dotenv_path_points_to_project_root(self):
        """DEFAULT_DOTENV_PATH must always resolve to .env at the repository root."""
        assert DEFAULT_DOTENV_PATH == PROJECT_ROOT / ".env"
        assert PROJECT_ROOT.is_dir()
        assert (PROJECT_ROOT / "pyproject.toml").is_file()

    def test_env_file_loads_successfully_with_configured_values(self):
        """Verifies that .env is loaded and populates Settings with configured values."""
        assert DEFAULT_DOTENV_PATH.is_file(), "Root .env file must exist for local development"

        loaded = load_project_env(DEFAULT_DOTENV_PATH, override=False)
        assert loaded is True

        s = Settings()
        # Verify required configuration values from .env
        assert s.ai_mode == "mock"
        assert s.live_inference_enabled is False
        assert s.max_live_calls == 3
        assert s.google_cloud_project == "precise-equator-511303-m1"
        assert s.google_cloud_location == "global"
        assert s.google_genai_use_vertexai is True
        assert s.gemini_model == "gemini-3.8-flash"
        assert s.mock_llm is True

        # Safety gate: Live mode must be False
        assert s.is_live_mode() is False

    def test_process_environment_variable_precedence(self, monkeypatch):
        """Explicit process environment variables must override values from .env."""
        # Simulate explicitly exported shell variables
        monkeypatch.setenv("CLASSLENS_MAX_LIVE_CALLS", "9")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        monkeypatch.setenv("CLASSLENS_GEMINI_MODEL", "gemini-2.5-flash")

        # Reload with override=False (the default behavior)
        load_project_env(DEFAULT_DOTENV_PATH, override=False)

        s = Settings()
        assert s.max_live_calls == 9
        assert s.google_cloud_location == "us-central1"
        assert s.gemini_model == "gemini-2.5-flash"

    def test_load_dotenv_from_arbitrary_working_directory(self):
        """load_project_env must locate project-root .env regardless of cwd."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                os.chdir(tmp_dir)
                # Calling load_project_env without arguments from a foreign cwd
                loaded = load_project_env()
                assert loaded is True
                s = Settings()
                assert s.google_cloud_project == "precise-equator-511303-m1"
            finally:
                os.chdir(original_cwd)

    def test_safe_mock_defaults_when_env_file_missing(self, monkeypatch):
        """When .env does not exist and no env vars are set, defaults must enforce safe mock mode."""
        # Clear ClassLens env vars
        vars_to_clear = [
            "CLASSLENS_AI_MODE",
            "CLASSLENS_LIVE_INFERENCE_ENABLED",
            "CLASSLENS_MAX_LIVE_CALLS",
            "MOCK_LLM",
        ]
        for v in vars_to_clear:
            monkeypatch.delenv(v, raising=False)

        missing_path = Path("/tmp/nonexistent_classlens_env_file_path/.env")
        loaded = load_project_env(missing_path)
        assert loaded is False

        s = Settings()
        assert s.ai_mode == "mock"
        assert s.live_inference_enabled is False
        assert s.is_live_mode() is False

    def test_reload_settings_helper(self, monkeypatch):
        """reload_settings() refreshes the global settings singleton."""
        monkeypatch.setenv("CLASSLENS_MAX_LIVE_CALLS", "7")
        fresh = reload_settings()
        assert fresh.max_live_calls == 7

    def test_git_ignores_env_file(self):
        """Git must ignore .env and allow .env.example."""
        res_env = subprocess.run(
            ["git", "check-ignore", "-v", ".env"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert res_env.returncode == 0, ".env must be ignored by git"
        assert ".gitignore" in res_env.stdout

        res_example = subprocess.run(
            ["git", "check-ignore", "-v", ".env.example"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert res_example.returncode != 0, ".env.example must NOT be ignored by git"
