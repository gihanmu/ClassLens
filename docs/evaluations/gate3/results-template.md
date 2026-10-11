# ClassLens — Gate 3 Teacher Review & Evaluation Results Template

This template is designed for human educators and evaluation engineers to review and audit model outputs against ground truth following live execution.

---

## 1. Case Audit Form

### Case ID: `[case_id]`
- **Evaluator Name:** `[Educator / Engineer]`
- **Date Evaluated:** `[YYYY-MM-DD]`
- **Category:** `[canonical_correct | procedural_error | ambiguous_incomplete]`
- **Worksheet File:** `[path/to/image.png]`

---

## 2. Dimension Scoring (1–4 Scale)

| Evaluation Dimension | Weight | Score (1-4) | Observations & Evidence |
| :--- | :--- | :--- | :--- |
| **1. Visual Element Capture** | 30% | `[ ]` | Did Gemini capture all hops and tick labels accurately? |
| **2. Directionality & Arrowheads** | 20% | `[ ]` | Were arrowheads and directions correctly identified? |
| **3. Mathematical Decoupling** | 25% | `[ ]` | Did Gemini report visible marks without fixing student math errors? |
| **4. Ambiguity & Quality** | 15% | `[ ]` | Were faint strokes or missing marks correctly documented? |
| **5. Teacher Escalation Precision** | 10% | `[ ]` | Did the model escalate when appropriate? |

**Weighted Total Score:** `[   ] / 4.0` (Target: >= 3.4 / 85%)

---

## 3. Discrepancy & Hallucination Log

| Item | Extracted by Model | Actual Ink on Worksheet | Discrepancy Type | Impact Severity |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `[Model output]` | `[Physical reality]` | `[Omission / Hallucination / Coordinate shift]` | `[Minor / Blocking]` |
| 2 | `[Model output]` | `[Physical reality]` | `[Omission / Hallucination / Coordinate shift]` | `[Minor / Blocking]` |

---

## 4. Final Verification Decision

- [ ] **ACCEPTED:** High fidelity transcription; safe for diagnostic pipeline.
- [ ] **NEEDS REFINEMENT:** Minor prompt adjustments needed for arrowheads/faint marks.
- [ ] **REJECTED:** Hallucinations or mathematical conflation observed.

**Educator Notes & Feedback:**
> `[Teacher qualitative assessment here]`
