# Acceptance Tests: 005 — Teacher Inspection & Review Interface

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/005-teacher-review/spec.md)
**Test Suite Paths:** `tests/integration/test_teacher_review.py` & `apps/web/tests/a11y.spec.ts`

---

## 1. Test Matrix

| Test Case ID | Test Target | Preconditions / Action | Expected Outcome | Verification Criterion |
| :--- | :--- | :--- | :--- | :--- |
| **TC-005.01** | Approve Diagnosis | Teacher clicks "Approve Diagnosis" | Status updates to `approved_as_is`; audit log created. | Database confirms `teacher_review_status == "approved_as_is"`. |
| **TC-005.02** | Override Diagnosis | Teacher selects `MISC-NUM-DIR-REVERSE` & adds notes | Status updates to `overridden`; corrected taxonomy saved; `reviewed_responses` incremented. | Audit event contains `old_state` and `new_state`. |
| **TC-005.03** | Canvas Controls | User clicks Zoom In ($\times 2.0$) and Rotate $90^\circ$ | Canvas CSS transform applies `scale(2) rotate(90deg)`. | Visual transformation verified via DOM inspect. |
| **TC-005.04** | Dual Indicators | Inspect DOM of step list | Green check icon has aria-label "Correct"; red cross has aria-label "Error". | No status indicated by color alone. |
| **TC-005.05** | Automated Accessibility Linter | Run Playwright axe-core audit on inspection page | 0 violations for color contrast ($\ge 4.5:1$), ARIA tags, or focus rings. | `@axe-core/playwright` returns 0 critical/serious violations. |

---

## 2. Verification Execution Command
```bash
pytest tests/integration/test_teacher_review.py -v
npx playwright test apps/web/tests/a11y.spec.ts
```
