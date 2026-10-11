# Implementation Tasks: 001 — Deterministic Math & Geometry Verification

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/001-math-verification/spec.md)
**Status:** Completed & Verified via Unit Tests (47/47 passing)

---

## Task List

- [x] **TASK-001.1**: Initialize `services/worker/math_verifier/` package with `__init__.py` and typed Pydantic models matching `SPEC-001`.
- [x] **TASK-001.2**: Implement `SymPyChecker.eval_arithmetic(expr: str) -> float` and `SymPyChecker.verify_equality(lhs: str, rhs: float) -> bool` with robust exception handling for `SympifyError`.
- [x] **TASK-001.3**: Implement `NumberLineDisplacementCalculator.compute_displacements(hops: List[NumberLineHop]) -> List[float]` verifying vector magnitude and sign.
- [x] **TASK-001.4**: Implement `MethodMatcher` supporting canonical paths (hop from zero, direct start, commutative rearrangement).
- [x] **TASK-001.5**: Implement `TaxonomyMapper` classifying directional reversals, off-by-one errors, interval slips, and compensatory error flags.
- [x] **TASK-001.6**: Implement integration entrypoint `verify_student_math_reasoning(hops: List[NumberLineHop], final_answer: Optional[float], rule: QuestionRule) -> MathVerificationVerdict`.
- [x] **TASK-001.7**: Author comprehensive unit test suite in `tests/unit/test_math_verifier.py` validating all 13 test fixtures.
