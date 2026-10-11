# Design: 005 — Teacher Inspection & Review Interface

**Design ID:** DES-005
**Module:** `apps/web/` & `services/api/`
**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/005-teacher-review/spec.md)

---

## 1. Component Hierarchy (Next.js 15 App Router)

```text
apps/web/src/
├── app/
│   ├── assessments/
│   │   └── [id]/
│   │       ├── responses/
│   │       │   └── [responseId]/
│   │       │       └── page.tsx           # Dual-Pane Inspection View
│   │       └── page.tsx                   # Assessment Overview
├── components/
│   ├── inspection/
│   │   ├── ImageViewerCanvas.tsx          # Pan, zoom, rotate image canvas
│   │   ├── DiagnosticSummaryCard.tsx      # Answer vs Reasoning status badges
│   │   ├── StepBreakdownList.tsx          # Number line jump step cards
│   │   ├── ErrorLocalizationCard.tsx      # First error callout with taxonomy badge
│   │   └── TeacherReviewForm.tsx          # Approve / Override action controls
│   └── ui/
│       ├── Button.tsx
│       ├── Badge.tsx
│       └── Modal.tsx
```

---

## 2. Review Override State Mutation Flow

```mermaid
sequenceDiagram
    autonumber
    participant Teacher as Teacher Browser (Next.js)
    participant API as FastAPI Backend (/api/v1/responses/{id}/review)
    participant Repo as Persistence Layer / Audit Log

    Teacher->>API: PUT /responses/{id}/review (decision: "overridden", new_taxonomy, notes)
    API->>API: Verify user authorization & validate CSRF
    API->>Repo: Update ResponseDoc.teacher_review_status = "overridden"
    API->>Repo: Append AuditEventDoc (action: "OVERRIDE_DIAGNOSIS", old_state, new_state)
    API->>Repo: Increment AssessmentDoc.reviewed_responses counter
    API-->>Teacher: HTTP 200 OK (TeacherReviewResponse)
    Teacher->>Teacher: Update UI badge to "Overridden by Teacher" with green check
```
