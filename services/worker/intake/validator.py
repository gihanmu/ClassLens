"""Binary payload validation, magic byte verification, and decompression bomb protection."""

from __future__ import annotations

import hashlib
import io
import warnings
from typing import Optional, Tuple
from PIL import Image, UnidentifiedImageError

from services.worker.intake.contracts import IntakeConfig

try:
    import puremagic
except ImportError:
    puremagic = None


def detect_mime_type(data: bytes) -> Optional[str]:
    """Detects MIME type from raw bytes using magic numbers and file headers.

    Supports JPEG, PNG, and WebP. Rejects disguised non-image files.

    Args:
        data: Initial raw bytes of the file.

    Returns:
        MIME type string (e.g. 'image/jpeg', 'image/png', 'image/webp') or None if unrecognized.
    """
    if len(data) < 12:
        return None

    # 1. Exact binary header signatures (Fast path)
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"

    # 2. Supplementary check via puremagic if available
    if puremagic is not None:
        try:
            detected = puremagic.from_string(data[:2048], mime=True)
            if detected in ("image/jpeg", "image/png", "image/webp"):
                return detected
        except (puremagic.PureError, ValueError, Exception):
            pass

    return None


def compute_sha256(data: bytes) -> str:
    """Computes cryptographic SHA-256 hex digest of raw payload.

    Args:
        data: Binary payload.

    Returns:
        64-character lowercase hexadecimal hash.
    """
    return hashlib.sha256(data).hexdigest()


def validate_image_payload(
    data: bytes,
    config: Optional[IntakeConfig] = None,
) -> Tuple[bool, Optional[str], Optional[str], Tuple[int, int]]:
    """Validates raw image bytes for security, integrity, and dimension bounds.

    Enforces:
    1. Maximum payload file size (10 MB).
    2. Magic bytes header verification (JPEG, PNG, WebP only).
    3. Decompression bomb protection (Image.MAX_IMAGE_PIXELS = 16,000,000).
    4. Dimension boundaries (min 300px, max 4096px).
    5. Actual raster decode integrity verification.

    Args:
        data: Raw image payload bytes.
        config: Optional configuration thresholds.

    Returns:
        Tuple of (is_valid, detected_mime_type, error_message, (width, height))
    """
    cfg = config or IntakeConfig()

    # 1. Byte length ceiling check
    payload_len = len(data)
    if payload_len == 0:
        return False, None, "Empty payload provided (0 bytes)", (0, 0)

    if payload_len > cfg.max_file_size_bytes:
        return (
            False,
            None,
            f"Payload size ({payload_len} bytes) exceeds maximum ceiling of {cfg.max_file_size_bytes} bytes (10 MB)",
            (0, 0),
        )

    # 2. Magic byte verification
    mime_type = detect_mime_type(data)
    if not mime_type or mime_type not in cfg.allowed_mime_types:
        return (
            False,
            mime_type or "application/octet-stream",
            f"Invalid or unsupported MIME type: {mime_type or 'unknown'}. Allowed: {', '.join(cfg.allowed_mime_types)}",
            (0, 0),
        )

    # 3. Configure Pillow decompression bomb protection
    Image.MAX_IMAGE_PIXELS = cfg.max_image_pixels

    # Treat decompression bomb warnings as errors
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)

        try:
            # First pass: read header structure
            bio = io.BytesIO(data)
            img = Image.open(bio)

            width, height = img.size
            total_pixels = width * height

            # Explicit check against pixel ceiling
            if total_pixels > cfg.max_image_pixels:
                return (
                    False,
                    mime_type,
                    f"Decompression bomb detected: {total_pixels} pixels exceeds safety ceiling of {cfg.max_image_pixels}",
                    (width, height),
                )

            # Minimum dimension check
            if width < cfg.min_dimension_px or height < cfg.min_dimension_px:
                return (
                    False,
                    mime_type,
                    f"Image dimensions ({width}x{height}) are smaller than minimum requirement of {cfg.min_dimension_px}x{cfg.min_dimension_px}",
                    (width, height),
                )

            # Maximum pre-normalization dimension check
            if width > cfg.max_dimension_px or height > cfg.max_dimension_px:
                return (
                    False,
                    mime_type,
                    f"Image dimensions ({width}x{height}) exceed maximum limit of {cfg.max_dimension_px}x{cfg.max_dimension_px}",
                    (width, height),
                )

            # Verify integrity
            img.verify()

            # Second pass: decode pixel buffer to catch truncated/corrupted raster data
            bio.seek(0)
            img_decode = Image.open(bio)
            img_decode.load()

            return True, mime_type, None, (width, height)

        except Image.DecompressionBombError as bomb_err:
            return (
                False,
                mime_type,
                f"Decompression bomb detected: {bomb_err}",
                (0, 0),
            )
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as decode_err:
            return (
                False,
                mime_type,
                f"Corrupted or malformed image data: {decode_err}",
                (0, 0),
            )
