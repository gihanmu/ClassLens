# ClassLens — Gate 3 Student Privacy & Security Verification Checklist

**Standard Alignment:** SEC-PRV-001 (Zero-PII Transmission), SEC-PRV-002 (Provisional Dataset Isolation), FERPA & COPPA Principles.

---

## 1. Privacy Safeguards Verification Matrix

| Checklist Item | Description | Verification Status | Implementation Proof |
| :--- | :--- | :--- | :--- |
| **Zero Real Student PII Transmitted** | No real student images, names, IDs, or metadata are transmitted to external AI APIs. | **PASSED** | Only synthetic PIL-generated images in `tests/fixtures/synthetic_evaluation_cases/` are included in the manifest. |
| **Zero Google Cloud Storage (GCS) Buckets** | No student worksheet images are staged or uploaded to cloud storage buckets. | **PASSED** | Images are converted to raw in-memory bytes and streamed directly via `types.Part.from_bytes(data=image_bytes)`. |
| **Ephemeral In-Memory Processing** | Processed bytes reside only in volatile memory during the HTTP request lifecycle. | **PASSED** | No local temporary copies or cache files are persisted in public or unmonitored directories. |
| **Zero Model Training Retention** | Vertex AI enterprise inference agreements guarantee that customer inputs and outputs are not used for foundation model training. | **PASSED** | Adapter enforces enterprise mode (`genai.Client(enterprise=True)`). |
| **Output Directory Excluded from Git** | Local test run dumps, token logs, and raw outputs in `.evaluation_outputs/` must not be checked into Git. | **PASSED** | `.evaluation_outputs/` added to root `.gitignore`. |
| **Provisional Dataset Isolation** | Raw 2,030-image research dataset and 13 curated response images remain local and offline. | **PASSED** | Dataset files in `/dataset/*` remain strictly excluded in `.gitignore` and offline. |
| **Hard Call Budget Safeguard** | Model adapter strictly enforces a maximum call ceiling to prevent runaway requests or batch leaks. | **PASSED** | Hard limit of 3 calls enforced in `GeminiEvaluationAdapter.max_calls`. |

---

## 2. Security Officer Attestation

Before authorizing live model calls:
1. Manifest points exclusively to `tests/fixtures/synthetic_evaluation_cases/*.png`.
2. Hard ceiling is set to `--max-calls 3`.
3. Offline dry-run has successfully validated 100% schema compliance.
