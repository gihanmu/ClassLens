# API Contracts & OpenAPI Specification — ClassLens

**Document ID:** ARC-API-004
**Version:** 1.2.0
**Date:** 2026-10-11

---

### Changelog (v1.2.0 — Final Technical-Validity Revision)
- Formalized Cloud Tasks at-least-once delivery handling and application-level idempotency contracts in `/tasks/analyze-response`.
- Added `/tasks/aggregate-cohort` webhook contract for decoupled cohort intelligence synthesis.
- Clarified signed upload URL endpoint targeting `raw_quarantine/` and updated CSRF protection contracts.
- Aligned service identities (`sa-classlens-tasks`) and OIDC audience verification.

---

## 1. Authentication & Authorization Matrix

All external API endpoints are prefixed with `/api/v1` and require an authenticated session (`Bearer <token>` or encrypted `__session` HTTP-only cookie), except the health check and public demo read endpoint.

State-changing external endpoints (`POST`, `PUT`, `DELETE`) require the custom header `X-Requested-With: ClassLens` and validate a double-submit `csrf_token` cookie.

The internal worker endpoints `/tasks/analyze-response` and `/tasks/aggregate-cohort` are IAM-authenticated and require a Google Cloud OIDC token minted for `sa-classlens-tasks`.

| Endpoint | Method | Ingress / Scope | Allowed Roles / Identities | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/auth/google` | `POST` | Public Edge | Public | Exchange Google ID token for session cookie + CSRF token |
| `/auth/logout` | `POST` | Public Edge | Authenticated | Invalidate user session cookie |
| `/classes` | `GET`, `POST` | Public Edge | `teacher`, `admin` | List or create classes |
| `/assessments` | `GET`, `POST` | Public Edge | `teacher`, `admin` | List or create assessments |
| `/assessments/{id}` | `GET`, `PUT`, `DELETE`| Public Edge | `teacher`, `admin` | Get, update, or archive assessment |
| `/assessments/{id}/uploads/sign` | `POST` | Public Edge | `teacher` | Request V4 signed GCS upload URLs targeted to `raw_quarantine/` |
| `/assessments/{id}/demo-import` | `POST` | Public Edge | `teacher`, `demo_observer` | Import curated DrawEduMath problem #1065658 |
| `/assessments/{id}/analyze` | `POST` | Public Edge | `teacher` | Enqueue asynchronous batch analysis via Cloud Tasks |
| `/assessments/{id}/status` | `GET` | Public Edge | Authenticated | Poll job state and progress counts |
| `/assessments/{id}/responses` | `GET` | Public Edge | Authenticated | List student responses with diagnostic summary |
| `/responses/{id}` | `GET` | Public Edge | Authenticated | Get full analysis record and signed image preview URL |
| `/responses/{id}/review` | `PUT` | Public Edge | `teacher`, `admin` | Submit teacher review approval or override |
| `/assessments/{id}/insights` | `GET` | Public Edge | Authenticated | Get aggregated class misconception dashboard data |
| `/assessments/{id}/reteach` | `POST`, `PUT` | Public Edge | `teacher` | Generate or edit reteaching plan & exit ticket |
| `/reports/{assessment_id}/export` | `GET` | Public Edge | `teacher`, `admin` | Export PDF summary or CSV data dump |
| `/tasks/analyze-response` | `POST` | **IAM Worker Only** | `sa-classlens-tasks` (OIDC Token) | Cloud Tasks worker webhook to analyze single response |
| `/tasks/aggregate-cohort` | `POST` | **IAM Worker Only** | `sa-classlens-tasks` (OIDC Token) | Cloud Tasks worker webhook to run cohort intelligence synthesis |

---

## 2. Internal Cloud Tasks Worker Contracts

### 2.1 `POST /tasks/analyze-response`
Invoked exclusively by Google Cloud Tasks on the `services/worker` Cloud Run container.

- **Headers**:
  - `Authorization`: `Bearer <OIDC_TOKEN>` (Signed by `accounts.google.com`, Audience: `https://classlens-worker-<hash>-<region>.a.run.app`)
  - `Content-Type`: `application/json`
  - `X-CloudTasks-QueueName`: `classlens-analysis-queue`
  - `X-CloudTasks-TaskRetryCount`: `0`
