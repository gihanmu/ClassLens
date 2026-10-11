"""Configuration settings for ClassLens FastAPI backend."""

from __future__ import annotations

import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application configuration with local development defaults."""

    app_name: str = "ClassLens API"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")
    mock_llm: bool = Field(default=True)
    queue_type: str = Field(default="inline")  # "inline" or "cloud_tasks"
    secret_key: str = Field(default="classlens-dev-secret-key-32-chars-long!")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    default_org_id: str = "org_cedar_sec"
    demo_user_id: str = "usr_sarah_lim"
    demo_user_name: str = "Sarah Lim"
    demo_user_email: str = "sarah.lim@moe.edu.sg"
    demo_user_role: str = "teacher"


settings = Settings()
