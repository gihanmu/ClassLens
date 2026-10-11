# ClassLens — Engineering Specifications Directory

**Version:** 1.0.0
**Status:** Fully Implemented and 100% Offline Verified (Sprints 1 through 6 Complete)
**Methodology:** Specification-Driven Development (SDD) & Deterministic Test-First Engineering

---

## 1. Specification-Driven Development Overview

ClassLens follows a strict **Specification-Driven Development** workflow. Implementation code is never authored ad-hoc; every feature is derived from approved architectural requirements, documented in a four-part specification bundle, and validated against explicit acceptance criteria before implementation.

### Specification Directory Layout

```text
specs/
├── README.md
├── 001-math-verification/          # Deterministic rational arithmetic & geometry engine
│   ├── spec.md                     # Requirements, scope, contracts, and rules
│   ├── design.md                   # Architecture, algorithms, data structures
│   ├── tasks.md                    # Ordered, atomic implementation tasks
│   └── acceptance-tests.md         # Test cases, synthetic fixtures, expected verdicts
├── 002-image-intake/               # Binary quarantine, validation, EXIF stripping
│   ├── spec.md
│   ├── design.md
│   ├── tasks.md
│   └── acceptance-tests.md
├── 003-agent-orchestration/        # Bounded Google ADK agent pipeline & mock adapters
│   ├── spec.md
│   ├── design.md
│   ├── tasks.md
│   └── acceptance-tests.md
├── 004-analysis-api/               # FastAPI batch analysis endpoints & task dispatch
│   ├── spec.md
│   ├── design.md
│   ├── tasks.md
│   └── acceptance-tests.md
├── 005-teacher-review/             # Next.js dual-pane inspection & teacher override UI
│   ├── spec.md
│   ├── design.md
│   ├── tasks.md
│   └── acceptance-tests.md
└── 006-class-insights/             # Cohort statistical aggregation & reteaching cards
    ├── spec.md
    ├── design.md
    ├── tasks.md
    └── acceptance-tests.md
```

---

## 2. Skill Guidance & Workflow Integration

The specification process synthesizes the official Google skills installed in `.agents/skills/`:

| Feature Area | Primary Guiding Skills | Architectural & Implementation Influence |
| :--- | :--- | :--- |
| **001: Math Verification** | Local deterministic Python | Pure SymPy algebraic verification and geometric vector math without LLM dependency. |
| **002: Image Intake** | `google-cloud-storage-basics`<br>`google-cloud-waf-security` | Signed upload quarantine paths, byte-level MIME inspection, decompression bomb limits, and EXIF sanitization. |
| **003: Agent Orchestration** | `google-agents-cli-workflow`<br>`google-agents-cli-adk-code`<br>`gemini-api` | ADK agent definitions, tool binding (`FunctionTool`), Pydantic schemas, mock LLM runners, and prompt design. |
| **004: Analysis API** | `google-cloud-solution-n-tier-serverless-web-app`<br>`sign-in-with-google-web` | Public/private decoupling, GIS cookie auth, CSRF headers, and idempotent Cloud Tasks dispatch contracts. |
| **005: Teacher Review** | `sign-in-with-google-web`<br>Local accessibility linters | Accessible Next.js 15 dual-pane UI, audit trail persistence, and teacher override authority. |
| **006: Class Insights** | `google-agents-cli-adk-code`<br>`gemini-api` | Deterministic cohort frequency computation in Python; LLM synthesis of qualitative narrative and exit tickets. |

---

## 3. Traceability Matrix

Every specification traces back to approved requirements in `docs/`:

| Spec ID | Feature Name | Core Requirements | Architecture Decision | Data Model Entity |
| :--- | :--- | :--- | :--- | :--- |
| `001` | Math Verification | `REQ-FUN-002`, `REQ-NFR-002` | `ADR-005` (Deterministic Core) | `VerifiedStep`, `FirstSupportedError` |
| `002` | Image Intake | `REQ-SEC-002`, `REQ-FUN-001` | `ADR-004` (Quarantine Pipeline) | `ResponseDoc.upload_status` |
| `003` | Agent Orchestration | `REQ-AGT-001` to `005` | `ADR-003`, `ADR-005` | `VisualEvidenceOutput`, `DiagnosticOutput` |
| `004` | Analysis API | `REQ-API-001`, `REQ-API-002` | `ADR-002` (Cloud Tasks Idempotency) | `AnalysisJobDoc`, `JobAttemptDoc` |
| `005` | Teacher Review | `REQ-UI-001`, `REQ-GOV-001` | `ADR-004`, `ADR-006` | `AuditEventDoc`, `teacher_review_status` |
| `006` | Class Insights | `REQ-COH-001`, `REQ-COH-002` | `ADR-005` (Cohort Intelligence) | `ClassInsightDoc`, `ReteachingPlanDoc` |
