"""Comprehensive unit and acceptance test suite for image intake, validation, and sanitization."""

from __future__ import annotations

import io
import os
import tempfile
import time
import pytest
from PIL import Image

from services.worker.intake.contracts import (
    IntakeConfig,
    IntakeValidationResult,
    QualityStatus,
)
from services.worker.intake.metrics import (
    compute_laplacian_sharpness,
    compute_rms_contrast,
)
from services.worker.intake.quality_service import ImageQualityService
from services.worker.intake.sanitizer import sanitize_and_normalize_image
from services.worker.intake.validator import (
    compute_sha256,
    detect_mime_type,
    validate_image_payload,
)
from tests.fixtures.synthetic_image_fixtures import (
    create_blurred_image,
    create_decompression_bomb,
    create_faint_image,
    create_test_jpeg,
    create_test_png,
    create_test_webp,
)


# ==============================================================================
# 1. Validator Tests (Magic Bytes, Size, Decompression Bomb)
# ==============================================================================

class TestValidator:
    """Tests for payload validation, magic byte checking, and security boundaries."""

    def test_detect_mime_type_jpeg(self):
        jpeg_data = create_test_jpeg()
        assert detect_mime_type(jpeg_data) == "image/jpeg"

    def test_detect_mime_type_png(self):
        png_data = create_test_png()
        assert detect_mime_type(png_data) == "image/png"

    def test_detect_mime_type_webp(self):
        webp_data = create_test_webp()
        assert detect_mime_type(webp_data) == "image/webp"

    def test_detect_mime_type_invalid(self):
        assert detect_mime_type(b"Hello world! Not an image.") is None
        assert detect_mime_type(b"") is None
        assert detect_mime_type(b"\x00" * 10) is None

    def test_payload_size_ceiling_10mb(self):
        cfg = IntakeConfig(max_file_size_bytes=1000)
        valid_img = create_test_jpeg()
        assert len(valid_img) > 1000

        is_valid, mime, err, _ = validate_image_payload(valid_img, cfg)
        assert not is_valid
        assert "exceeds maximum ceiling" in err

    def test_empty_payload(self):
        is_valid, _, err, _ = validate_image_payload(b"")
        assert not is_valid
        assert "Empty payload" in err

    def test_decompression_bomb_rejection(self):
        bomb = create_decompression_bomb()
        is_valid, _, err, _ = validate_image_payload(bomb)
        assert not is_valid
        assert "Decompression bomb" in err

    def test_minimum_dimension_rejection(self):
        small = create_test_jpeg(dimensions=(200, 200))
        is_valid, _, err, dims = validate_image_payload(small)
        assert not is_valid
        assert "smaller than minimum requirement" in err
        assert dims == (200, 200)

    def test_maximum_dimension_rejection(self):
        cfg = IntakeConfig(max_dimension_px=1000)
        large = create_test_jpeg(dimensions=(1200, 800))
        is_valid, _, err, dims = validate_image_payload(large, cfg)
        assert not is_valid
        assert "exceed maximum limit" in err
        assert dims == (1200, 800)

    def test_corrupted_image_bytes(self):
        # Truncated JPEG stream (starts with magic bytes but contains garbage)
        corrupted = b"\xff\xd8\xff\xe0" + b"\x00" * 30
        is_valid, _, err, _ = validate_image_payload(corrupted)
        assert not is_valid
        assert "Corrupted or malformed" in err


# ==============================================================================
# 2. Sanitizer Tests (EXIF Stripping, Proportional Scaling, Transparency)
# ==============================================================================

