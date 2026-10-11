# Implementation Tasks: 004 — Assessment Analysis REST API & Dispatch

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/004-analysis-api/spec.md)
**Status:** Ready for Implementation upon Spec Approval

---

## Task List

- [x] **TASK-004.1**: Initialize `services/api/` package with FastAPI, Pydantic Settings, and CORS middleware in `main.py`.
- [x] **TASK-004.2**: Implement session cookie handling, CSRF token validation, and demo sandbox login in `auth/`.
- [x] **TASK-004.3**: Implement in-memory repository `memory_repo.py` supporting organizations, assessments, responses, and audit events.
- [x] **TASK-004.4**: Implement `InlineDispatcher` providing non-blocking asynchronous dispatch for local offline development.
- [x] **TASK-004.5**: Implement router endpoints in `routers/assessments.py`:
  - `POST /api/v1/assessments`
  - `POST /api/v1/assessments/{id}/demo-import`
  - `POST /api/v1/assessments/{id}/analyze`
  - `GET /api/v1/assessments/{id}/status`
- [x] **TASK-004.6**: Implement response detail endpoints in `routers/responses.py`:
  - `GET /api/v1/responses/{id}`
- [x] **TASK-004.7**: Author integration test suite in `tests/integration/test_api_endpoints.py` testing auth, assessment creation, demo import, and async batch analysis.
