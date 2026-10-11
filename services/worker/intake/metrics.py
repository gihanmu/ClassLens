"""Visual quality metrics: Laplacian sharpness, RMS contrast, and luminance calculation."""

from __future__ import annotations

from typing import Tuple
import numpy as np
from PIL import Image

from services.worker.intake.contracts import IntakeConfig, QualityStatus


def compute_laplacian_sharpness(img: Image.Image) -> float:
    """Computes Laplacian variance as an objective measure of image focus/sharpness.

    A sharp image with crisp handwritten pencil/pen strokes will have high
    Laplacian variance (typically > 150.0). A severely blurred image will have
    very low variance (< 80.0).

    Args:
        img: PIL Image instance.

    Returns:
        Laplacian variance score as float.
    """
    # Convert to grayscale
    gray = img.convert("L")
    arr = np.array(gray, dtype=float)

    # 2D Laplacian convolution with edge padding
    # Kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    pad = np.pad(arr, 1, mode="edge")
    laplacian = (
        pad[2:, 1:-1]
        + pad[:-2, 1:-1]
        + pad[1:-1, 2:]
        + pad[1:-1, :-2]
        - 4.0 * pad[1:-1, 1:-1]
    )

    return float(np.var(laplacian))


def compute_rms_contrast(img: Image.Image) -> Tuple[float, float]:
    """Computes Root-Mean-Square (RMS) contrast and mean luminance.

    Args:
        img: PIL Image instance.

    Returns:
        Tuple of (contrast_score, mean_luminance).
    """
    gray = img.convert("L")
    arr = np.array(gray, dtype=float)

    contrast = float(np.std(arr))
    mean_lum = float(np.mean(arr))

    return contrast, mean_lum


def assess_quality_status(
    sharpness: float,
    contrast: float,
    mean_lum: float,
    config: IntakeConfig,
) -> Tuple[QualityStatus, bool, str]:
    """Determines pedagogical quality status and teacher review routing.

    Blur and contrast metrics serve as objective quality indicators rather than
    an immediate fatal rejection, preserving the image for educator review.

    Args:
        sharpness: Measured Laplacian variance.
        contrast: Measured RMS contrast (pixel std dev).
        mean_lum: Mean grayscale luminance (0..255).
        config: Intake configuration thresholds.

    Returns:
        Tuple of (QualityStatus, needs_teacher_review, explanation).
    """
    # Severely blurred or unreadable image
    if sharpness < config.min_sharpness_threshold:
        return (
            QualityStatus.UNREADABLE,
            True,
            f"Image sharpness ({sharpness:.1f}) is below threshold ({config.min_sharpness_threshold:.1f}). Handwriting may be blurred.",
        )

    # Faint or low-contrast marks (pencil faint on paper)
    if contrast < config.min_contrast_threshold:
        return (
            QualityStatus.FAINT_READABLE,
            True,
            f"Low contrast detected ({contrast:.1f} < {config.min_contrast_threshold:.1f}). Handwriting appears faint.",
        )

    # Extreme overexposure or underexposure
    if mean_lum < 20.0 or (mean_lum > 245.0 and contrast < 10.0):
        return (
            QualityStatus.UNREADABLE,
            True,
            f"Extreme exposure detected (luminance: {mean_lum:.1f}). Content is not clearly legible.",
        )

    # High quality, legible image
    return (
        QualityStatus.CLEAR,
        False,
        f"Image is sharp ({sharpness:.1f}) and well-contrasted ({contrast:.1f}).",
    )
