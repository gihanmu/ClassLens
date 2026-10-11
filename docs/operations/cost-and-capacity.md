# Cost and Capacity Planning Guide — ClassLens

**Document ID:** OPS-CST-003
**Version:** 1.2.0
**Date:** 2026-10-11

---

### Changelog (v1.2.0 — Final Technical-Validity Revision)
- Recalculated inference costs using **Vertex AI Gemini 3.8 Flash (`gemini-3.8-flash`)** in `asia-southeast1` (Singapore) at introductory rate ($0.75 / 1M input, $3.75 / 1M output).
- Replaced flat 258 vision token assumption with **dynamic vision tiling model** ($\approx 516 – 774$ vision tokens for 768px normalized images).
- Removed absolute financial containment guarantees; defined **worker pre-inference kill switch** that prevents already-queued tasks from executing paid calls.
- Documented regional Cloud Storage pricing (no free tier in `asia-southeast1`).

---

## 1. Pricing Model & Unit Cost Drivers

ClassLens cost is governed by three primary serverless variables:

### 1.1 Multimodal Inference (Vertex AI Gemini 3.8 Flash in `asia-southeast1`)
- **Introductory Rate Card (through December 31, 2026)**:
  - Input tokens: $0.75 per 1,000,000 tokens ($0.00000075 / token).
  - Output tokens: $3.75 per 1,000,000 tokens ($0.00000375 / token). Output rate applies to reasoning/thinking tokens.
- **Dynamic Vision Tiling**:
  - Images $\le 384\times 384$ px consume 258 tokens.
  - Normalizing student work to max dimension 768px generates $\approx 516 – 774$ vision tokens (2 to 3 tiles).
  - *Note*: All token counts are analytical estimates based on Vertex AI specifications; exact usage will be calibrated during the Phase 2 live feasibility test.
- **Multi-Agent Pipeline Footprint Per Response**:
  - `VisualEvidenceAgent`: 1,424 input tokens (774 image + 650 prompt), 450 output tokens = $0.002756
  - `MathInterpretationAgent`: 1,150 input tokens, 350 output tokens = $0.002175
  - `DiagnosticAgent`: 850 prompt tokens (0 for SymPy tools), 300 output tokens = $0.001763
  - `IndependentCriticAgent`: 1,250 input tokens, 150 output tokens = $0.001500
  - **Base Total Per Student Response**: **~4,674 input + ~1,250 output tokens = ~$0.008194 USD**.
  - **Expected Total with 15% Critic Retry**: **~$0.009049 USD** (~0.90 cents).
- **Cohort Intelligence Synthesis (Once Per 15-Student Batch)**:
  - `CohortIntelligenceAgent`: 1,800 input tokens, 900 output tokens = **$0.004725 USD**.
- **Total Expected Assessment Batch Cost (15 Students)**:
  - $(15 \times \$0.008194) + (2 \times \$0.005700) + \$0.004725 = \mathbf{\$0.1389\text{ USD}}$ (~14 cents per entire class).

### 1.2 Compute (Cloud Run)
- **Zero-Scale Idle**: $0.00 standing compute cost.
- **Active Processing**: A 15-student batch takes $\approx 25$ seconds of aggregate container runtime across 4 workers = $\approx 0.03$ vCPU-hours ($\approx \$0.0008$). Covered by the global free tier during development (first 2M requests/mo free).

### 1.3 Storage & Registry
- **Firestore Native Mode**: Within global free tier (1 GiB storage, 50k reads/day, 20k writes/day) = **$0.00**.
- **Cloud Storage**: **No Free Tier in Singapore (`asia-southeast1`)**; Standard storage billed at $0.023/GB-month from byte 1. 5 GB with operations = **~$0.15 – $0.35/month**.
- **Artifact Registry**: Container image storage for 3 images (~1.2 GB) = **~$0.12/month**.
- **Cloud Tasks**: Within free tier (first 1M tasks/month free) = **$0.00**.

---

## 2. Monthly Workload Scenarios & Sensitivity Analysis

### Scenario 1: Low Workload — Local Development & Deterministic Fixtures
- **Workload**: Deterministic mocks for coding; 1 live feasibility run on Problem #1065658 (13 student responses).
- **Gemini Inference**: $13 \times \$0.00905 + \$0.0047 = \$0.12$
- **GCP Standing Storage & Registry**: ~$1.50
- **Total Projected Cost**: **$1.50 – $2.50 USD / month**

### Scenario 2: Expected Workload — AI Builder Cup Hackathon & Live Judging Demo
- **Workload**: 20 demonstration runs, 300 student responses analyzed, demo sandbox active.
- **Gemini Inference**: $(300 \times \$0.00905) + (20 \times \$0.0047) = \$2.81$
- **Cloud Run Compute**: ~$1.20
- **Standing Storage & Registry**: ~$1.50
- **Total Projected Cost**: **$4.50 – $7.50 USD / month**

### Scenario 3: High Workload — Single School Pilot (Standard Pricing Post-2026)
- **Workload**: 5 teachers, 20 assessments/month (600 responses/month), post-intro standard rate ($1.50 / $7.50), unscaled 1024px images (~1,290 vision tokens), 30% critic retries.
- **Unit Cost**: ~$0.0225 per response.
- **Gemini Inference**: $600 \times \$0.0225 = \$13.50$
- **Cloud Run Compute**: ~$12.00
- **Storage, Registry & Egress**: ~$6.50
- **Total Projected Cost**: **$25.00 – $40.00 USD / month**

---

## 3. Financial Guardrails & Multi-Tier Spending Safeguards

> [!CAUTION]
> **No Guarantees of Absolute Financial Containment**: Software-level quotas, batch limits, and cloud alerts mitigate accidental runaway costs, but no public cloud architecture can promise absolute zero-risk financial containment against severe credential compromise or zero-day exploitation.

ClassLens enforces defense-in-depth spending controls:

1. **Daily Assessment Quota**: FastAPI middleware caps each teacher account to a maximum of **5 assessments per day** in the demo environment.
2. **Batch Upload Cap**: Max upload batch size capped at **30 files** per submission.
3. **Queue Concurrency Cap**: Cloud Tasks enforces `max_concurrent_dispatches: 5`, capping peak instantaneous Vertex AI token burn.
4. **Token Generation Ceiling**: All Gemini API calls enforce `max_output_tokens = 1024`.
5. **Worker Pre-Inference Kill Switch**: Evaluated immediately before every call to `client.models.generate_content` (checking `INFERENCE_ENABLED` env and Firestore circuit-breaker flag). If tripped, the worker immediately aborts the call, transitioning queued tasks to `PAUSED_CIRCUIT_BREAKER` without executing paid inference.
6. **Notification Alerts**: Cloud Monitoring alerts at $25 and $50 thresholds notify administrators.
