# Functional Requirements Specification — ClassLens

**Document ID:** REQ-FUN-003
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Aligned AUTH-001 with Google Identity Services (GIS) and backend ID token verification.
- Reconciled ORCH-001 to use Google Cloud Tasks durable queue dispatch to private Cloud Run worker.
- Replaced SQL relational database references with Firestore Native Mode collection paths.
- Updated DEMO-001 & DEMO-002 to reference verified problem `1065658`.
- Added application-level quota circuit breaker requirements (ORCH-004).

---

## 1. Identity, Authentication & Multi-Tenancy (AUTH)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUTH-001** | P0 | Google Identity Services (GIS) Sign-In for educators. | None | `POST /api/v1/auth/google`<br>Verifies Google ID token using Google Auth library; sets session cookie (`HttpOnly; Secure; SameSite=Lax`). | User authenticates with Google account; backend verifies token signature and audience; provisions profile in `users` collection. |
| **AUTH-002** | P0 | Role-Based Access Control (RBAC). Roles: `teacher`, `admin`, `reviewer`, `demo_observer`. | AUTH-001 | User claims verified on every endpoint; 403 Forbidden on role mismatch. | Demo user cannot mutate data; teacher can only mutate owned classes; admin manages org members. |
| **AUTH-003** | P0 | Multi-tenant organization isolation. | AUTH-002 | `organization_id` partitioned on all Firestore collections and GCS prefixes. | No user can query or access assets belonging to another organization (tested via IDOR suite). |
| **AUTH-004** | P1 | Token expiration and safe logout. | AUTH-001 | Short-lived access session (60 min), explicit logout endpoint. | Logging out clears session cookie and terminates active session. |

---

## 2. Organization, Class & Student Management (ORG / STU)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ORG-001** | P0 | Class section creation and management. | AUTH-002 | `POST /api/v1/classes`, `GET /api/v1/classes`<br>Document: `classes/{classId}` | Teacher can create a class (e.g., "Sec 1 Matheletes") and view active class rosters. |
| **STU-001** | P0 | Pseudonymous student labeling. | ORG-001 | `pseudonymous_student_id` (e.g. `STU-001`, `Student-A`) scoped to class. | Zero student PII (no real names, IC numbers, or student emails) required or stored. |
| **STU-002** | P0 | DrawEduMath student isolation guarantee. | STU-001 | DrawEduMath rows mapped strictly as response instances, not continuous student identities. | Dataset problem responses are never artificially linked across problems or presented as a real class roster. |

---

## 3. Question and Rubric Authoring (ASM / QST)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ASM-001** | P0 | Assessment wizard and metadata creation. | ORG-001 | `POST /api/v1/assessments`<br>Document: `assessments/{assessmentId}` | Teacher enters title, topic ("Integers"), grade level ("Grade 7"), and date. |
| **QST-001** | P0 | Mathematical question and LaTeX authoring. | ASM-001 | `question_text`, `latex_expression`, `diagram_type` in assessment doc. | Renders rich text and KaTeX math formulas in real-time preview. |
| **QST-002** | P0 | Multi-method rubric specification. | QST-001 | `canonical_answer`, `accepted_methods[]`, `step_rules[]` | Teacher can define canonical steps AND alternative valid methods (e.g. direct jump vs hop from 0). |
| **QST-003** | P1 | Reference diagrams and assets. | QST-001 | Reference number line image uploaded to GCS. | AI compares student diagrams against reference coordinates. |

---

## 4. Image Intake & Secure Storage (INTK)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **INTK-001** | P0 | Multi-file batch upload (drag & drop). | ASM-001 | Signed V4 GCS upload URL issued by API. | Teacher can select up to 30 images simultaneously; client shows per-file upload progress. |
| **INTK-002** | P0 | File signature, size, and decompression bomb validation. | INTK-001 | Server-side `python-magic` check; Pillow decompression bomb limit (`MAX_IMAGE_PIXELS=16M`). | Reject invalid MIME types, scripts, and oversize bombs with HTTP 422 Unprocessable. |
| **INTK-003** | P0 | Client-side and server-side image rotation & preprocessing. | INTK-001 | 90°/180°/270° orientation transform; EXIF stripping via PIL. | Rotated preview saved correctly; EXIF metadata completely stripped before persistence. |
| **INTK-004** | P0 | Private Cloud Storage persistence. | INTK-001 | GCS bucket configured with Uniform Bucket-Level Access, private-only. | Images only accessible via short-lived signed URLs (15 min TTL) generated for authorized teachers. |

---

## 5. Dataset Explorer & Curated Demo Importer (DEMO)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEMO-001** | P0 | Local DrawEduMath metadata indexing. | None | Metadata parsed from `./dataset/` without modifying raw files. | System reads 188 problems and metadata on startup without copying 2,030 images. |
| **DEMO-002** | P0 | Curated Problem #1065658 vertical slice. | DEMO-001 | Assessment initialized with 13 responses from `dataset/problem_1065658`. | Demo assessment instantly ready for evaluation without external API calls or image leakage. |
| **DEMO-003** | P0 | Human vs. Synthetic annotation provenance. | DEMO-001 | Explicit flag `annotation_source: human_teacher \| synthetic_gpt4o \| synthetic_claude`. | Synthetic QA pairs are never displayed as ground truth or used in evaluation. |

---

