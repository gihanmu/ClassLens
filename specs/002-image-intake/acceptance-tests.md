# Acceptance Tests: 002 — Binary Image Intake & Quarantine Validation

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/002-image-intake/spec.md)
**Test Suite Path:** `tests/unit/test_image_intake.py`

---

## 1. Test Matrix

| Test Case ID | Input Fixture | Expected Validity | Expected Quality Status | Expected Action | Verification Criterion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-002.01** | Valid 800x600 JPEG with EXIF | `True` | `clear` | `promote_to_validated` | Normalized to 768x576; EXIF stripped; SHA256 recorded |
| **TC-002.02** | PNG renamed as `.jpg` | `True` | `clear` | `promote_to_validated` | True MIME detected as `image/png` via magic bytes |
| **TC-002.03** | Text file named `image.png` | `False` | `unreadable` | `reject_to_quarantine` | Rejected with `Invalid MIME type` |
| **TC-002.04** | Raster decompression bomb ($20,000\times 20,000\text{px}$) | `False` | `unreadable` | `reject_to_quarantine` | Catches `DecompressionBombError`; terminates without OOM |
| **TC-002.05** | Heavy Gaussian blurred image | `True` | `unreadable` | `promote_to_validated` | Sharpness $< 80.0$; flags `needs_teacher_review = True` |
| **TC-002.06** | Tiny icon ($100\times 100\text{px}$) | `False` | `unreadable` | `reject_to_quarantine` | Dimensions below minimum 300px threshold |

---

## 2. Verification Execution Command
```bash
pytest tests/unit/test_image_intake.py -v
```
- **Acceptance Gate**: 100% pass rate in $< 1.0$ seconds with zero cloud dependencies.
