# Acceptance Tests: 004 — Assessment Analysis REST API & Dispatch

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/004-analysis-api/spec.md)
**Test Suite Path:** `tests/integration/test_api_endpoints.py`

---

## 1. Test Matrix

| Test Case ID | Endpoint & Method | Preconditions / Payload | Expected Status | Verification Criterion |
| :--- | :--- | :--- | :--- | :--- |
| **TC-004.01** | `POST /api/v1/auth/google` | Valid demo login credential | `200 OK` | Returns user profile; sets `__session` and `csrf_token` cookies. |
| **TC-004.02** | `POST /api/v1/assessments` | Authenticated session; CSRF header missing | `403 Forbidden` | Rejects mutation lacking `X-Requested-With` header. |
| **TC-004.03** | `POST /api/v1/assessments/{id}/demo-import` | Authenticated session; valid CSRF header | `200 OK` | Loads 13 response records for Problem #1065658 into repository. |
| **TC-004.04** | `POST /api/v1/assessments/{id}/analyze` | Valid assessment; `idempotency_key = "test_01"` | `202 Accepted` | Returns `job_id`; spawns background execution. |
| **TC-004.05** | `GET /api/v1/assessments/{id}/status` | Polled 1s after analysis dispatch | `200 OK` | Shows `completed_items == 13`, `failed_items == 0`. |
| **TC-004.06** | `GET /api/v1/responses/{id}` | Completed response ID | `200 OK` | Returns full `StudentResponseAnalysis` with observations and steps. |

---

## 2. Verification Execution Command
```bash
pytest tests/integration/test_api_endpoints.py -v
```
- **Acceptance Gate**: 100% pass rate in $< 2.0$ seconds with zero cloud dependencies.
