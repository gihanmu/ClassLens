"""Configuration settings for ClassLens FastAPI backend and multi-agent AI execution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DOTENV_PATH = PROJECT_ROOT / ".env"


def load_project_env(
    env_path: Optional[Union[str, Path]] = None,
    override: bool = False,
) -> bool:
    """Loads environment variables from project-root .env file using python-dotenv.

    Preserves process-environment precedence:
    Explicitly exported environment variables (e.g. from shell or container)
    take precedence over .env file entries by default (override=False).

    Args:
        env_path: Optional explicit path to .env file (defaults to PROJECT_ROOT / ".env").
        override: If True, .env values overwrite existing process variables. Defaults to False.

    Returns:
        True if the file was found and loaded, False otherwise.
    """
    target = Path(env_path) if env_path else DEFAULT_DOTENV_PATH
    if target.is_file():
        load_dotenv(dotenv_path=target, override=override)
        return True
    return False


# Automatically load project .env on module import
load_project_env()


class ConfigurationError(ValueError):
    """Raised when application or AI execution configuration is invalid."""


class Settings(BaseModel):
    """Application configuration supporting explicit MOCK and LIVE AI execution modes."""

    app_name: str = "ClassLens API"
    app_version: str = "1.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    queue_type: str = Field(default_factory=lambda: os.getenv("QUEUE_TYPE", "inline"))
    secret_key: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "classlens-dev-secret-key-32-chars-long!")
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    default_org_id: str = "org_cedar_sec"
    demo_user_id: str = "usr_sarah_lim"
    demo_user_name: str = "Mrs. Sarah Lim"
    demo_user_email: str = "teacher@classlens.demo"
    demo_user_role: str = "Secondary 1 Mathematics Teacher"
    demo_user_school: str = "Cedar Secondary School"
    session_max_age_seconds: int = Field(
        default_factory=lambda: int(os.getenv("CLASSLENS_SESSION_MAX_AGE_SECONDS", "86400"))
    )

    # AI Execution Mode Configuration
    # MOCK (default): 100% offline, deterministic fixtures, zero network calls
    # LIVE: Google Cloud Vertex AI inference via Application Default Credentials
    ai_mode: str = Field(
        default_factory=lambda: os.getenv("CLASSLENS_AI_MODE", "mock").lower()
    )
    live_inference_enabled: bool = Field(
        default_factory=lambda: os.getenv("CLASSLENS_LIVE_INFERENCE_ENABLED", "false").lower()
        in ("true", "1", "yes")
    )

    # Google Cloud Vertex AI Settings
    google_cloud_project: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", "precise-equator-511303-m1")
    )
    google_cloud_location: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    )
    google_genai_use_vertexai: bool = Field(
        default_factory=lambda: os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower()
        in ("true", "1", "yes")
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv(
            "CLASSLENS_GEMINI_MODEL",
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        )
    )
    max_live_calls: int = Field(
        default_factory=lambda: int(os.getenv("CLASSLENS_MAX_LIVE_CALLS", "3"))
    )

    # Fail-closed owner authorization key (Gate 6)
    live_auth_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLASSLENS_LIVE_AUTH_KEY")
    )
    gemini_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("CLASSLENS_GEMINI_TIMEOUT_SECONDS", "30.0"))
    )
    max_image_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("CLASSLENS_MAX_IMAGE_SIZE_BYTES", str(10 * 1024 * 1024)))
    )
    gemini_max_output_tokens: int = Field(
        default_factory=lambda: int(os.getenv("CLASSLENS_GEMINI_MAX_OUTPUT_TOKENS", "4096"))
    )

    # Legacy compatibility flag
    mock_llm: bool = Field(
        default_factory=lambda: os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes")
    )

    def is_live_mode(self) -> bool:
        """Determines if live Gemini inference is explicitly enabled.

        Live execution requires BOTH:
        1. ai_mode == 'live'
        2. live_inference_enabled == True
        """
        if self.mock_llm and self.ai_mode != "live":
            return False
        return (self.ai_mode == "live") and (self.live_inference_enabled is True)

    def is_live_authorized(self, provided_key: Optional[str] = None) -> bool:
        """Determines if live Gemini inference is fully authorized by the owner.

        Fail-closed requirements (both must be satisfied):
        1. is_live_mode() is True (ai_mode == 'live' AND live_inference_enabled == True)
        2. A non-empty CLASSLENS_LIVE_AUTH_KEY is configured in the environment.
        3. If provided_key is passed, it must match live_auth_key using constant-time comparison.
        """
        import secrets

        if not self.is_live_mode():
            return False
        if not self.live_auth_key or not self.live_auth_key.strip():
            return False
        if provided_key is not None:
            return secrets.compare_digest(provided_key.strip(), self.live_auth_key.strip())
        return True

    def validate_live_configuration(
        self,
        provided_key: Optional[str] = None,
        require_owner_key: bool = False,
    ) -> None:
        """Validates configuration when live mode is active.

        Enforces fail-closed authorization:
        Raises ConfigurationError if prerequisites, credentials, or owner authorization key are missing.
        """
        if not self.is_live_mode():
            return

        if not self.google_cloud_project:
            raise ConfigurationError(
                "Live Gemini execution requires GOOGLE_CLOUD_PROJECT to be configured."
            )

        # Reconcile model with verified catalog
        verified_models = {
            "gemini-3.8-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-002",
        }
        if self.gemini_model not in verified_models:
            raise ConfigurationError(
                f"Configured model '{self.gemini_model}' is not in the verified Vertex AI model catalog. "
                f"Supported models: {sorted(verified_models)}"
            )

        if require_owner_key or provided_key is not None:
            self.validate_live_authorization(provided_key=provided_key)

    def validate_live_authorization(self, provided_key: Optional[str] = None) -> None:
        """Enforces that explicit owner authorization is present before invoking live inference.

        Raises ConfigurationError if live mode is disabled, owner authorization key is missing,
        or provided key does not match.
        """
        import secrets

        if not self.is_live_mode():
            raise ConfigurationError("Live Gemini mode is not enabled.")

        if not self.live_auth_key or not self.live_auth_key.strip():
            raise ConfigurationError(
                "Gate 6 Fail-Closed Safeguard: Live Gemini execution requires explicit owner authorization. "
                "Set CLASSLENS_LIVE_AUTH_KEY in the environment before enabling live inference."
            )

        if provided_key is not None:
            if not secrets.compare_digest(provided_key.strip(), self.live_auth_key.strip()):
                raise ConfigurationError(
                    "Gate 6 Fail-Closed Safeguard: Invalid owner authorization key provided."
                )


settings = Settings()


def reload_settings(env_path: Optional[Union[str, Path]] = None, override: bool = False) -> Settings:
    """Reloads project environment configuration and returns a fresh Settings instance."""
    global settings
    load_project_env(env_path=env_path, override=override)
    settings = Settings()
    return settings


def get_settings() -> Settings:
    """Returns the current application settings instance."""
    return settings
