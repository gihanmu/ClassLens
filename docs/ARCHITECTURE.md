# ClassLens System Architecture

## Overview

ClassLens is an AI-powered diagnostic platform designed for K-12 mathematics educators. It analyzes handwritten student worksheets, verifies mathematical reasoning with symbolic computation, diagnoses deep-seated misconceptions, aggregates cohort-wide patterns, and delivers targeted instructional action plans.

```
                              +---------------------------------------+
                              |         HTTPS Load Balancer           |
                              |           (Google Cloud)              |
                              +-------------------+-------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                   Path: /* (Default)                                Path: /api/*, /health
                         v                                                 v
        +---------------------------------+               +---------------------------------+
        |  Next.js Frontend (Cloud Run)   |               |   FastAPI Backend (Cloud Run)   |
        |  - React 18, Tailwind CSS       |               |   - Python 3.12, Uvicorn        |
        |  - Standalone Node.js Runner    |               |   - Non-root unprivileged user   |
        |  - Tenant-aware session context |               |   - Strict CORS & Security hdrs |
        +---------------------------------+               +----------------+----------------+
                                                                           |
                         +-------------------------------------------------+------------------------+
                         |                                                 |                        |
                         v                                                 v                        v
        +---------------------------------+               +---------------------------------+  +----+--------------------+
        |  Vertex AI (Gemini 1.5 Flash)   |               |    Symbolic Math Verifier       |  |   Persistence Layer     |
        |  - Multimodal Vision Intake     |               |    - SymPy Engine               |  | - SQLite / Cloud SQL    |
        |  - Structured Step Extraction   |               |    - Task Router (Int / Frac)   |  | - FileStorageBackend    |
        |  - Zero Hallucination Pipeline  |               |    - Misconception Taxonomy     |  |   (Local / GCS Bucket)  |
        +---------------------------------+               +---------------------------------+  +-------------------------+
```

---

## Architectural Principles

1. **Separation of Perception and Verification**: Gemini 1.5 Flash extracts handwritten mathematical expressions and student diagrams, while deterministic Python symbolic execution (SymPy) evaluates mathematical correctness. Large language models never make unverified pass/fail grading determinations.
2. **Teacher-in-the-Loop Authority**: AI findings are preliminary diagnostic recommendations. Teachers can review student evidence, inspect side-by-side worksheet crops, and override AI diagnoses. All overrides are tracked and preserved with full audit history.
3. **Evidence Sufficiency Enforcement**: If student handwriting is ambiguous, partially cut off, or lacks step-by-step reasoning, ClassLens classifies the submission as `Insufficient Evidence` requiring review rather than making speculative guesses.
4. **Tenant Isolation**: All database queries, uploads, and AI analysis requests are scoped by `org_id`. Cross-tenant data leakage is structurally prevented at both the repository and router layers.
5. **Zero-Trust Infrastructure**: All container workloads run as unprivileged non-root users (`nextjs:nodejs` UID 1001, `appuser` UID 10001). Cloud Run services enforce `ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"`, ensuring backend services cannot be addressed directly over public URLs.

---

## Core Components

### 1. Web Frontend (`apps/web`)
- **Framework**: Next.js 14 (App Router) in `output: "standalone"` mode.
- **Styling**: Tailwind CSS with custom design tokens adhering to high-contrast educational UI principles.
- **Views**:
  - `Dashboard`: Cohort overview, mastery distribution, flagged students.
  - `Responses`: Grid of student submissions with image thumbnails, confidence indicators, and filterable diagnostic status.
  - `Insights`: Evidence-grounded cohort analytics and misconception prevalence charts.
  - `Recommendations`: Assessment-specific differentiated teaching action cards with traceable student rosters.
  - `Resources`: Diagnostic guides, exit ticket generators, and instructional aids.
  - `Assessments`: Assessment creator, rubric manager, and worksheet intake interface.

### 2. API Backend (`services/api`)
- **Framework**: FastAPI (ASGI) on Python 3.12 running under Uvicorn.
- **Middleware**:
  - `CorrelationIdMiddleware`: Generates or propagates `X-Correlation-ID` on all incoming requests.
  - `SecurityHeadersMiddleware`: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
  - `LoginRateLimiter`: Sliding-window limiter on `/api/v1/auth/login` (5 failed attempts/minute per IP/account).
- **Domain Modules**:
  - `routers/auth.py`: Session management with Argon2id password hashing and HTTP-only cookies.
  - `routers/assessments.py`: Assessment definition, rubric configuration, and batch upload handling.
  - `routers/responses.py`: Student submission retrieval, image delivery, and teacher review overrides.
  - `routers/dashboard.py`: Cohort summary metrics and flagged student aggregation.
  - `routers/insights.py`: Evidence-grounded misconception distribution.
  - `routers/recommendations.py`: Dynamic intervention synthesis isolated by assessment topic.

### 3. Diagnostic & Verification Engine
- **Task Router** (`services/api/analysis/task_router.py`): Inspects assessment prompt text and mathematical criteria to select the appropriate domain verifier (e.g., `INTEGER_OPERATIONS_NUMBER_LINE` vs `FRACTION_DIVISION`).
- **Multimodal Perception**:
  - Vertex AI Gemini 1.5 Flash (`gemini-1.5-flash-001` or `gemini-1.5-flash-002`) receives image bytes and structured prompt instructions.
  - Outputs structured JSON conforming strictly to `WorksheetAnalysisResult`.
- **Deterministic Math Verifier** (`services/api/analysis/math_verifier.py` & `fraction_verifier.py`):
  - Evaluates intermediate steps, directional hops, sign changes, and common denominators using SymPy.
  - Maps anomalies to standardized misconception codes (`MISC-DIR-INV`, `MISC-MAG-COUNT`, `MISC-ARITH-OFF-BY-ONE`, `MISC-FRAC-DIV-INVERT-WRONG`, etc.).

### 4. Storage & Persistence
- **Relational Data**: Abstracted repository pattern supporting SQLite (`classlens.db`) for local evaluation and PostgreSQL (Cloud SQL) for multi-instance production.
- **Worksheet Image Storage** (`services/api/repository/file_storage.py`):
  - Interface `FileStorageBackend`.
  - `LocalFilesystemStorage`: Stores images in `data/uploads/{org_id}/{assessment_id}/`.
  - `GoogleCloudStorageBackend`: Stores images in a private Google Cloud Storage bucket (`gs://{CLASSLENS_GCS_BUCKET}/uploads/...`) with IAM Uniform Bucket-Level Access.
