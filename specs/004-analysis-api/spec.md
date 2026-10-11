# Specification: 004 — Assessment Analysis REST API & Dispatch

**Specification ID:** SPEC-004
**Module:** `services/api/`
**Related Documents:** [`api-contracts.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/api-contracts.md), [`security-threat-model.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/review/security-threat-model.md)
**Guided by Skills:** `sign-in-with-google-web`, `google-cloud-solution-n-tier-serverless-web-app`
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

Educators and demo evaluators need a reliable backend API to set up math assessments, inspect student responses, launch batch analyses, and monitor processing progress.

`004-analysis-api` implements the FastAPI backend. In local development, it provides session authentication, tenant-scoped data queries, signed upload simulation, and an **inline asynchronous dispatch adapter** that triggers worker analysis jobs without requiring Google Cloud Tasks or cloud infrastructure.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-004.1 (Authentication & Session)**: Support Google Identity Services ID token verification at `POST /api/v1/auth/google`. In local demo mode, support a sandboxed test session for teacher `usr_sarah_lim`. Sets `HttpOnly; Secure; SameSite=Lax` session cookie (`__session`).
- **FR-004.2 (CSRF Protection)**: State mutations (`POST`, `PUT`, `DELETE`) require the custom header `X-Requested-With: ClassLens` and double-submit `csrf_token` cookie.
- **FR-004.3 (Assessment Management)**: CRUD operations for `/api/v1/assessments` and `/api/v1/assessments/{id}/demo-import` (imports curated Problem #1065658).
- **FR-004.4 (Batch Analysis Trigger)**: `POST /api/v1/assessments/{id}/analyze` launches analysis. Accepts an `idempotency_key` and dispatches individual response jobs.
- **FR-004.5 (Progress & Status Polling)**: `GET /api/v1/assessments/{id}/status` returns total, completed, and failed counts.
- **FR-004.6 (Local Inline Dispatch Adapter)**: In offline dev mode (`QUEUE_TYPE=inline`), dispatches worker tasks asynchronously using Python `asyncio.create_task` or a background thread pool, perfectly simulating Cloud Tasks webhook execution.

### Non-Functional Requirements
- **NFR-004.1 (Latency)**: API CRUD responses return in P95 $\le 200\text{ ms}$.
- **NFR-004.2 (Zero Cloud Standing Cost)**: Uses in-memory / local Firestore emulator persistence during local development.

---

## 3. Typed Contracts
Matches the approved [`api-contracts.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/api-contracts.md).
