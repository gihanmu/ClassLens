# Implementation Tasks: 002 — Binary Image Intake & Quarantine Validation

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/002-image-intake/spec.md)
**Status:** Completed & Verified via Unit Tests (27/27 passing, 74/74 total)

---

## Task List

- [x] **TASK-002.1**: Initialize `services/worker/intake/` module with typed Pydantic models matching `SPEC-002`.
- [x] **TASK-002.2**: Implement `validator.py` verifying MIME magic bytes via binary signatures and `puremagic`, checking byte length ($\le 10\text{ MB}$), and setting `Image.MAX_IMAGE_PIXELS = 16_000_000`.
- [x] **TASK-002.3**: Implement `sanitizer.py` stripping EXIF metadata, re-encoding to clean JPEG/PNG, and proportionally scaling to $\max(\text{dim}) \le 768\text{ px}$.
- [x] **TASK-002.4**: Implement `metrics.py` computing Laplacian variance and RMS contrast indicators.
- [x] **TASK-002.5**: Implement `ImageQualityService.process_image_bytes(raw_bytes: bytes) -> tuple[IntakeValidationResult, Optional[bytes]]`.
- [x] **TASK-002.6**: Author comprehensive unit test suite in `tests/unit/test_image_intake.py` testing valid images, corrupt files, non-images, raster bombs, and blurred images.
