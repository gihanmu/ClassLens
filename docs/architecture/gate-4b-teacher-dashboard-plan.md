# ClassLens — Gate 4B: Teacher Dashboard & AI Analysis Integration Architecture Plan

**Document Version:** 1.0.0  
**Target Branch:** `feature/gate-4b-teacher-dashboard`  
**Base Commit:** `ef3ebb3`  
**Author:** Principal Software Architect & Full-Stack AI Engineer  

---

## 1. Executive Summary & Objective

Gate 4B transforms ClassLens into a fully functional, evidence-grounded mathematical reasoning review experience for secondary school mathematics educators. Building upon the verified Gate 4A.2 multimodal pipeline, Gate 4B connects the existing 5-agent AI system to intuitive teacher workflows.

Teachers must be able to:
1. Navigate seamlessly between the class dashboard, assessment checkpoints, student responses, multimodal reasoning analyses, and teacher review workflows.
2. Inspect the original student handwritten worksheet side-by-side with AI reasoning extraction, with zoom, fit-to-screen, and hop overlays.
3. Explicitly distinguish final answer correctness from step-by-step reasoning validity.
4. Understand what Gemini physically observed versus what SymPy deterministically verified.
5. Identify supported misconceptions with clear evidence citations, while suppressing ungrounded diagnoses when evidence is ambiguous or incomplete (Case 3).
6. Inspect the Independent Critic grounding audit verdict, discrepancy notes, and escalation reasons.
7. Execute real teacher reviews and overrides (confirm, override taxonomy, mark as insufficient evidence/unreadable, add notes) backed by an immutable audit trail.
8. Explore cohort intelligence with evidence-aware aggregation (excluding ambiguous and unreadable cases from confirmed misconception counts).
9. Drill down into specific misconception clusters and access actionable, grounded reteaching recommendations.

---

## 2. Existing Architecture Audit

### 2.1 Frontend Architecture (`apps/web/`)
- **Next.js 14 App Router:**
  - `apps/web/src/app/page.tsx`: Main dashboard interface hosting 5 tabs (`responses`, `insights`, `recommendations`, `resources`, `assessments`).
  - `apps/web/src/app/dev/gemini-test/page.tsx`: Development-only manual testing lab created in Gate 4A.1.
- **Components:**
  - `apps/web/src/components/inspection/StudentInspectionModal.tsx`: Dual-pane inspection modal (left: `StudentWorkViewer`, right: reasoning cards, review panel, audit drawer).
  - `apps/web/src/components/features/students/StudentWorkViewer.tsx`: Canvas/image viewer with zoom in/out, fit-to-screen, and SVG hop overlay support.
  - `apps/web/src/components/features/analysis/ReasoningStepCard.tsx`: Step verification card supporting SymPy valid, procedural error, and unverifiable amber states.
  - `apps/web/src/components/features/analysis/MisconceptionCard.tsx`: Displays first supported error and taxonomy title.
  - `apps/web/src/components/features/teacher-review/TeacherReviewPanel.tsx`: Interactive review form for confirming or overriding AI diagnoses.
  - `apps/web/src/components/inspection/AuditTrailDrawer.tsx`: Drawer displaying the response's immutable audit history.
  - `apps/web/src/components/features/cohort/`: `TeachingRecommendationCard`, `ClassroomResourcesView`, and `MisconceptionBarChart`.

### 2.2 Backend Architecture (`services/api/` & `services/worker/`)
- **FastAPI Endpoints:**
  - `/api/v1/assessments`: Checkpoint management, batch multi-agent trigger (`/analyze`), analysis status polling (`/status`).
  - `/api/v1/assessments/{id}/insights`: Cohort intelligence and distribution statistics.
  - `/api/v1/responses/{id}`: Detailed response analysis with tenant isolation.
  - `/api/v1/responses/{id}/image`: Handwritten image serving with provenance verification.
  - `/api/v1/responses/{id}/review`: Teacher review submission.
  - `/api/v1/responses/{id}/audit-trail`: Immutable audit log of teacher reviews.
  - `/api/v1/dev/*`: Development test lab endpoints with strict localhost guards.