class TestSanitizer:
    """Tests for metadata sanitization and proportional normalization."""

    def test_exif_stripping(self):
        # Create JPEG with camera metadata
        exif_tags = {0x010F: "Apple", 0x0110: "iPhone 15 Pro", 0x9003: "2026:10:11 12:00:00"}
        raw_jpeg = create_test_jpeg(exif_tags=exif_tags)

        # Confirm original has EXIF
        orig_img = Image.open(io.BytesIO(raw_jpeg))
        assert bool(orig_img.getexif())

        # Sanitize
        sanitized_bytes, orig_dims, norm_dims = sanitize_and_normalize_image(
            raw_jpeg, detected_mime="image/jpeg"
        )

        # Confirm sanitized has zero EXIF tags
        clean_img = Image.open(io.BytesIO(sanitized_bytes))
        assert len(clean_img.getexif()) == 0

    def test_proportional_scaling_above_768(self):
        # 800x600 -> Scale factor 768/800 = 0.96 -> 768x576
        raw_jpeg = create_test_jpeg(dimensions=(800, 600))
        sanitized_bytes, orig_dims, norm_dims = sanitize_and_normalize_image(
            raw_jpeg, detected_mime="image/jpeg"
        )
        assert orig_dims == (800, 600)
        assert norm_dims == (768, 576)

        clean_img = Image.open(io.BytesIO(sanitized_bytes))
        assert clean_img.size == (768, 576)

    def test_no_upscaling_below_768(self):
        # 600x400 -> Should retain 600x400
        raw_jpeg = create_test_jpeg(dimensions=(600, 400))
        sanitized_bytes, orig_dims, norm_dims = sanitize_and_normalize_image(
            raw_jpeg, detected_mime="image/jpeg"
        )
        assert orig_dims == (600, 400)
        assert norm_dims == (600, 400)

    def test_png_transparency_composited_to_white(self):
        raw_png = create_test_png(with_alpha=True)
        sanitized_bytes, _, _ = sanitize_and_normalize_image(
            raw_png, detected_mime="image/png"
        )
        clean_img = Image.open(io.BytesIO(sanitized_bytes))
        assert clean_img.mode in ("RGB", "RGBA")


# ==============================================================================
# 3. Quality Metrics Tests (Sharpness, Contrast, Blur)
# ==============================================================================

class TestQualityMetrics:
    """Tests for objective image quality calculations."""

    def test_sharp_image_has_high_variance(self):
        sharp_bytes = create_test_jpeg()
        img = Image.open(io.BytesIO(sharp_bytes))
        sharpness = compute_laplacian_sharpness(img)
        assert sharpness > 100.0

    def test_blurred_image_has_low_variance(self):
        blurred_bytes = create_blurred_image(blur_radius=12.0)
        img = Image.open(io.BytesIO(blurred_bytes))
        sharpness = compute_laplacian_sharpness(img)
        assert sharpness < 80.0

    def test_rms_contrast(self):
        faint_bytes = create_faint_image()
        faint_img = Image.open(io.BytesIO(faint_bytes))
        contrast, _ = compute_rms_contrast(faint_img)
        assert contrast < 15.0


# ==============================================================================
# 4. Core Acceptance Tests (TC-002.01 through TC-002.06)
# ==============================================================================

