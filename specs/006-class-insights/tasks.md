# Implementation Tasks: 006 — Cohort Misconception Dashboard & Differentiated Reteaching

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/006-class-insights/spec.md)
**Status:** Ready for Implementation upon Spec Approval

---

## Task List

- [x] **TASK-006.1**: Implement `services/worker/cohort/statistics_calculator.py` computing counts, percentages, and misconception clusters from response lists.
- [x] **TASK-006.2**: Implement `services/worker/cohort/exit_ticket_validator.py` verifying exit ticket math using `SymPyChecker`.
- [x] **TASK-006.3**: Implement mock cohort synthesizer returning structured `CohortIntelligenceOutput` for Problem #1065658.
- [x] **TASK-006.4**: Build `apps/web/components/cohort/MisconceptionBarChart.tsx` displaying explicit fractional denominators (e.g. `4/13`).
- [x] **TASK-006.5**: Build `apps/web/components/cohort/ReteachingActionCards.tsx` rendering small-group strategies and printable exit ticket view.
- [x] **TASK-006.6**: Author unit test suite in `tests/unit/test_cohort_statistics.py` verifying calculations across the 13 responses of Problem #1065658.
