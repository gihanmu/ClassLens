"""Typed data contracts for image intake, quarantine validation, and quality metrics."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field


class QualityStatus(str, Enum):
    """Categorization of image visual clarity for AI vision processing."""

    CLEAR = "clear"
    FAINT_READABLE = "faint_readable"
    BLURRED = "blurred"
    LOW_CONTRAST = "low_contrast"
    ROTATED = "rotated"
    UNREADABLE = "unreadable"


class IntakeConfig(BaseModel):
    """Security boundaries and thresholds for image intake."""

    max_file_size_bytes: int = Field(
        default=10 * 1024 * 1024, description="Strict 10 MB payload ceiling"
    )
    max_image_pixels: int = Field(
        default=16_000_000, description="16-million-pixel Pillow decompression bomb ceiling"
    )
    min_dimension_px: int = Field(
        default=300, description="Minimum acceptable pixel width or height"
    )
    max_dimension_px: int = Field(
        default=4096, description="Maximum acceptable pixel width or height before normalization"
    )
    max_normalized_dim_px: int = Field(
        default=768, description="Target bounding dimension for downstream multimodal vision"
    )
    min_sharpness_threshold: float = Field(
        default=80.0, description="Laplacian variance threshold for blur indication"
    )
    min_contrast_threshold: float = Field(
        default=15.0, description="Standard deviation pixel intensity threshold for contrast"
    )
    allowed_mime_types: Tuple[str, ...] = Field(
        default=("image/jpeg", "image/png", "image/webp"),
        description="Permitted image formats validated via magic bytes",
    )


class IntakeValidationResult(BaseModel):
    """Structured result of image quarantine inspection and sanitization."""

    is_valid: bool = Field(
        description="True if file is an authentic, non-malicious image within size limits"
    )
    quality_status: QualityStatus = Field(
        description="Pedagogical visual quality indicator"
    )
    mime_type: str = Field(
        description="Detected MIME type (image/jpeg, image/png, image/webp, or unverified)"
    )
    original_dimensions: Tuple[int, int] = Field(
        description="(width, height) of original raw image in pixels"
    )
    normalized_dimensions: Tuple[int, int] = Field(
        description="(width, height) of sanitized processing copy in pixels"
    )
    original_size_bytes: int = Field(
        description="Original payload size in bytes"
    )
    sanitized_size_bytes: int = Field(
        default=0, description="Sanitized processing copy size in bytes"
    )
    sha256_hash: str = Field(
        description="Cryptographic SHA-256 digest of original raw payload"
    )
    sharpness_score: float = Field(
        default=0.0, description="Laplacian variance sharpness indicator"
    )
    contrast_score: float = Field(
        default=0.0, description="RMS standard deviation contrast indicator"
    )
    needs_teacher_review: bool = Field(
        default=False, description="Flag indicating poor quality requiring educator inspection"
    )
    error_message: Optional[str] = Field(
        default=None, description="Detailed explanation if validation failed"
    )
    quarantine_action: Literal["promote_to_validated", "reject_to_quarantine"] = Field(
        description="Quarantine outcome: promote_to_validated or reject_to_quarantine"
    )
