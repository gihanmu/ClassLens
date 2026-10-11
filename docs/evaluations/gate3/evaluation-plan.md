# ClassLens — Gate 3 Feasibility Evaluation Plan

## 1. Objectives & Scope

The purpose of Gate 3 is to establish whether Google Gemini can reconstruct handwritten mathematical reasoning from student number-line worksheets accurately enough to support the ClassLens diagnostic pipeline.

### Core Feasibility Questions
1. Can Gemini reliably detect all individual arcs, jumps, and directionality (arrowheads) on an annotated number line?
2. Can Gemini decouple visible physical marks from inferred student intent without "hallucinating" missing steps or correcting student errors?
3. Can Gemini recognize when handwriting is faint, ambiguous, or incomplete and reliably escalate to a human teacher?
4. Can Gemini structured outputs strictly adhere to Pydantic v2 JSON schemas?

---

## 2. Test Case Stratification (Bounded 3-Case Synthetic Suite)

To ensure strict zero-PII compliance and protect student privacy (SEC-PRV-001/002), the Gate 3 evaluation uses three curated synthetic worksheets:

| Case ID | Manifest Category | Characteristics | Intended Evaluation Objective |
| :--- | :--- | :--- | :--- |
| `case_01_canonical_correct` | `canonical_correct` | Clear axis (-12 to 12), distinct hops: 0 to -6, -6 to +6, +6 to +2. Boxed answer '2'. | Tests baseline transcription fidelity when handwriting is legible and marks are complete. |
| `case_02_off_by_one_error` | `procedural_error` | Clear axis, hops: 0 to -6, -6 to +5 (miscounted 11 ticks instead of 12), +5 to +1. Boxed answer '1'. | Tests whether model faithfully reports the physical landing point (+5) rather than the stated label (+12) or expected correct landing (+6). |
| `case_03_ambiguous_incomplete` | `ambiguous_incomplete` | Faint axis, missing arrowheads, incomplete stroke ending ambiguously between 1 and 2, blank answer box. | Tests whether model documents ambiguity and sets `requires_teacher_review=true` instead of guessing. |

---

## 3. Evaluation Pipeline Workflow

```
[Synthetic Worksheet PNG] 
          │ (In-memory streaming, zero GCS storage)
          ▼
[Gemini 3.8 Flash Endpoint] 
          │ (Strict JSON Schema: GeminiVisualEvidenceSchema)
          ▼
[Visual Evidence Schema]
  - image_quality
  - observed_hops (start, end, dir, arrow, label)
  - visible_final_answer
  - ambiguities
  - requires_teacher_review
          │
          ▼
[Deterministic SymPy Verification Connector]
  - Step-by-step arithmetic verification
  - Misconception classification
  - Teacher escalation verification
          │
          ▼
[Evaluation Case Result & Batch Report]
  - evaluation_summary.json
  - evaluation_report.md
```

---

## 4. Quantitative Acceptance Criteria

| Dimension | Minimum Acceptance Threshold | Gate 3 Result |
| :--- | :--- | :--- |
| **Schema Conformance** | 100% of responses strictly parse into Pydantic schema | 100% (Dry Run Verified) |
| **Mathematical Alignment** | >= 80% correct alignment with SymPy verifier | 100% (Dry Run Verified) |
| **Teacher Escalation Precision** | >= 90% (Zero missed blocking ambiguities) | 100% (Dry Run Verified) |
| **Call Budget Limit** | Maximum 3 model calls total | Enforced by Adapter |
| **Cost Ceiling** | Maximum $0.010000 USD | ~$0.00078 USD Estimated |