- **Agent Pipeline & Grounding Engine (`services/worker/agents/`):**
  - `MultiAgentPipeline`: 5-agent pipeline (VisualEvidenceAgent, MathInterpretationAgent, DiagnosticAgent, IndependentCriticAgent, CohortIntelligenceAgent).
  - `EvidenceSufficiencyEvaluator`: Evaluates stroke clarity, coordinate certainty, and flags incomplete evidence.
  - `MockAgentAdapter`: Deterministic offline execution for mock mode.

---

## 3. Missing Integration Points & Required Enhancements

### 3.1 Teacher Dashboard Overview & Review Queue (Phase 2)
1. **Enhanced Metrics:** Add explicit metric counters for "Responses Awaiting Review" and "Insufficient Visual Evidence".
2. **Review Queue Section:** Provide a dedicated view/filter for responses requiring teacher attention (`needs_teacher_review && teacher_review_status === "unreviewed"`), displaying student label, reason for escalation, and direct inspection action.
3. **Evidence Sufficiency Filter:** Enable filtering by evidence state (`all`, `review`, `insufficient`, `errors`, `correct`).

### 3.2 Student Response Inspection (Phase 3)
1. **Three-Way Separation of Concerns:**
   - Clearly delineate:
     - **Observed on Worksheet** (physical marks, arrow jumps, bracket curves, written digits).
     - **Mathematically Interpreted** (detected strategies, candidate sequences).
     - **Verified by SymPy** (exact algebraic and interval verification).
2. **Independent Critic Audit Card:**
   - Directly render the Critic's audit in `StudentInspectionModal`:
     - Audit verdict: `audit_passed`, `review_required`, or `audit_rejected`.
     - Contradiction detected indicator.
     - Evidence grounded indicator.
     - Review escalation reason and discrepancy notes.
3. **Ambiguity & Insufficient Evidence Handling:**
   - In Case 3 (or any incomplete submission), ensure no hallucinated misconception is shown.
   - Display a prominent message: *"No reliable misconception can be assigned from the available evidence."*
   - Display unverifiable steps with warm amber badge: `Unverifiable (Insufficient Evidence)`.
4. **Calibrated Confidence Presentation:**
   - Display qualitative confidence tiers (`Clear Evidence (High)`, `Partially Supported (Moderate)`, `Insufficient Evidence (Low)`).
   - Clarify that numeric percentages represent internal model extraction scores rather than calibrated probabilities.

### 3.3 Teacher Review & Override Persistence (Phase 4)
1. **Comprehensive Review Actions:**
   - Support: `approved_as_is`, `overridden`, `marked_unreadable`, `insufficient_evidence`.
   - Allow entering custom educator notes.
2. **Preservation of Raw Evidence:**
   - Confirm that overrides update review status and override taxonomy without modifying raw image bytes, visual evidence observations, or original AI diagnostic fields.
3. **Audit History Verification:**
   - Verify that `AuditEventDoc` logs `teacher_id`, `timestamp`, `action`, `old_state`, `new_state`, and `notes`.
   - Ensure audit logs persist and are retrievable across reloads.

### 3.4 Cohort Intelligence (Phase 5)
1. **Evidence-Aware Aggregation:**
   - In `CohortStatisticsCalculator`:
     - Exclude unreadable and `insufficient_evidence` cases from confirmed misconception clusters.
     - Differentiate `ai_proposed_count` vs `teacher_confirmed_count`.
     - Ensure the denominator matches the total active cohort.
2. **Actionable Reteaching Recommendations:**
   - Ground recommendations directly in the detected class misconceptions.
   - Support drilling down from a misconception into the filtered student responses.

