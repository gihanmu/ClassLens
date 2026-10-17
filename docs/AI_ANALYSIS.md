# ClassLens AI Analysis & Mathematical Verification Engine

## Architecture Overview

ClassLens rejects the "black-box LLM grader" paradigm. In K-12 mathematics education, an LLM acting as sole arbiter of student correctness frequently hallucinates, overlooks subtle sign reversals, or invents intermediate steps.

ClassLens enforces a strict **Two-Phase Diagnostic Architecture**:
1. **Multimodal Perception (Vertex AI Gemini 1.5 Flash)**: Transcribes handwritten expressions, diagrammatic hops, coordinate marks, and written student justifications into structured semantic steps.
2. **Deterministic Mathematical Verification (SymPy Engine)**: Evaluates algebraic equivalence, arithmetic progressions, interval counts, and vector signs with 100% mathematical certainty.

```
+---------------------------------------------------------------------------------------------------+
|                                      TWO-PHASE AI PIPELINE                                        |
+---------------------------------------------------------------------------------------------------+
|  Phase 1: Perception (Gemini 1.5 Flash)                                                           |
|  - Ingests raw worksheet image bytes                                                              |
|  - Extracts question context, final answer, reasoning steps, diagram representations              |
|  - Enforces JSON Schema validation (WorksheetAnalysisResult)                                     |
|  - Evaluates Evidence Sufficiency (rejects unreadable, partial, or cropped-out work)              |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|  Task Router (services/api/analysis/task_router.py)                                               |
|  - Inspects assessment domain: INTEGER_OPERATIONS vs FRACTION_DIVISION vs UNSUPPORTED             |
|  - Dispatches to specialized symbolic verifier                                                    |
+---------------------------------------------------------------------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
+-------------------------------------------------+  +---------------------------------------------+
| Phase 2A: Integer Verifier (math_verifier.py)   |  | Phase 2B: Fraction Verifier (fraction_v...)|
| - Reconstructs number-line intervals & hops     |  | - Evaluates unit form conversions           |
| - Identifies sign flips & directional inversion |  | - Checks invert-and-multiply transformations|
| - Verifies hop-from-zero vs direct start        |  | - Reconciles visual area models with quotient|
+-------------------------------------------------+  +---------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| Taxonomy Mapper & Misconception Diagnostics                                                       |
| - Maps mathematical discrepancies to standardized taxonomy codes                                 |
| - Assigns confidence score (heuristic indicator based on evidence clarity)                        |
| - Generates preliminary status: Correct / Needs Review / Insufficient Evidence                    |
+---------------------------------------------------------------------------------------------------+
```

---

## Task Router & Supported Mathematical Domains

The `TaskRouter` inspects the assessment prompt, question text, and rubric specifications:

| Domain Key | Characteristics | Specialized Verifier |
|---|---|---|
| `INTEGER_OPERATIONS_NUMBER_LINE` | Directed integer addition/subtraction, hops, number lines | `MathVerifier` (Intervals, vectors, compensatory steps) |
| `FRACTION_DIVISION` | Fraction quotients, unit forms, visual strip/tape models | `FractionDivisionVerifier` (SymPy rational arithmetic) |
| `UNSUPPORTED_TASK` | Out-of-scope math domains (e.g. calculus, geometry proofs) | Returns `UNSUPPORTED_TASK` gracefully without guessing |

---

## Misconception Taxonomy Codes

### Integer Operations on Number Lines
- `MISC-DIR-INV`: **Directional Inversion** — Student moved left instead of right (or vice versa), confusing sign semantics of negative addition or subtraction.
- `MISC-MAG-COUNT`: **Magnitude / Interval Miscount** — Student counted tick marks rather than intervals, or misread interval spacing.
- `MISC-ARITH-OFF-BY-ONE`: **Off-by-One Arithmetic Error** — Correct hop structure but final calculation deviated by ±1.
- `MISC-START-ORIGIN`: **Origin Ambiguity** — Student assumed hop starts from origin without accounting for initial offset.
- `MISC-SLIP`: **Computational Slip** — Conceptual model was sound, but minor clerical arithmetic error occurred.

### Fraction Division
- `MISC-FRAC-DIV-INVERT-WRONG`: **Invert and Multiply Misapplication** — Student inverted the dividend instead of divisor, or inverted both.
- `MISC-FRAC-DIV-GROUP-SIZE`: **Group Size vs Number of Groups Confusion** — Misunderstanding the divisor as groups rather than items per group.
- `MISC-FRAC-DIV-UNIT-FORM`: **Unit Form Conversion Error** — Incorrect conversion to common denominator units before division.

---

## Evidence Sufficiency & Anti-Hallucination Rules

1. **Zero Hallucination Rule**: If Gemini fails to transcribe legible student steps or if the student wrote only an isolated number with zero visible reasoning, the system **never** invents hypothetical hops. It returns `has_sufficient_evidence = false` and status `Insufficient Evidence`.
2. **Confidence Score Semantics**: The confidence score (0.0 to 1.0) is a **heuristic indicator** reflecting visual handwriting clarity and step completeness. It is **not** a calibrated statistical probability.
3. **Teacher Review Override**: Teachers possess complete authority to override AI classifications, amend diagnosed misconceptions, or add contextual notes. Overrides preserve the original AI diagnostic record for comparison and quality tracking.
