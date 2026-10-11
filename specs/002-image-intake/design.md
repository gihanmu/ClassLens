# Design: 002 — Binary Image Intake & Quarantine Validation

**Design ID:** DES-002
**Module:** `services/worker/intake/`
**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/002-image-intake/spec.md)

---

## 1. Module Architecture

```text
services/worker/intake/
├── __init__.py
├── quality_service.py     # Main ImageQualityService entrypoint
├── validator.py           # Magic bytes, size, and decompression bomb validation
├── sanitizer.py           # EXIF stripping & PIL re-encoding
└── metrics.py             # Laplacian variance sharpness & contrast calculation
```

---

## 2. Quarantine State Flow

```mermaid
flowchart TD
    Raw["Raw Object from raw_quarantine/"] --> CheckBytes["1. python-magic: check MIME bytes"]
    CheckBytes -->|Not JPEG/PNG/WebP| RejectMIME["Action: REJECT (Invalid Format)"]
    CheckBytes -->|Valid MIME| CheckSize{"2. Size <= 10MB?"}
    CheckSize -->|No| RejectSize["Action: REJECT (Payload Too Large)"]
    CheckSize -->|Yes| OpenPIL["3. Open with PIL (MAX_IMAGE_PIXELS=16M)"]
    OpenPIL -->|DecompressionBombError| RejectBomb["Action: REJECT (Decompression Bomb)"]
    OpenPIL -->|Success| StripEXIF["4. Strip EXIF & Normalize to max 768px"]
    StripEXIF --> CalcSharp["5. Compute Laplacian Sharpness"]
    CalcSharp --> CheckSharp{"Sharpness >= 80.0?"}
    CheckSharp -->|No| MarkUnreadable["quality_status: UNREADABLE<br>Flag for Teacher Review<br>Halt Downstream LLMs"]
    CheckSharp -->|Yes| Promote["quality_status: CLEAR<br>Save to validated_images/<br>Proceed to Agent Analysis"]
```
