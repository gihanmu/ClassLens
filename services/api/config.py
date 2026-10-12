"""Configuration settings for ClassLens FastAPI backend and multi-agent AI execution."""

from __future__ import annotations

import os
from typing import List, Optional
from pydantic import BaseModel, Field


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
    demo_user_name: str = "Sarah Lim"
    demo_user_email: str = "sarah.lim@moe.edu.sg"
    demo_user_role: str = "teacher"

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
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("CLASSLENS_GEMINI_MODEL", "gemini-3.8-flash")
    )
    max_live_calls: int = Field(
        default_factory=lambda: int(os.getenv("CLASSLENS_MAX_LIVE_CALLS", "3"))
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

    def validate_live_configuration(self) -> None:
        """Validates configuration when live mode is active.

        Raises ConfigurationError if prerequisites are missing.
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


settings = Settings()