- **Request Body**:
```json
{
  "job_id": "job_98a7c12f-9812",
  "assessment_id": "asm_1065658",
  "response_id": "resp_04255753",
  "attempt_number": 1,
  "idempotency_key": "asm_1065658_resp_04255753_v1"
}
```
- **Responses**:
  - `200 OK`:
    - Success: lease acquired, image validated and analyzed, `analysis_version` saved, progress counter incremented.
    - Idempotent duplicate: response status is already `COMPLETED` or actively held under valid lease. Worker acknowledges task immediately to prevent duplicate runs.
  - `422 Unprocessable`: Image corrupted or permanently unreadable (recorded in DB as `FAILED_INVALID_FORMAT`, task acknowledged, no retry).
  - `500 / 503`: Transient error (Worker releases lock; Cloud Tasks retries up to 3 times with exponential backoff).

---

### 2.2 `POST /tasks/aggregate-cohort`
Invoked by Cloud Tasks after all individual student response tasks reach terminal states.

- **Headers**:
  - `Authorization`: `Bearer <OIDC_TOKEN>` (Audience: Worker URL)
  - `Content-Type`: `application/json`
- **Request Body**:
```json
{
  "job_id": "job_98a7c12f-9812",
  "assessment_id": "asm_1065658",
  "aggregation_version": "v1_20261011_001"
}
```
- **Responses**:
  - `200 OK`: Deterministic cohort stats computed, `CohortIntelligenceAgent` synthesizes narrative and exit tickets, stored in `insights/` collection.

---

## 3. Core Public API Endpoint Contracts

### 3.1 Google Identity Services Authentication
`POST /api/v1/auth/google`
- **Request Body**:
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",
  "g_csrf_token": "csrf_token_value"
}
```
- **Response (`200 OK`)**:
```json
{
  "user": {
    "id": "usr_sarah_lim",
    "email": "sarah.lim@moe.edu.sg",
    "name": "Sarah Lim",
    "role": "teacher",
    "organization_id": "org_cedar_sec"
  },
  "csrf_token": "csrf_token_value"
}
```
*(Sets cookies: `__session=<token>; Path=/; Secure; HttpOnly; SameSite=Lax` and `csrf_token=<token>; Path=/; Secure; SameSite=Lax`)*

### 3.2 Request Upload Signed URLs
`POST /api/v1/assessments/{assessment_id}/uploads/sign`
- **Request Body**:
```json
{
  "files": [
    {"filename": "student_01.jpg", "content_type": "image/jpeg", "file_size_bytes": 1048576}
  ]
}
```
- **Response (`200 OK`)**:
```json
{
  "uploads": [
    {
      "response_id": "resp_04255753",
      "upload_url": "https://storage.googleapis.com/classlens-quarantine/raw_quarantine/asm_1065658/resp_04255753.bin?X-Goog-Algorithm=...",
      "expires_at": "2026-10-11T12:15:00Z",
      "quarantine_path": "raw_quarantine/asm_1065658/resp_04255753.bin"
    }
  ]
}
```

### 3.3 Launch Batch Analysis
`POST /api/v1/assessments/{assessment_id}/analyze`
- **Headers**:
  - `X-Requested-With: ClassLens`
- **Request Body**:
```json
{
  "force_reanalyze": false,
  "idempotency_key": "user_req_20261011_001"
}
```
- **Response (`202 Accepted`)**:
```json
{
  "job_id": "job_98a7c12f-9812",
  "assessment_id": "asm_1065658",
  "status": "processing",
  "total_items": 13,
  "completed_items": 0,
  "failed_items": 0,
  "created_at": "2026-10-11T12:00:00Z"
}
```

---

## 4. Error Handling & Standard Codes

RFC 7807 Problem Details returned on non-2xx responses:

```json
{
  "type": "https://classlens.app/errors/quota-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Daily assessment limit of 5 assessments exceeded for this demo account.",
  "instance": "/api/v1/assessments/asm_1065658/analyze",
  "code": "DAILY_QUOTA_EXCEEDED"
}
```