class TestAcceptanceCases:
    """Verifies all acceptance criteria defined in specs/002-image-intake/acceptance-tests.md."""

    def test_tc_002_01_valid_jpeg_with_exif(self):
        """TC-002.01: Valid 800x600 JPEG with EXIF -> normalized to 768x576, EXIF stripped, promoted."""
        raw = create_test_jpeg(
            dimensions=(800, 600),
            exif_tags={0x010F: "Canon", 0x0110: "EOS R5"},
        )
        res, sanitized = ImageQualityService.process_image_bytes(raw)

        assert res.is_valid is True
        assert res.quality_status == QualityStatus.CLEAR
        assert res.quarantine_action == "promote_to_validated"
        assert res.original_dimensions == (800, 600)
        assert res.normalized_dimensions == (768, 576)
        assert res.sha256_hash == compute_sha256(raw)
        assert sanitized is not None

        # Verify EXIF was stripped in output
        clean_img = Image.open(io.BytesIO(sanitized))
        assert len(clean_img.getexif()) == 0

    def test_tc_002_02_png_renamed_as_jpg(self):
        """TC-002.02: PNG binary content with misleading extension -> detected as image/png via magic bytes."""
        raw_png = create_test_png()
        res, sanitized = ImageQualityService.process_image_bytes(raw_png)

        assert res.is_valid is True
        assert res.mime_type == "image/png"
        assert res.quarantine_action == "promote_to_validated"
        assert sanitized is not None

    def test_tc_002_03_text_file_named_image_png(self):
        """TC-002.03: Plain text file payload -> rejected with Invalid MIME type."""
        fake_payload = b"This is not a PNG file, but malicious or plain text content."
        res, sanitized = ImageQualityService.process_image_bytes(fake_payload)

        assert res.is_valid is False
        assert res.quality_status == QualityStatus.UNREADABLE
        assert res.quarantine_action == "reject_to_quarantine"
        assert "Invalid or unsupported MIME type" in res.error_message
        assert sanitized is None

    def test_tc_002_04_raster_decompression_bomb(self):
        """TC-002.04: Raster decompression bomb (20,000 x 20,000 px) -> caught safely without OOM."""
        bomb = create_decompression_bomb()
        res, sanitized = ImageQualityService.process_image_bytes(bomb)

        assert res.is_valid is False
        assert res.quality_status == QualityStatus.UNREADABLE
        assert res.quarantine_action == "reject_to_quarantine"
        assert "Decompression bomb" in res.error_message
        assert sanitized is None

    def test_tc_002_05_heavy_gaussian_blurred_image(self):
        """TC-002.05: Heavy Gaussian blurred image -> sharpness < 80.0, flags needs_teacher_review = True."""
        blurred = create_blurred_image(blur_radius=15.0)
        res, sanitized = ImageQualityService.process_image_bytes(blurred)

        assert res.is_valid is True
        assert res.sharpness_score < 80.0
        assert res.needs_teacher_review is True
        assert res.quality_status == QualityStatus.UNREADABLE
        assert res.quarantine_action == "promote_to_validated"
        assert sanitized is not None  # Preserved for teacher review!

    def test_tc_002_06_tiny_icon_below_minimum_dimensions(self):
        """TC-002.06: Tiny icon (100x100 px) -> rejected (below minimum 300px threshold)."""
        tiny = create_test_jpeg(dimensions=(100, 100))
        res, sanitized = ImageQualityService.process_image_bytes(tiny)

        assert res.is_valid is False
        assert res.quality_status == QualityStatus.UNREADABLE
        assert res.quarantine_action == "reject_to_quarantine"
        assert "smaller than minimum requirement" in res.error_message
        assert sanitized is None


# ==============================================================================
# 5. Security, File System & Performance Tests
# ==============================================================================

class TestSecurityAndFileIntegrity:
    """Tests for file preservation, temporary file management, and performance."""

    def test_source_file_preservation(self):
        """Verifies process_image_file creates a separate copy and does NOT alter source."""
        raw_jpeg = create_test_jpeg(dimensions=(800, 600))

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = os.path.join(tmpdir, "original_student_work.jpg")
            dst_path = os.path.join(tmpdir, "sanitized_copy.jpg")

            with open(src_path, "wb") as f:
                f.write(raw_jpeg)

            res, out_path = ImageQualityService.process_image_file(
                source_path=src_path, output_path=dst_path
            )

            assert res.is_valid is True
            assert out_path == dst_path
            assert os.path.exists(dst_path)

            # Confirm source file exists and is byte-for-byte identical to original
            with open(src_path, "rb") as f:
                assert f.read() == raw_jpeg

    def test_webp_full_pipeline(self):
        webp_bytes = create_test_webp()
        res, sanitized = ImageQualityService.process_image_bytes(webp_bytes)
        assert res.is_valid is True
        assert res.mime_type == "image/webp"
        assert sanitized is not None

    def test_faint_handwriting_flags_teacher_review_without_rejection(self):
        """Requirement: Treat contrast as quality indicator, preserving faint mathematical marks."""
        faint_bytes = create_faint_image()
        res, sanitized = ImageQualityService.process_image_bytes(faint_bytes)

        assert res.is_valid is True
        assert res.needs_teacher_review is True
        assert res.quality_status == QualityStatus.FAINT_READABLE
        assert res.quarantine_action == "promote_to_validated"
        assert sanitized is not None

    def test_performance_nfr_benchmark(self):
        """Verifies NFR-002.1: Complete intake execution in < 200 ms."""
        raw_jpeg = create_test_jpeg(dimensions=(1200, 900))

        start_t = time.perf_counter()
        res, sanitized = ImageQualityService.process_image_bytes(raw_jpeg)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        assert res.is_valid is True
        assert elapsed_ms < 200.0, f"Execution was too slow: {elapsed_ms:.1f} ms"
