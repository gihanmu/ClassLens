# Specification: 002 — Binary Image Intake & Quarantine Validation

**Specification ID:** SPEC-002
**Module:** `services/worker/intake/`
**Related Documents:** [`security-threat-model.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/review/security-threat-model.md), [`threat-model.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/security/threat-model.md)
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

Educators take photos of student math worksheets using personal mobile devices or scanners. These files frequently carry tracking metadata (GPS, device identifiers), extreme resolutions that trigger out-of-memory errors, blurred/faint ink that confuses vision models, or potentially malicious payloads.

`002-image-intake` provides the deterministic intake firewall (`ImageQualityService`). It validates file authenticity, prevents decompression bombs, strips student privacy metadata (EXIF), normalizes image dimensions to max 768px (bounding vision token costs), and halts downstream AI processing if an image is unreadable—saving teacher costs and preventing hallucinated diagnoses.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-002.1 (MIME Magic Bytes Verification)**: Verify raw byte headers using exact binary magic signatures (`\xff\xd8\xff`, `\x89PNG`, `RIFF...WEBP`) and `puremagic`. Accept only `image/jpeg`, `image/png`, and `image/webp`. Reject executables, scripts, or disguised text files.
- **FR-002.2 (Size & Decompression Bomb Protection)**: Enforce a strict file byte ceiling ($10\text{ MB}$). Enforce Pillow ceiling `Image.MAX_IMAGE_PIXELS = 16_000_000` to prevent decompression bombs.
- **FR-002.3 (Dimension Boundary Check)**: Reject images smaller than $300\times 300\text{ px}$ (too degraded) or larger than $4096\times 4096\text{ px}$ prior to downscaling.
- **FR-002.4 (EXIF Stripping & Privacy Sanitization)**: Transpose camera rotation and re-encode image without EXIF metadata (GPS tags, camera serials, timestamps) before moving to validated storage. Alpha channels are composited onto white paper background.
- **FR-002.5 (Dimension Normalization)**: Downscale valid images proportionally using high-fidelity Lanczos resampling so that $\max(\text{width}, \text{height}) \le 768\text{ px}$, preserving faint pencil marks and tick labels.
- **FR-002.6 (Sharpness & Contrast Assessment)**: Compute Laplacian variance (sharpness) and RMS contrast (standard deviation). Treat metrics as objective quality indicators rather than automatic rejection: images with blur or low contrast are promoted to validated with `needs_teacher_review = True` and categorized as `blurred`, `faint_readable`, or `unreadable`.

### Non-Functional Requirements
- **NFR-002.1 (Performance)**: Complete validation, EXIF stripping, and normalization in $< 200\text{ ms}$ for a 5 MB image.
- **NFR-002.2 (Memory Safety)**: Prevent container OOM crashes through stream-based size checking and pixel allocation limits.

---

## 3. Typed Contracts

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

class QualityStatus(str, Enum):
    CLEAR = "clear"
    FAINT_READABLE = "faint_readable"
    BLURRED = "blurred"
    LOW_CONTRAST = "low_contrast"
    ROTATED = "rotated"
    UNREADABLE = "unreadable"

class IntakeValidationResult(BaseModel):
    is_valid: bool
    quality_status: QualityStatus
    mime_type: str
    original_dimensions: tuple[int, int]
    normalized_dimensions: tuple[int, int]
    original_size_bytes: int
    sanitized_size_bytes: int = 0
    sha256_hash: str
    sharpness_score: float
    contrast_score: float = 0.0
    needs_teacher_review: bool = False
    error_message: Optional[str] = None
    quarantine_action: Literal["promote_to_validated", "reject_to_quarantine"]
```
