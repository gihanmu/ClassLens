# Acceptance Tests: 006 — Cohort Misconception Dashboard & Differentiated Reteaching

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/006-class-insights/spec.md)
**Test Suite Path:** `tests/unit/test_cohort_statistics.py`

---

## 1. Test Matrix

| Test Case ID | Test Target | Input Data | Expected Outcome | Verification Criterion |
| :--- | :--- | :--- | :--- | :--- |
| **TC-006.01** | Exact Frequencies | 13 responses from Problem #1065658 (7 correct, 4 errors, 1 incomplete, 1 unreadable) | `total: 13`, `correct_count: 7 (53.8%)`, `error_count: 4 (30.8%)`, `unreadable_count: 1 (7.7%)` | Exact fractional values match manual audit table. |
| **TC-006.02** | Misconception Clustering | 4 error responses | Identifies `MISC-ARITH-OFF-BY-ONE` (count: 2) as dominant cluster. | Clusters ranked by frequency in descending order. |
| **TC-006.03** | SymPy Exit Ticket Check | Generated questions targeting off-by-one errors | All question mathematical stems and solutions evaluated by SymPy. | Returns `sympy_verified = True` for all 3 items. |
| **TC-006.04** | Accessible Chart Denominators | UI render test of `MisconceptionBarChart` | Every bar label contains explicit string `X of Y students (Z%)`. | Screen reader test asserts denominator presence. |

---

## 2. Verification Execution Command
```bash
pytest tests/unit/test_cohort_statistics.py -v
```
- **Acceptance Gate**: 100% pass rate in $< 0.5$ seconds with zero cloud dependencies.
