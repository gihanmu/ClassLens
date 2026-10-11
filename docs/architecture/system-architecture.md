# System Architecture Specification — ClassLens

**Document ID:** ARC-SYS-001
**Version:** 1.2.0
**Date:** 2026-10-11

---

### Changelog (v1.2.0 — Final Technical-Validity Revision)
- Designated **Vertex AI Gemini 3.8 Flash (`gemini-3.8-flash`) in `asia-southeast1`** as the primary workhorse model for multimodal perception, reasoning, and cohort synthesis.
- Reconciled worker ingress topology: `--ingress all` with `--no-allow-unauthenticated` (IAM-authenticated private access over Google's backbone, invokable exclusively by Cloud Tasks using OIDC tokens).
- Standardized multi-agent inventory to **1 Deterministic Python Service + 5 Bounded Google ADK Agents**.
- Incorporated signed upload quarantine architecture (`raw_quarantine/` -> post-upload validation -> `validated_images/`).
- Updated monthly cost scenarios to reflect Gemini 3.8 Flash introductory rate cards and Singapore Cloud Storage pricing.

---

## 1. Architectural Philosophy & Principles

The ClassLens architecture is guided by five core architectural tenets:
1. **Python Owns All AI Logic**: All multimodal parsing, image preprocessing, prompt orchestration, SymPy verification, agent decision paths, and cohort statistics reside exclusively in Python. TypeScript is strictly limited to UI, presentation, and thin proxy communication.
2. **Deterministic Tools Before LLM Guesswork**: Wherever mathematical correctness, arithmetic evaluation, interval measurement, or aggregation can be computed deterministically, it is executed by unit-tested Python code rather than generative model inference.
3. **Decoupled Asynchronous Processing**: Image intake and agent analysis are decoupled via Cloud Tasks and a private Cloud Run worker, preventing HTTP request timeouts and isolating transient failures.
4. **Zero-Trust Multi-Tier Security**: Private Cloud Storage, signed URLs with post-upload validation, least-privilege IAM service accounts, and tenant-scoped database isolation ensure zero leakage of student work.
5. **Serverless Simplicity**: Managed GCP serverless infrastructure (Cloud Run, Cloud Storage, Firestore Native, Cloud Tasks) minimizes operational overhead and ensures true zero baseline compute cost when idle.

---

## 2. High-Level System Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer (Educator & Observer)"]
        Browser["Teacher Browser / Mobile Device<br>(Next.js 15 / React 19 / Tailwind / KaTeX)"]
        JudgeBrowser["Demo Observer Browser<br>(Read-Only Sandbox)"]
    end

    subgraph EdgeLayer ["Edge & Ingress Boundary (Public Cloud Run)"]
        WebFront["Frontend Web Container (apps/web)<br>(Next.js App Router - TypeScript, Port 3000)"]
        APIServer["Backend API Container (services/api)<br>(FastAPI - Python 3.12, Port 8000)<br>CORS Whitelist + GIS Cookie Auth + CSRF Verification"]
    end

    subgraph AsyncTier ["Asynchronous Worker Tier (Cloud Run & Cloud Tasks)"]
        Queue["Cloud Tasks Regional Queue<br>(classlens-analysis-queue, max_concurrent: 5)"]
        AIWorker["AI Orchestration Worker (services/worker)<br>(Python Google ADK Runtime, Port 8080)<br>Ingress: all | Auth: OIDC sa-classlens-tasks"]
    end

    subgraph StorageTier ["Data & Storage Tier (Google Cloud)"]
        GCS_Quarantine["Private GCS: raw_quarantine/<br>(Uniform Access, AES-256, 30d Lifecycle)"]
        GCS_Validated["Private GCS: validated_images/<br>(Sanitized, EXIF-stripped, 30d Lifecycle)"]
        FirestoreDB[("Firestore Native Database<br>(Serverless Document Store, Free Tier Eligible)<br>Tenant-Partitioned Collections")]
    end

    subgraph IntelligenceTier ["Google Vertex AI & Deterministic Engines"]
        VertexGemini["Vertex AI Gemini 3.8 Flash<br>(Multimodal Vision & Reasoning, asia-southeast1)"]
        SymPyEngine["Deterministic SymPy Engine<br>(Exact Rational Arithmetic Checker)"]
        NumberLineEngine["Deterministic Geometry Engine<br>(Arrow & Vector Displacement Calculator)"]
    end

    %% Interactions
    Browser -->|HTTPS TLS 1.3| WebFront
    Browser -->|HTTPS API with Session Cookie & CSRF Header| APIServer
    Browser -.->|Direct Signed V4 PUT (15m TTL)| GCS_Quarantine
    JudgeBrowser -->|HTTPS Read-Only| WebFront

    WebFront -->|Typed BFF API Requests| APIServer
    APIServer -->|Generate V4 Upload URL| GCS_Quarantine
    APIServer -->|Enqueue Analysis Task with OIDC Token| Queue
    Queue -->|HTTP POST with OIDC Bearer Token| AIWorker

    APIServer <-->|CRUD Entity Documents| FirestoreDB
    AIWorker <-->|Atomic Lease Claim & Status Update| FirestoreDB
    AIWorker -->|Validate & Sanitize| GCS_Quarantine
    AIWorker -->|Store Normalized Image| GCS_Validated
    AIWorker -->|Multimodal Extraction via ADC (Pre-Checked)| VertexGemini
    AIWorker -->|Step Verification| SymPyEngine
    AIWorker -->|Displacement Verification| NumberLineEngine
```

---

## 3. Component Details & Technology Choices

### 3.1 Web Frontend (`apps/web`)
- **Technology**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, KaTeX math formatting.
- **Role**: Presentation, user session management, accessible interactive dashboards, dual-pane image viewer (zoom/pan/rotate), and teacher review forms.
- **Constraint**: Zero direct LLM calls or AI inference logic in TypeScript. Communicates with Python API via type-safe generated OpenAPI client contracts.

### 3.2 Backend API (`services/api`)
- **Technology**: Python 3.12, FastAPI, Pydantic v2, `google-cloud-firestore`.
- **Role**: RESTful API for classes, assessments, questions, upload URL generation, Cloud Tasks job dispatch, teacher review CRUD, audit logging, and report exporting.
- **Security**: Validates Google Identity Services ID tokens, issues `HttpOnly; Secure; SameSite=Lax` cookies, enforces double-submit CSRF tokens, and enforces tenant scoping on all database queries.

### 3.3 AI Worker Service (`services/worker`)
- **Technology**: Python 3.12, Google Agent Development Kit (ADK), Vertex AI SDK (`google-genai`), SymPy, Pillow, `python-magic`.
- **Role**: Asynchronous execution of multi-agent assessment workflows triggered by Cloud Tasks:
  - `ImageQualityService`: deterministic post-upload validation, decompression bomb check, EXIF stripping, and 768px normalization (no LLM).
  - `VisualEvidenceAgent`: multimodal extraction with Gemini 3.8 Flash.
  - `MathInterpretationAgent`: candidate step sequence generation and alternative method identification.
  - `DiagnosticAgent`: deterministic mathematical verification (SymPy + geometry vectors) and error taxonomy mapping.
  - `IndependentCriticAgent`: contradiction checks and teacher review triage (max 1 bounded re-try).
  - `CohortIntelligenceAgent`: deterministic cohort statistical aggregation and qualitative synthesis (1 call per batch).

### 3.4 Data & Storage Layer
- **Cloud Storage (GCS)**:
  - `raw_quarantine/`: Private bucket partition storing unvalidated uploads directly from client browsers.
  - `validated_images/`: Private bucket partition storing sanitized, EXIF-stripped, 768px-normalized images.
- **Application Database**:
  - **Firestore Native Mode**: Serverless document store partitioned by organization. Stores collections for `organizations`, `users`, `classes`, `assessments`, `responses`, `analysis_versions`, `analysis_jobs`, `job_attempts`, `class_insights`, and `audit_events`.

---

## 4. Trust Boundaries & Security Enclaves

```mermaid
flowchart LR
    subgraph PublicZone ["Untrusted Public Network"]
        Client["Browser Client"]
    end

    subgraph EdgeBoundary ["Public Cloud Run Ingress"]
        Web["Next.js Web Frontend"]
        API["FastAPI Backend (GIS Auth & CSRF)"]
    end

    subgraph PrivateAppZone ["IAM-Authenticated Cloud Run Worker Tier"]
        Queue["Cloud Tasks Queue"]
        Worker["ADK AI Worker (--no-allow-unauthenticated)"]
    end

    subgraph SecureDataZone ["Secure Managed Google Cloud Tier"]
        DB[("Firestore Native Database")]
        GCS[("Private GCS Buckets")]
        Vertex["Vertex AI Gemini 3.8 Flash (ADC)"]
    end

    Client -->|HTTPS TLS 1.3| Web
    Client -->|HTTPS API Requests| API
    Web -->|Internal HTTP API| API
    API -->|Enqueue Task| Queue
    Queue -->|OIDC Bearer Token (sa-classlens-tasks)| Worker
    API <-->|IAM ADC| DB
    Worker <-->|IAM ADC| DB
    Worker -->|IAM ADC| GCS
    Worker -->|IAM ADC| Vertex
```

---

## 5. Monthly Cost Estimates & Capacity Scenarios

Figures are based on official Google Cloud Platform pricing in `asia-southeast1` (Singapore) as of late 2026, using Vertex AI Gemini 3.8 Flash introductory pricing ($0.75/$3.75 per 1M tokens) and dynamic vision tiling:

| Scenario | Workload Assumptions | Cloud Run Compute | Cloud Storage & Registry | Vertex AI Gemini 3.8 Flash | Firestore Native | Total Est. Monthly Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Dev & Feasibility** | Local deterministic mocks; 1 live feasibility test on Problem #1065658 (13 responses). | $0.00 (Free Tier) | $1.50 (Storage + Registry) | $0.12 ($0.00905 $\times$ 13) | $0.00 (Free Tier) | **$1.50 – $2.50 USD** |
| **2. Hackathon Demo** | 20 demonstration batches, 300 total responses processed, 15% critic retries. | $1.20 | $1.50 (GCS + Registry) | $2.81 ($0.00905 $\times$ 300 + cohort) | $0.00 (Free Tier) | **$4.50 – $7.50 USD** |
| **3. School Pilot (High)** | 5 teachers, 20 assessments/mo, 600 responses/mo, post-intro standard rate ($1.50/$7.50). | $12.00 (Over free tier) | $6.50 (Storage + Registry) | $13.50 ($0.0225 $\times$ 600) | $1.00 – $2.00 | **$25.00 – $40.00 USD** |

*Financial Guardrails*: Software-level quotas (max 5 assessments/day per teacher), batch caps (max 30 images), worker pre-inference kill switch, and Cloud Tasks concurrency caps (`max_concurrent_dispatches: 5`) provide active spend containment. Notification alerts configured at $25 and $50 USD.
