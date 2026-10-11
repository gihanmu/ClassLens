# Implementation Tasks: 005 — Teacher Inspection & Review Interface

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/005-teacher-review/spec.md)
**Status:** Ready for Implementation upon Spec Approval

---

## Task List

- [x] **TASK-005.1**: Implement `PUT /api/v1/responses/{id}/review` endpoint in `services/api/routers/responses.py` updating review status and recording `AuditEventDoc`.
- [x] **TASK-005.2**: Scaffold `apps/web/` using Next.js 15 App Router, TypeScript, Tailwind CSS, and Lucide Icons.
- [x] **TASK-005.3**: Build `ImageViewerCanvas.tsx` supporting pan, zoom ($\times 0.5$ to $\times 3.0$), and $90^\circ$ rotation with keyboard controls.
- [x] **TASK-005.4**: Build `DiagnosticSummaryCard.tsx` and `StepBreakdownList.tsx` rendering dual status indicators (icons + text) without relying exclusively on color.
- [x] **TASK-005.5**: Build `ErrorLocalizationCard.tsx` rendering first-error callout and standard taxonomy badge (`MISC-ARITH-OFF-BY-ONE`).
- [x] **TASK-005.6**: Build `TeacherReviewForm.tsx` supporting Approve, Override (with taxonomy dropdown), and Notes submission.
- [x] **TASK-005.7**: Author automated test suite:
  - Unit tests for review router in `tests/integration/test_teacher_review.py`.
  - Automated accessibility linter test using `@axe-core/playwright`.
