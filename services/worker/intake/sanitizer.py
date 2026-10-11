"""Image sanitization, EXIF stripping, high-fidelity normalization, and privacy protection."""

from __future__ import annotations

import io
from typing import Optional, Tuple
from PIL import Image, ImageOps

from services.worker.intake.contracts import IntakeConfig


def sanitize_and_normalize_image(
    raw_bytes: bytes,
    detected_mime: str,
    config: Optional[IntakeConfig] = None,
) -> Tuple[bytes, Tuple[int, int], Tuple[int, int]]:
    """Strips all privacy metadata and scales image proportionally to bounded dimensions.

    Guarantees:
    1. EXIF, GPS, camera metadata, and user identifiers are completely stripped.
    2. Phone camera rotation orientation is corrected before metadata removal.
    3. Transparent backgrounds are cleanly alpha-composited onto pure white paper.
    4. Image is proportionally scaled so max(width, height) <= max_normalized_dim (768px).
    5. High-fidelity Lanczos resampling is used to preserve fine pencil strokes,
       arrowheads, and tick marks.
    6. Output is re-encoded into clean, standard format.

    Args:
        raw_bytes: Validated raw image bytes.
        detected_mime: Validated MIME type (e.g. 'image/jpeg', 'image/png', 'image/webp').
        config: Optional configuration thresholds.

    Returns:
        Tuple of (sanitized_bytes, original_dimensions, normalized_dimensions).
    """
    cfg = config or IntakeConfig()

    # Open image from in-memory stream
    bio = io.BytesIO(raw_bytes)
    img = Image.open(bio)

    original_dims = (img.width, img.height)

    # 1. Correct camera orientation according to EXIF before stripping tags
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        # If EXIF orientation tag is corrupt, continue with unaltered layout
        pass

    # 2. Handle transparency / alpha channels (composite onto white background)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img_rgba = img.convert("RGBA")
        background = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
        alpha_composited = Image.alpha_composite(background, img_rgba)
        img = alpha_composited.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # 3. Strip all metadata dictionaries and color profiles
    img.info = {}

    # 4. Dimension normalization (Proportional downscaling)
    orig_w, orig_h = img.size
    max_dim = max(orig_w, orig_h)

    if max_dim > cfg.max_normalized_dim_px:
        scale = cfg.max_normalized_dim_px / float(max_dim)
        target_w = max(1, int(round(orig_w * scale)))
        target_h = max(1, int(round(orig_h * scale)))

        # Use Lanczos resampling to prevent blurring of thin pencil marks and tick labels
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        normalized_dims = (target_w, target_h)
    else:
        normalized_dims = (orig_w, orig_h)

    # 5. Re-encode cleanly without metadata
    out_bio = io.BytesIO()

    # Re-encode in JPEG (for photos) or PNG (for lossless diagrams)
    if detected_mime == "image/png":
        img.save(out_bio, format="PNG", optimize=True)
    else:
        # Standardize on high-quality JPEG (quality=92) with standard 4:4:4 subsampling
        # to prevent color bleeding around dark math ink
        img.save(
            out_bio,
            format="JPEG",
            quality=92,
            optimize=True,
            subsampling=0,
        )

    sanitized_bytes = out_bio.getvalue()
    return sanitized_bytes, original_dims, normalized_dims
