# Specification: 005 — Teacher Inspection & Review Interface

**Specification ID:** SPEC-005
**Module:** `apps/web/` & `services/api/routers/responses.py`
**Related Documents:** [`personas-and-user-journeys.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/requirements/personas-and-user-journeys.md), [`non-functional-requirements.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/requirements/non-functional-requirements.md)
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

Educators must never be subjected to "black-box" grading without transparent evidence. When an AI proposes an error diagnosis, the teacher must be able to inspect the original student handwriting side-by-side with the AI's transcription, verify the mathematical steps, and exercise unilateral override authority.

`005-teacher-review` implements the Next.js 15 dual-pane inspection interface and backend review override handler. It provides pan/zoom/rotate image inspection, step-by-step reasoning cards with dual visual indicators (icons + text), an audit-trailed Approve / Override form, and accessible keyboard navigation.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-005.1 (Dual-Pane Layout)**:
  - *Left Pane*: High-resolution image canvas with interactive pan, zoom ($\times 0.5$ to $\times 3.0$), and $90^\circ$ rotation controls.
  - *Right Pane*: Structured diagnostic breakdown:
    - Quality status badge (`clear`, `faint_readable`, `unreadable`).
    - Final answer card (`correct` vs `incorrect`) vs visible reasoning status card (`supported_correct`, `supported_error`, `incomplete`).
    - Verified step breakdown showing observed jumps vs expected jumps.
    - First-error localization card highlighting the failure point with pedagogical taxonomy badge.
- **FR-005.2 (Teacher Override Action)**:
  - Form allowing the teacher to select `approved_as_is`, `overridden`, or `marked_unreadable`.
  - When overriding, teacher can select a corrected misconception taxonomy ID from a dropdown and input optional pedagogical notes.
  - Updates `teacher_review_status` and appends an immutable `AuditEventDoc`.
- **FR-005.3 (Color Independence & Accessibility)**: Correct/incorrect indicators must never rely exclusively on color (green/red). Must feature distinct icons (check mark vs cross) and explicit textual status labels.

### Non-Functional Requirements
- **NFR-005.1 (Automated Accessibility)**: Zero automated violations under `@axe-core/playwright` (contrast $\ge 4.5:1$, visible focus rings, ARIA labels on icon buttons).
- **NFR-005.2 (Fluid Responsiveness)**: Dual-pane collapses to stacked tabs on viewport widths $< 1024\text{ px}$.

---

## 3. Typed Contracts

```python
class TeacherReviewAction(BaseModel):
    decision: Literal["approved_as_is", "overridden", "marked_unreadable"]
    override_misconception_id: Optional[str] = None
    notes: Optional[str] = None

class TeacherReviewResponse(BaseModel):
    response_id: str
    teacher_review_status: str
    reviewed_by: str
    reviewed_at: datetime
```
