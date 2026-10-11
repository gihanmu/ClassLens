# ClassLens — Revised Implementation Roadmap & Approval Gates

**Document ID:** REV-GAT-007
**Version:** 1.2.1
**Date:** 2026-10-11
**Status:** Ready for User Review & Sign-Off (Final Technical-Validity Revision)

---

## 1. Unified Phase-by-Phase Roadmap & Gate Alignment

```mermaid
flowchart TD
    G1{Approval Gate 1:<br>Architecture Sign-Off<br><b>(Current Gate)</b>} --> P2[Phase 2: Offline Deterministic Local Vertical Slice<br>FastAPI + Next.js + SymPy + Mock ADK Pipeline]
    P2 --> G2{Approval Gate 2:<br>Local Slice Verified<br><b>(Plumbing & Contracts Confirmed)</b>}
    G2 --> P3[Phase 3: Bounded Live Gemini Feasibility Test<br>Live Gemini 3.8 Flash on Problem #1065658 (13 Responses)]
    P3 --> G3{Approval Gate 3:<br>Feasibility & Cost Approved<br><b>(Empirical Metrics Verified)</b>}
    G3 --> P4[Phase 4: Persistence & Cloud Infrastructure<br>Firestore Native + GIS Auth + Terraform asia-southeast1]
    P4 --> G4{Approval Gate 4:<br>Terraform Apply Authorized}
    G4 --> P5[Phase 5: Cloud Deployment & Demo Hardening<br>Cloud Run + Cloud Tasks + Judge Sandbox]
    P5 --> G5{Approval Gate 5:<br>Production & Demo Freeze}
```

---

## 2. Detailed Work Packages & Verification Criteria

### Phase 2: Offline Deterministic Local Vertical Slice (Target: 3 Working Days)
- **Primary Goal**: End-to-end working pipeline running 100% locally on synthetic fixtures and structured observation vectors without cloud dependencies, paid Gemini API calls, or GCP provisioning.
- **Critical Technical Distinction**:
  > [!IMPORTANT]
  > **Deterministic Tools Validate Structured Math Data, NOT Raw Handwriting**: Deterministic Python tools (`SymPyChecker`, `NumberLineDisplacementCalculator`) operate strictly on **structured observation vectors** (e.g. `start: 0, end: -6, delta: -6`) and synthetic test fixtures. They do **not** transcribe raw pixels of student drawings. In Phase 2, mock AI adapters supply structured observation fixtures representing the 13 student cases of Problem #1065658 to validate mathematical checking, error taxonomy mapping, and UI rendering. Actual handwriting perception from image pixels is strictly validated in Phase 3.
- **Work Package 2.1**: Scaffolding & Packaging
  - Initialize `apps/web/` (Next.js 15 App Router, React 19, Tailwind CSS, KaTeX).
  - Initialize `services/api/` (FastAPI, Pydantic v2, CORS, cookie/CSRF handlers).
  - Initialize `services/worker/` (Python ADK agents, Pillow, SymPy — non-hyphenated package).
  - Local unit test runner in `tests/unit/`.
- **Work Package 2.2**: Deterministic Math & Image Tools
  - Implement `SymPyChecker` (exact rational arithmetic verification on structured expressions).
  - Implement `NumberLineDisplacementCalculator` (displacement vectors $\Delta x_i$, interval consistency, tick label intervals on structured vector fixtures).
  - Implement `ImageQualityService` (magic bytes, dimensions, contrast, EXIF stripping, rotation detection on raw files).
- **Work Package 2.3**: Bounded ADK Agent Pipeline with Mock Adapters
  - Implement `VisualEvidenceAgent`, `MathInterpretationAgent`, `DiagnosticAgent`, `IndependentCriticAgent`.
  - Wire deterministic tools to agents with strict Pydantic JSON contracts.
  - Implement local mock LLM provider returning realistic synthetic observation vectors for Problem #1065658.
- **Work Package 2.4**: Next.js Educator Interface
  - Dual-pane image viewer (zoom, pan, rotate).
  - Step-by-step reasoning card with dual visual indicators (icons + text).
  - First-error localization card with misconception badge.
  - Teacher Approve / Override toggle with audit event tracking.
- **Verification Test Command**:
  ```bash
  pytest tests/unit/test_math_verifier.py tests/unit/test_number_line_geometry.py tests/unit/test_image_quality.py
  ```

---

### Phase 3: Bounded Live Gemini Feasibility Test (Target: 1 Working Day — STRICTLY GATED)
- **Primary Goal**: Measure actual multimodal transcription accuracy, empirical token counts, and live latency on real handwriting using curated Problem #1065658.
- **Work Package 3.1**: Bounded Live Evaluation Harness
  - Execute live Gemini 3.8 Flash inference strictly on the 13 responses of `dataset/problem_1065658/`.
  - Measure empirical token usage via SDK `client.models.count_tokens()`.
  - Record measured P50 and P95 latency per response (target SLO: P50 $\le 3.5$s, P95 $\le 6.0$s; empirical values will replace targets).
  - **Budgeting & Spend Governance**:
    - *Estimated Budget*: $\approx \$0.12 – \$0.14\text{ USD}$ total (Gemini 3.8 Flash introductory rate).
    - *Enforced Application Quota*: Hardcoded test ceiling `MAX_TEST_RESPONSES = 13`, `MAX_RETRIES = 1`, `MAX_OUTPUT_TOKENS = 1024`.
    - *Stop-on-Threshold Circuit Breaker*: Test runner tracks cumulative token spend; halts immediately if cumulative estimated cost reaches **$0.50 USD**.
    - *Residual Billing Risk*: In-flight HTTP requests dispatched to Vertex AI cannot be canceled mid-generation; max potential exposure is bounded by token ceilings ($< \$1.00\text{ USD}$).
