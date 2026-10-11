# Architecture Decision Records (ADRs) — ClassLens

**Document ID:** ARC-ADR-005
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- **ADR-001 Reconciled**: Formally selected **Google Cloud Firestore Native Mode** as the single authoritative datastore for MVP, retiring Cloud SQL PostgreSQL.
- **ADR-003 Reconciled**: Formally selected **Google Cloud Tasks + Private Cloud Run Worker**, rejecting FastAPI BackgroundTasks.
- **ADR-006 Added**: Evaluation ground truth adjudication protocol (retracting unverified multi-expert consensus assertion).
- **ADR-007 Added**: Python service packaging standardized to non-hyphenated `services/worker/`.

---

## ADR-001: Choice of Datastore — Firestore Native Mode

### Status: Accepted (Reconciled)
### Context:
ClassLens requires persistence for organizations, users, classes, assessments, questions, submissions, multi-step analysis records, teacher overrides, audit logs, and aggregated class snapshots. The system must support strict tenant isolation, transactional review updates, and seamless Terraform provisioning with zero idle costs.

### Alternatives Considered:
1. **Google Cloud Firestore Native Mode**: Serverless NoSQL document store with generous free tier (1 GiB storage, 50,000 reads/day, 20,000 writes/day), true zero baseline cost when idle, native nested JSON document support, and instant Terraform provisioning.
2. **Cloud SQL for PostgreSQL**: Relational ACID database. Rejected due to minimum standing instance cost of $\approx \$10 – \$15/mo$ (`db-f1-micro`), 7–10 minute Terraform provisioning delay, VPC peering complexity, and unnecessary overhead for classroom assessment batches.

### Decision:
**Adopt Google Cloud Firestore Native Mode exclusively for the ClassLens MVP**.

### Rationale:
- **Zero Standing Cost**: Serverless billing fits the AI Builder Cup hackathon constraints perfectly.
- **Document Structure**: Student responses contain nested observations, coordinate lists, verified steps, and candidate hypotheses. Storing these as rich documents is vastly cleaner than maintaining 8 normalized SQL join tables.
- **ACID Transactions**: Firestore provides serializable atomic transactions on up to 500 documents, enabling safe teacher review overrides and atomic cohort progress updates.
- **Local Development**: Supported by the official Google Cloud Firestore Emulator (`gcloud beta emulators firestore start`).

---

## ADR-002: AI Processing Language & Runtime Boundary

### Status: Accepted
### Context:
Modern web frameworks often embed LLM calls directly in server actions or edge API routes. We must establish an inviolable boundary between frontend UI and AI inference.

### Decision:
**All AI manipulation, multimodal parsing, SymPy checks, agent orchestration, and cohort aggregations MUST be written in Python. TypeScript is strictly limited to UI, presentation, and thin typed BFF proxying.**

### Rationale:
- **Ecosystem Dominance**: Advanced mathematical reasoning requires SymPy, Pillow for geometric transformations, and Google Agent Development Kit (ADK) Python libraries.
- **Security & Separation of Concerns**: Isolates Gemini API credentials and proprietary prompt chains in private backend services.
- **Auditability**: Ensures all model evaluations, benchmark test suites, and golden dataset checks share the identical Python codebase used in production.

---

## ADR-003: Asynchronous Orchestration — Cloud Tasks & Private Cloud Run Worker

### Status: Accepted (Reconciled)
### Context:
Analyzing 10–15 handwritten responses takes 20–40 seconds of aggregate processing time. Running this synchronously inside a standard HTTP request risks gateway timeouts and poor UX.

### Alternatives Considered:
1. **FastAPI `BackgroundTasks` on Cloud Run**: Rejected because Cloud Run throttles container CPU outside of active HTTP responses by default, freezing background tasks mid-inference.
2. **Cloud Run Jobs**: Rejected because container startup overhead (~10–15s) per assessment batch is too slow for interactive classroom workflows.
3. **Cloud Tasks HTTP Webhooks**: Enqueues individual response tasks into a regional queue targeting a private Cloud Run worker.

### Decision:
**Adopt Google Cloud Tasks dispatching to a private Cloud Run Worker service (`services/worker`), with an inline adapter for local offline development.**

### Rationale:
- **Concurrency Control**: Cloud Tasks enforces `max_concurrent_dispatches: 5`, capping peak Vertex AI concurrency to prevent HTTP 429 quota exhaustion.
- **Deduplication**: Cloud Tasks guarantees task name deduplication within the queue, preventing duplicate runs.
- **Granular Retries**: Each student response is an isolated HTTP task. Transient timeouts retry individually with exponential backoff without failing the entire classroom batch.

---

## ADR-004: Multimodal Model Selection & Regional Placement

### Status: Accepted (Reconciled)
### Context:
ClassLens analyzes handwritten numbers, equations, and number lines. We must balance perceptual acuity, structured output adherence, latency, and cost.

### Decision:
**Vertex AI Gemini 1.5 Flash (`gemini-1.5-flash-002`) and Gemini 2.0 Flash (`gemini-2.0-flash`) deployed in `asia-southeast1` (Singapore)**, with `gemini-1.5-pro-002` as an optional fallback for complex ambiguous diagrams.

### Rationale:
- **Vision Acuity & Structured JSON**: Gemini Flash models excel at following strict Pydantic JSON schema output contracts with sub-second latency.
- **Cost**: Normalizing images to $\le 1024 \times 1024$ px locks vision input at 258 tokens, enabling an entire classroom assessment (15 students) to be analyzed for under $\$0.01$ USD.
- **Data Residency**: Singapore hosting aligns with Singapore Personal Data Protection Act (PDPA) considerations and MOE school network latency requirements.

---

## ADR-005: Terraform as Infrastructure Source of Truth

### Status: Accepted
### Context:
Cloud deployments must be reproducible, auditable, and disposable without manual Google Cloud Console clicks.

### Decision:
**100% of GCP cloud infrastructure defined in modular Terraform (`infra/terraform/`) with remote GCS state locking.**

---

## ADR-006: Evaluation Ground Truth Protocol & Retraction of Unverified Claims

### Status: Accepted (New)
### Context:
Initial planning documents asserted that the 13 responses in `problem_1065658` had been "manually verified with multi-expert consensus". A deep audit revealed only single-teacher ASSISTments descriptive text.

### Decision:
**Retract the multi-expert consensus claim. Reclassify the benchmark as `Provisional / Single-Rater Benchmark` and mandate a formal double-blind adjudication protocol before publishing benchmark accuracy metrics.**

---

## ADR-007: Python Service Packaging & Module Naming

### Status: Accepted (New)
### Context:
Python PEP 8 prohibits hyphens in module and package directories. The folder `services/ai-worker` prevents valid Python imports (`import services.ai-worker` is a syntax error).

### Decision:
**Standardize Python worker service directory to `services/worker/` (or `services/ai_worker/`)**.