## 6. Asynchronous Analysis Orchestration (ORCH)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ORCH-001** | P0 | Asynchronous job creation & Cloud Tasks dispatch. | INTK-001 | `POST /api/v1/assessments/{id}/analyze`<br>Enqueues tasks in Cloud Tasks queue targeting private worker. | Analysis returns `202 Accepted` with `job_id`; UI polls status or listens to SSE. |
| **ORCH-002** | P0 | Task-level idempotency and failure isolation. | ORCH-001 | Cloud Tasks task name deduplication (`task_name = resp_{id}_{version}`). | Retrying response 3 does not duplicate processing; failed item marked `failed`. |
| **ORCH-003** | P0 | Bounded concurrency & rate limit backoff. | ORCH-001 | Cloud Tasks `max_concurrent_dispatches: 5`; exponential backoff on 429 Vertex AI errors. | Reaches safety cutoff without exceeding Vertex AI quotas or blowing budgets. |
| **ORCH-004** | P0 | Application-level spending circuit breaker. | ORCH-001 | Daily limit of 5 assessments per teacher account; global `INFERENCE_ENABLED` flag. | System prevents runaway automated testing or denial-of-wallet attacks. |

---

## 7. Multimodal Interpretation & Verification (AI / MATH)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI-001** | P0 | Multimodal transcription of handwriting and diagrams. | ORCH-001 | Vertex AI Gemini 1.5/2.0 Flash with strict Pydantic JSON schema. | Extracts tick marks, start points, arrow directions, end points, and intermediate steps. |
| **AI-002** | P0 | Visual quality classification & explicit abstention. | AI-001 | Output status: `clear \| faint \| blurred \| rotated \| unreadable`. | If image is unreadable, returns `reasoning_status: undetermined` without inventing steps. |
| **MATH-001** | P0 | Deterministic SymPy arithmetic checker. | AI-001 | Python tool executing SymPy checks on extracted expressions. | Evaluates arithmetic correctness independently of LLM reasoning. |
| **MATH-002** | P0 | Deterministic number line movement validator. | AI-001 | Python tool calculating arrow displacements: $\Delta x = x_{end} - x_{start}$. | Validates whether arrows match addends (e.g. arrow from -6 to 5 is +11, not +12). |
| **AI-003** | P0 | First supported error localization. | MATH-001, MATH-002 | Sets `first_supported_error` with step index, observed value, and expected value. | Successfully localizes the exact step where calculation diverged. |
| **AI-004** | P0 | Standardized pedagogical misconception classification. | AI-003 | Maps error to taxonomy ID (e.g. `MISC-NUM-DIR-REVERSE`, `MISC-ARITH-OFF-BY-ONE`). | Associates error with taxonomy code, description, and confidence rating. |

---

## 8. Class Misconception Aggregation & Reteaching (AGGR / PLAN)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AGGR-001** | P0 | Deterministic class-wide error aggregation. | AI-004 | Python statistical service computing cohort percentages. | Total responses, correct count, misconception breakdown calculated strictly in code. |
| **AGGR-002** | P0 | Clear denominator and status disclosure. | AGGR-001 | Explicit breakdown: AI-proposed vs. Teacher-confirmed. | UI displays: "3 of 13 students (23.1%) — Confirmed by teacher: 2, AI-proposed: 1". |
| **PLAN-001** | P0 | Grounded reteaching strategy generator. | AGGR-001 | Python Teaching Strategy Agent prompting Gemini with aggregated patterns. | Generates small-group intervention suggestions linked directly to observed error patterns. |
| **PLAN-002** | P0 | Formative exit ticket generator. | PLAN-001 | 3 targeted assessment items targeting identified misconceptions. | Renders printable/exportable exit ticket with SymPy-verified teacher answer key. |

---

## 9. Teacher Review Workflow & Auditability (REV / AUDIT)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REV-001** | P0 | Side-by-side response inspection viewer. | AI-001 | Dual-pane layout: zoomable image + structured reasoning cards. | Pan, zoom, and rotate original handwriting alongside step-by-step breakdown. |
| **REV-002** | P0 | Human-in-the-loop review actions. | REV-001 | `PUT /api/v1/responses/{id}/review`<br>Actions: `approved_as_is`, `overridden_correct`, etc. | Teacher can override correctness or misconception label and enter custom notes. |
| **AUDIT-001**| P0 | Audit trail for overrides and data mutations. | REV-002 | `audit_events` collection recording user ID, timestamp, old value, new value, reason. | All teacher edits are preserved with full history without silently retraining models. |
| **REV-003** | P1 | Safe re-analysis without overwriting human edits. | REV-002 | Versioned analysis records (`version: 1, 2...`). | Re-running AI analysis creates a new version; teacher overrides remain intact. |

---

## 10. Dashboard, Reports & Evaluation Workbench (DASH / EVAL)

| Req ID | Priority | Description | Dependencies | API & Data Implications | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DASH-001**| P0 | Responsive teacher dashboard. | AGGR-001 | Accessible charts (Recharts / Accessible SVG) + tabular data. | Fully usable on desktop, tablet, and mobile; accessible with screen readers. |
| **DASH-002**| P1 | Exportable class summary report (PDF/CSV). | DASH-001 | PDF generation endpoint; CSV download. | Exports aggregated summary with "AI-assisted / Teacher-verified" badges; no student PII leaked. |
| **EVAL-001**| P0 | Automated AI quality evaluation suite. | AI-001..AI-004 | Pytest evaluation runner against provisional Problem #1065658 set. | Outputs precision, recall, and abstention rate without live network dependencies. |