- **Verification Test Command**:
  ```bash
  pytest tests/evaluation/test_live_feasibility_1065658.py --run-live-gemini
  ```

---

### Phase 4: Secure Persistence & Cloud Infrastructure (Target: 2 Working Days — STRICTLY GATED)
- **Primary Goal**: Durable state management using Firestore Native Mode and infrastructure-as-code with Terraform.
- **Work Package 4.1**: Firestore Repository Layer
  - Configure `google-cloud-firestore` repository adapters.
  - Local Firestore emulator integration (`gcloud beta emulators firestore start`).
  - Implement atomic transactions for task lease claims, teacher review overrides, and cohort counters.
- **Work Package 4.2**: GIS Authentication & Tenant Scoping
  - Implement `/api/v1/auth/google` with Google ID Token verification.
  - Session cookie handling (`HttpOnly; Secure; SameSite=Lax`) and double-submit CSRF cookie.
- **Work Package 4.3**: Terraform Stacks in `infra/terraform/`
  - Modules: `services`, `iam`, `storage`, `firestore`, `tasks`, `monitoring`.
  - Review `terraform plan` in `asia-southeast1` before any deployment.
- **Verification Test Command**:
  ```bash
  pytest tests/integration/test_firestore_repository.py tests/integration/test_auth_rbac.py
  terraform -chdir=infra/terraform/environments/dev plan
  ```

---

### Phase 5: Cloud Deployment & Hackathon Demo Hardening (Target: 2 Working Days)
- **Primary Goal**: Deploy serverless services to GCP and harden the judge demonstration sandbox.
- **Work Package 5.1**: Cloud Run & Cloud Tasks Deployment
  - Deploy `apps/web` and `services/api` to public Cloud Run.
  - Deploy `services/worker` to IAM-authenticated private Cloud Run.
  - Configure regional Cloud Tasks queue (`classlens-analysis-queue`).
- **Work Package 5.2**: Guided Demo Sandbox
  - Provide explicit toggle between **Precomputed Demonstration Mode** (instant, guaranteed zero-latency fixture data for judging presentations) and **Live Analysis Mode** (real-time Cloud Tasks + Vertex AI execution).
  - Interactive multi-agent trace inspector (displaying handoffs between Visual, Interpretation, Diagnostic, and Critic agents).
  - **Automated Accessibility Testing**: Automated linters via `@axe-core/playwright` verify automated WCAG rules (contrast, ARIA, DOM structure). *Note*: Automated checks do **not** constitute proof of full WCAG 2.2 AA compliance, which requires human assistive tech audits.
- **Verification Test Command**:
  ```bash
  pytest tests/e2e/test_cloud_pipeline.py
  npx playwright test
  ```

---

## 3. Complete, Testable Approval-Gate Checklist

| Gate ID | Checkpoint Milestone | Prerequisites & Acceptance Criteria | Authorized Scope | Strictly Prohibited Actions | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GATE 1** | **Architecture & Technical-Validity Sign-Off** (Current) | All review documents reconciled; model IDs verified (`gemini-3.8-flash`); cost model, security threat model, and evaluation protocols approved by user. | Scaffolding local repository, writing unit tests, implementing deterministic Python tools and local mock pipeline. | **NO live Gemini API calls, NO GCP provisioning (`terraform apply`), NO editing raw datasets.** | **AWAITING USER SIGN-OFF** |
| **GATE 2** | **Offline Local Vertical Slice Verification** | 100% pass on Tier 1 unit tests (`pytest tests/unit/`); deterministic Python tools validate structured mathematical observations and synthetic fixtures representing all 13 cases of Problem #1065658; local Next.js UI renders dual-pane inspection without cloud errors. | Scaffolding Phase 3 live feasibility test harness. | **NO GCP cloud provisioning; live API calls remain locked.** | Pending Gate 1 |
| **GATE 3** | **Live Gemini Feasibility Authorization** | Bounded test harness prepared; estimated budget ($\approx \$0.14\text{ USD}$) and $0.50 stop-on-threshold breaker confirmed; user authorizes running live inference on Problem #1065658. | Running live Gemini 3.8 Flash calls on strictly $\le 13$ responses of Problem #1065658; recording empirical tokens, latency, and transcription precision. | **NO bulk analysis of all 2,030 images across 188 problems; NO GCP cloud provisioning.** | Pending Gate 2 |
| **GATE 4** | **Terraform GCP Deployment Authorization** | Feasibility metrics verified; `terraform plan` reviewed and cost estimates approved in `asia-southeast1`. | Running `terraform apply` in dev GCP project; building and pushing Docker containers to Artifact Registry. | **NO production multi-region deployment; NO public unauthenticated release.** | Pending Gate 3 |
| **GATE 5** | **Production & Demo Freeze Authorization** | End-to-end integration tests pass on Cloud Run; precomputed demo sandbox verified; Playwright automated accessibility scans pass without errors. | Final presentation freeze; public demonstration to AI Builder Cup judges. | **NO out-of-band architecture modifications.** | Pending Gate 4 |
