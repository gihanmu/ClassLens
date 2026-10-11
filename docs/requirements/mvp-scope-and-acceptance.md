# MVP Scope and Acceptance Criteria — ClassLens

**Document ID:** REQ-SCP-005
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Explicitly anchored P0 vertical slice to DrawEduMath problem `1065658` (13 student responses in `dataset/problem_1065658/`).
- Resolved datastore specification: Firestore Native Mode replaces Cloud SQL for MVP.
- Retracted unverified "multi-expert consensus" claim in Definition of Done; mandated double-blind adjudication protocol.
- Clarified that demo data represents isolated response images rather than a real continuous class roster.

---

## 1. MVP vs. Future Scope Matrix

| Capability Area | Phase 1–2: Hackathon MVP (P0) | Phase 3–4: Cloud & Org (P1) | Phase 5+: Production Scale (P2) |
| :--- | :--- | :--- | :--- |
| **Problem Types** | Single multi-step integer arithmetic & number line problems (Problem #1065658). | Multi-question worksheets, fractions, linear algebra. | Geometry with protractor diagrams, word problems. |
| **Intake Modality** | Photo/scan upload (JPG, PNG, WebP) + Curated DrawEduMath demo loader. | Multi-page PDF splitting, mobile live camera stream. | Google Classroom batch assignment sync. |
| **Authentication** | Google Identity Services (GIS) OIDC + Demo read-only observer mode. | Multi-tenant RBAC with school admin provisioning. | SAML SSO for MOE / Enterprise School Portals. |
| **Datastore** | Google Cloud Firestore Native Mode (Serverless, Pydantic models). | Firestore with automated BigQuery export. | Spanner / Enterprise relational warehouse. |
| **AI Orchestration** | Cloud Tasks + Private Cloud Run Worker (Google ADK multi-agent pipeline). | Cloud Tasks with auto-dead-letter alerting. | Dedicated Vertex AI Agent Engine with custom fine-tuning. |
| **Math Checking** | SymPy evaluation + Number line displacement calculator. | Fraction & algebraic simplification validator. | Automated step-by-step theorem prover. |
| **Teacher Review** | Full side-by-side inspection, approve/override, audit trail. | Batch approvals, custom rubric tags. | Longitudinal student learning trajectory tracking. |
| **Reporting & Export** | Interactive Web Dashboard + Formative Reteaching Action Cards. | Exportable PDF summary + CSV data dump. | Automated LMS gradebook sync. |
| **Evaluation** | Adjudicated 13-response evaluation suite for Problem #1065658. | 50-response multi-problem benchmark suite. | Continuous evaluation flywheel with active learning. |

---

## 2. MVP Definition of Done (DoD)

A feature is considered complete for the MVP only when:
1. **Deterministic Verification Tested**: All mathematical and displacement logic is verified via deterministic Python unit tests (`SymPyChecker`, `NumberLineDisplacementCalculator`) with $100\%$ pass rate on unit test fixtures.
2. **Type Safety Enforced**: Data models adhere to Pydantic v2 schemas on Python and generated TypeScript contracts on Next.js.
3. **No Hallucination Fallback**: Images with ambiguous or unreadable handwriting explicitly return `needs_teacher_review: true` with `reasoning_status: undetermined`.
4. **No Public PII Exposure**: Responses are de-identified with pseudonymous IDs (`Student-01`); raw bucket URLs are never rendered to unauthorized clients.
5. **Human Review Loop Active**: A teacher can click to override any AI finding, and the override updates the class aggregate in an atomic Firestore transaction.
6. **Zero Silent Retraining**: Teacher corrections are logged to an audit table and golden evaluation pool, never piped directly to automated model retraining.
7. **End-to-End Vertical Slice Working**: From assessment creation to image intake, AI diagnosis, class aggregation, teacher review, and reteaching plan generation in a single seamless flow.
8. **Evaluation Ground Truth Adjudicated**: Benchmark results are evaluated against human-adjudicated labels, explicitly disclaiming synthetic QA leakage.
