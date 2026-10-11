# Acceptance Tests: 001 — Deterministic Math & Geometry Verification

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/001-math-verification/spec.md)
**Test Suite Path:** `tests/unit/test_math_verifier.py`

---

## 1. Test Matrix Derived from Problem #1065658 Cases

| Test Case ID | Input Vector Description | Expected Method | Expected Valid Reasoning | Expected Valid Final Answer | Expected Error Step & Taxonomy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-001.01** | `0 -> -6 -> 6 -> 2`, answer: `2` | `hop_from_zero` | `True` | `True` | None (Clean pass) |
| **TC-001.02** | `-6 -> 6 -> 2`, answer: `2` | `direct_start` | `True` | `True` | None (Clean pass) |
| **TC-001.03** | `12 -> 8 -> 2`, answer: `2` | `commutative` | `True` | `True` | None (Clean pass) |
| **TC-001.04** | `0 -> -6 -> 5 -> 2`, answer: `2` (Row 4) | `hop_from_zero` | **`False`** | **`True`** | Step 2: `MISC-ARITH-OFF-BY-ONE`, `is_compensatory_error: True` |
| **TC-001.05** | `0 -> -6 -> 5 -> 1`, answer: `1` (Row 5) | `hop_from_zero` | **`False`** | **`False`** | Step 2: `MISC-ARITH-OFF-BY-ONE`, `is_compensatory_error: False` |
| **TC-001.06** | `0 -> -6 -> 6 -> 2`, answer: `3` (Row 6) | `hop_from_zero` | **`True`** | **`False`** | None in steps; answer mismatch flagged |
| **TC-001.07** | `0 -> 6 -> -6 -> -10` (Reversed start) | `hop_from_zero` | **`False`** | **`False`** | Step 1: `MISC-NUM-DIR-REVERSE` |
| **TC-001.08** | Empty hops `[]`, answer: `2` (Row 11) | `unrecognized` | **`False`** | **`True`** | Step None: `REASONING_INCOMPLETE` |

---

## 2. Verification Execution Command
```bash
pytest tests/unit/test_math_verifier.py -v
```
- **Acceptance Gate**: 100% pass rate in $< 0.5$ seconds with zero cloud dependencies.