### 3.5 Synthetic Demo Data (Phase 6)
1. **Deterministic Seeding of Cases 1, 2, and 3:**
   - Ensure the assessment view or import mechanism provides immediate, deterministic access to:
     - Case 1: `case_01_canonical_correct` (Final answer 2, valid hops, correct reasoning, no review needed).
     - Case 2: `case_02_off_by_one_error` (Final answer 1, hop 2 jumped +11 instead of +12, off-by-one interval error).
     - Case 3: `case_03_ambiguous_incomplete` (Final answer undetermined, incomplete reasoning, unverifiable steps, no misconception, review required).
   - Ensure response images for synthetic fixtures are correctly resolved and served.

---

## 4. End-to-End Data Flow

```mermaid
flowchart TD
    subgraph Frontend ["Next.js Teacher Dashboard"]
        TD[Teacher Dashboard] --> RQ[Review Queue]
        TD --> SR[Student Response Grid]
        TD --> CI[Cohort Intelligence]
        SR --> IM[Student Inspection Modal]
        IM --> WW[Student Work Viewer - Left Pane]
        IM --> DC[Diagnostic & Step Cards - Right Pane]
        IM --> CC[Critic Audit Card]
        IM --> TRP[Teacher Review Panel]
        TRP --> AD[Audit Trail Drawer]
    end

    subgraph Backend ["FastAPI API Service"]
        API_A[/api/v1/assessments]
        API_R[/api/v1/responses/{id}]
        API_IMG[/api/v1/responses/{id}/image]
        API_REV[/api/v1/responses/{id}/review]
        API_AUD[/api/v1/responses/{id}/audit-trail]
        API_INS[/api/v1/assessments/{id}/insights]
    end

    subgraph Storage ["Thread-Safe Repository"]
        REPO[(MemoryRepository / Firestore)]
        AUDIT[(Audit Event Log)]
    end

    TD --> API_A
    IM --> API_R
    WW --> API_IMG
    TRP --> API_REV
    AD --> API_AUD
    CI --> API_INS

    API_REV --> REPO
    API_REV --> AUDIT
    API_AUD --> AUDIT
```

---

## 5. Security and Safety Boundaries

1. **Strict Offline Mock Default:**
   - `CLASSLENS_AI_MODE=mock` is maintained throughout.
   - Zero live Gemini API calls are made during Gate 4B development and automated testing.
2. **Provenance Guard Enforcement:**
   - Even in mock/demo mode, image serving enforces server-side file existence and directory containment.
3. **Tenant Isolation:**
   - Backend routes verify user organization ID on all assessment and response lookups.
4. **Data Integrity:**
   - Teacher overrides are strictly additive. Original AI analyses and raw image observations are never deleted or modified.

---

## 6. Implementation and Verification Plan

1. **Step 1:** Enhance backend repository and image serving to seamlessly support both Problem #1065658 dataset and authorized synthetic cases (Cases 1, 2, and 3).
2. **Step 2:** Update `CohortStatisticsCalculator` to support evidence-aware aggregation and evidence sufficiency breakdown.
3. **Step 3:** Enhance `apps/web/src/app/page.tsx` with review queue filtering, evidence sufficiency metrics, and misconception drill-down.
4. **Step 4:** Enhance `StudentInspectionModal.tsx`, `DiagnosticSummaryCard.tsx`, `CriticAuditCard.tsx`, and `ReasoningStepCard.tsx` with three-way evidence separation, Critic audit display, calibrated confidence, and ungrounded misconception suppression.
5. **Step 5:** Add comprehensive backend unit tests covering dashboard aggregation, review persistence, audit logging, tenant isolation, and synthetic demo cases.
6. **Step 6:** Run full test suite (`pytest`) and Next.js production build (`npm run build`).
7. **Step 7:** Document implementation in `docs/implementation/gate-4b-teacher-dashboard.md`.
