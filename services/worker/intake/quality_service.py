"""ImageQualityService: Main coordinator for binary intake, validation, sanitization, and quality scoring."""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Tuple
from PIL import Image

from services.worker.intake.contracts import (
    IntakeConfig,
    IntakeValidationResult,
    QualityStatus,
)
from services.worker.intake.metrics import (
    assess_quality_status,
    compute_laplacian_sharpness,
    compute_rms_contrast,
)
from services.worker.intake.sanitizer import sanitize_and_normalize_image
from services.worker.intake.validator import (
    compute_sha256,
    validate_image_payload,
)


class ImageQualityService:
    """Service coordinating deterministic quarantine validation, EXIF sanitization, and quality checks."""

    @classmethod
    def process_image_bytes(
        cls,
        raw_bytes: bytes,
        config: Optional[IntakeConfig] = None,
    ) -> Tuple[IntakeValidationResult, Optional[bytes]]:
        """Validates, sanitizes, and assesses an image from raw memory bytes.

        Guarantees:
        - Original payload is never modified.
        - Decompression bombs and malicious payloads are caught and rejected.
        - EXIF metadata is stripped from the returned sanitized copy.
        - Proportional dimension downscaling preserves fine pencil marks.
        - Sharpness and contrast indicators are accurately recorded.

        Args:
            raw_bytes: Raw binary payload.
            config: Optional intake configuration thresholds.

        Returns:
            Tuple of (IntakeValidationResult, sanitized_bytes_or_none).
        """
        cfg = config or IntakeConfig()
        sha256 = compute_sha256(raw_bytes)
        raw_len = len(raw_bytes)

        # 1. Quarantine validation pass (MIME, size, decompression bomb, raster load)
        is_valid, detected_mime, err_msg, raw_dims = validate_image_payload(
            raw_bytes, cfg
        )

        if not is_valid:
            result = IntakeValidationResult(
                is_valid=False,
                quality_status=QualityStatus.UNREADABLE,
                mime_type=detected_mime or "application/octet-stream",
                original_dimensions=raw_dims,
                normalized_dimensions=(0, 0),
                original_size_bytes=raw_len,
                sanitized_size_bytes=0,
                sha256_hash=sha256,
                sharpness_score=0.0,
                contrast_score=0.0,
                needs_teacher_review=True,
                error_message=err_msg,
                quarantine_action="reject_to_quarantine",
            )
            return result, None

        # 2. Quality assessment on decoded image
        try:
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                sharpness = compute_laplacian_sharpness(pil_img)
                contrast, mean_lum = compute_rms_contrast(pil_img)
                quality_status, needs_review, quality_notes = assess_quality_status(
                    sharpness, contrast, mean_lum, cfg
                )
        except Exception as metric_err:
            sharpness = 0.0
            contrast = 0.0
            quality_status = QualityStatus.UNREADABLE
            needs_review = True
            quality_notes = f"Failed to compute quality metrics: {metric_err}"

        # 3. Privacy sanitization & high-fidelity normalization
        sanitized_bytes, orig_dims, norm_dims = sanitize_and_normalize_image(
            raw_bytes=raw_bytes,
            detected_mime=detected_mime or "image/jpeg",
            config=cfg,
        )

        result = IntakeValidationResult(
            is_valid=True,
            quality_status=quality_status,
            mime_type=detected_mime or "image/jpeg",
            original_dimensions=orig_dims,
            normalized_dimensions=norm_dims,
            original_size_bytes=raw_len,
            sanitized_size_bytes=len(sanitized_bytes),
            sha256_hash=sha256,
            sharpness_score=sharpness,
            contrast_score=contrast,
            needs_teacher_review=needs_review,
            error_message=None if not needs_review else quality_notes,
            quarantine_action="promote_to_validated",
        )

        return result, sanitized_bytes

    @classmethod
    def process_image_file(
        cls,
        source_path: str,
        output_path: Optional[str] = None,
        config: Optional[IntakeConfig] = None,
    ) -> Tuple[IntakeValidationResult, Optional[str]]:
        """Processes an image file from disk without modifying the source file.

        Args:
            source_path: Path to source file in quarantine or uploads directory.
            output_path: Optional destination path to store sanitized copy.
            config: Optional intake configuration thresholds.

        Returns:
            Tuple of (IntakeValidationResult, sanitized_file_path_or_none).
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source image file not found: {source_path}")

        with open(source_path, "rb") as f:
            raw_bytes = f.read()

        result, sanitized_bytes = cls.process_image_bytes(raw_bytes, config)

        if not result.is_valid or sanitized_bytes is None:
            return result, None

        # Write sanitized output to destination or secure temporary file
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(sanitized_bytes)
            dest_file = output_path
        else:
            ext = ".png" if result.mime_type == "image/png" else ".jpg"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                tf.write(sanitized_bytes)
                dest_file = tf.name

        return result, dest_file
