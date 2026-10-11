# Non-Functional Requirements (NFR) — ClassLens

**Document ID:** REQ-NFR-004
**Version:** 1.2.0
**Date:** 2026-10-11

---

### Changelog (v1.2.0 — Final Technical-Validity Revision)
- Updated model reference to **Vertex AI Gemini 3.8 Flash (`gemini-3.8-flash`)** in `asia-southeast1` (Singapore) with introductory pricing card ($0.75/$3.75 per 1M).
- Replaced flat 258 vision token assumption with **dynamic vision tiling model** ($\approx 516 – 774$ tokens for 768px normalized images).
- Reconciled unit inference costs: Base response: ~$0.00819 USD; Expected with 15% Critic retry: ~$0.00905 USD; 15-student batch: ~$0.1389 USD.
- Designated latency figures (P50 $\le 25$s, P95 $\le 45$s) as **target SLOs** to be empirically measured during the Phase 2 live feasibility test.
- Added worker pre-inference kill switch to spending safeguards.

---

## 1. Accessibility (WCAG 2.2 AA)
- **Target Standard**: Web Content Accessibility Guidelines (WCAG) 2.2 Level AA compliance across all teacher-facing views.
- **Color Contrast**: Text and interactive UI elements must achieve a minimum contrast ratio of 4.5:1 against their backgrounds (3:1 for large text).
- **Color Independence**: Mathematical correctness and diagnostic statuses must never rely exclusively on color (e.g. green/red); must always feature dual indicators (icons + descriptive text badges).
- **Keyboard Navigation**: Full keyboard navigation support (Tab, Enter, Space, Arrow keys, Esc) across all modals, image inspection controls, and form wizards. Focus rings must remain distinctly visible.
- **Screen Reader Support**: Semantic HTML5 elements (`<main>`, `<nav>`, `<section>`, `<article>`), ARIA labels on icon buttons, and accessible math renderings via KaTeX/MathML.
- **Motion & Viewport**: Respect `prefers-reduced-motion`; fluid responsive layout scaling from 360px (mobile) to 2560px (ultra-wide desktop) without horizontal clipping.

---

## 2. Performance Budgets & Latency (Target SLOs)
- **Frontend Page Load**:
  - Largest Contentful Paint (LCP) $\le 1.8$ seconds on standard broadband.
  - Interaction to Next Paint (INP) $\le 200$ milliseconds.
  - Cumulative Layout Shift (CLS) $\le 0.05$.
- **API Response Latency**:
  - Synchronous CRUD endpoints (classes, assessments, review updates): P95 $\le 250$ milliseconds.
  - Image upload URL signing: P95 $\le 150$ milliseconds.
- **Asynchronous Analysis Pipeline (Cloud Tasks + Worker)**:
  - *Target SLO Per Response*: P50 $\le 3.5$ seconds, P95 $\le 6.0$ seconds (unmeasured estimate; subject to empirical measurement during Phase 2 live feasibility test).
  - *Target SLO 15-Response Batch* (with concurrency 4–5): completed in P50 $\le 25$ seconds, P95 $\le 45$ seconds.
  - Maximum hard timeout for a 30-response batch: 60 seconds.

---

## 3. Scalability & Serverless Concurrency
- **Architecture**: Fully serverless on Google Cloud Run and Google Cloud Tasks.
- **Horizontal Auto-scaling**:
  - Cloud Run Frontend: scales 0 to 10 instances based on concurrency (default 80 concurrent requests/instance).
  - Cloud Run API: scales 0 to 20 instances.
  - AI Worker: scales 0 to 5 instances, controlled strictly by Cloud Tasks concurrency limits (`max_concurrent_dispatches: 5`).
- **Cold-Start Optimization**: Lightweight distroless/slim Python container base images with lazy SDK initialization to achieve cold starts $\le 3$ seconds.

---

## 4. Reliability, Fault Tolerance & Graceful Degradation
- **Uptime Target**: $99.9\%$ availability for classroom assessment review.
- **At-Least-Once Delivery**: Handled via application-level idempotency and atomic lease claims on `student_responses` documents.
- **Isolation of Failures**: Individual image processing failures (e.g., corrupt file or Vertex AI transient timeout) must never fail the entire batch. Failed responses transition to `failed` state with actionable retry buttons.
- **Exponential Backoff**: Automatic retries (up to 3 attempts with exponential backoff: min 5s, max 60s) for transient Vertex AI 429/503 errors.
- **Dead-Letter Handling**: Tasks failing after 3 retries transition to `FAILED_UNRECOVERABLE` and are flagged for operator review.

---

## 5. Security & Data Residency (PDPA / MOE Alignment)
- **Principle of Least Privilege**: Application service accounts have strictly scoped IAM roles (`roles/storage.objectViewer`, `roles/aiplatform.user`, `roles/datastore.user`); no primitive Owner or Editor roles.
- **Data Minimization**: No student Personally Identifiable Information (PII) required. Pseudonymous IDs generated locally within classroom scope.
- **Encryption**:
  - In Transit: TLS 1.3 enforced on all external endpoints.
  - At Rest: Google-managed encryption keys (AES-256) on GCS buckets and Firestore storage.
- **Data Residency**: Cloud Storage buckets, Cloud Run compute, and Firestore database configured in Singapore (`asia-southeast1`). Vertex AI Gemini inference routed to Singapore regional endpoint (`asia-southeast1-aiplatform.googleapis.com`).
- **Retention & Purge**: User-configurable retention policy (default 30 days) with automated GCS bucket lifecycle rules and hard deletion cascading.

---

## 6. Cost Ceilings & Token Governance
- **Standing Monthly Cost**: Serverless architecture incurs storage and registry baseline fees ($\approx \$0.30 – \$1.50$ USD/month; note Cloud Storage has no free tier in `asia-southeast1`).
- **Inference Cost Budget**:
  - Model: Vertex AI Gemini 3.8 Flash (`gemini-3.8-flash`) in `asia-southeast1` at introductory rate ($0.75/$3.75 per 1M).
  - Vision token limit: Bounded by 768px normalization to $\approx 516 – 774$ vision tokens.
  - Target cost per student response: **~$0.00819 USD** (Base), **~$0.00905 USD** (Expected with 15% Critic retry).
  - Target cost per classroom batch (15 students): **~$0.1389 USD** (~14 cents/class).
- **Spending Safeguards (Multi-Tier)**:
  - Daily account quota: Max 5 assessments per teacher account.
  - Hard batch limit: Max 30 images per assessment.
  - Task concurrency cap: Max 5 concurrent tasks.
  - Hard output token limit: `max_output_tokens = 1024`.
  - Worker pre-inference kill switch: Evaluated immediately before every paid Gemini API call.
