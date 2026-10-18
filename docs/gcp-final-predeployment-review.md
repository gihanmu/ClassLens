# ClassLens — Final GCP Pre-Deployment Technical Review, HTTPS Optimisation & Cost Reduction

**Project ID:** `precise-equator-511303-m1`  
**Region:** `asia-southeast1` (Singapore)  
**Gemini Vertex AI Location:** `global`  
**Master Deployment Script:** `scripts/gcp/deploy-all.sh`  
**Status:** **READY FOR FIRST LIVE DEPLOYMENT** (343/343 backend tests passing, Next.js BFF build & end-to-end proxy verified, Terraform validated, 13/13 dry-run stages passing, **$0.00 cloud spend incurred**)

---

## 1. Gemini Model & Pricing Verification

### 1.1 Actual Model Usage Across the 5-Stage Pipeline

An audit of `services/api/config.py`, `services/worker/gemini/adapter.py`, `services/worker/agents/provider.py`, and `services/worker/agents/pipeline.py` confirms that ClassLens implements a **hybrid neuro-symbolic architecture** that invokes Vertex AI Gemini **strictly once per unseen worksheet**:

| Pipeline Stage | Component / File | Execution Mechanism | Gemini Calls per Worksheet |
|---|---|---|---|
| **Stage 1: Visual Evidence Extraction** | `GeminiVisualEvidenceProvider` (`services/worker/agents/provider.py` $\rightarrow$ `services/worker/gemini/adapter.py`) | **Live Multimodal Vertex AI Call** via `google-genai` SDK (`genai.Client(vertexai=True, location="global", project=...)`), `temperature=0.0`, `max_output_tokens=4096`, `HttpRetryOptions(attempts=1)`, enforcing structured JSON output (`GeminiVisualEvidenceSchema`). Extracted JSON is persisted in `analysis_data.visual_evidence.raw_extraction` so re-analysis reuses the extraction without re-calling Gemini. | **1 call** *(0 calls on re-analysis or synthetic fixtures)* |
| **Stage 2: Task & Method Routing** | `TaskRouter.resolve_task` (`services/worker/math_verifier/task_router.py`) | Deterministic domain classification (`NUMBER_LINE_INTEGER`, `FRACTION_DIVISION`, etc.). | **0 calls** |
| **Stage 3: Mathematical Step Hypotheses** | `MathInterpretationAgent` (`services/worker/agents/mock_adapter.py`) | Deterministic rule-based step hypothesis generation from Stage 1 visual observations. | **0 calls** |
| **Stage 4: Symbolic Verification & Misconception Diagnosis** | `DiagnosticAgent` (`services/worker/math_verifier/`) | Deterministic **SymPy symbolic engine** + geometry/fraction-model verifiers + topic-scoped misconception taxonomy mapping. | **0 calls** |
| **Stage 5: Independent Adversarial Critic** | `IndependentCriticAgent` (`services/worker/agents/mock_adapter.py`) | Deterministic consistency and grounding audit with at most 1 bounded re-interpretation pass. | **0 calls** |
| **Cohort Insights & Teaching Action Plans** | `compute_cohort_statistics` (`services/worker/agents/tools.py`) | Deterministic topic-aware pedagogical template synthesis scoped strictly to the assessment's `task_type` and verified student misconception counts. | **0 calls** |

### 1.2 Model Configurability & Consistency Across Codebase

- **Configuration Hierarchy (`services/api/config.py`):**
  - Controlled via `CLASSLENS_GEMINI_MODEL` (primary) or `GEMINI_MODEL` (fallback), defaulting to `gemini-3.8-flash` on `GOOGLE_CLOUD_LOCATION=global`.
  - Validated against `verified_models` in `Settings.validate_live_configuration()`: `{"gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-002"}`.
- **Consistency Check:**
  - `services/api/config.py`: `gemini-3.8-flash`, `location="global"`
  - `services/worker/gemini/adapter.py`: `gemini-3.8-flash`, `location="global"`
  - `infra/terraform/variables.tf`: `gemini_model = "gemini-3.8-flash"`, `gemini_location = "global"`, `ai_mode = "live"`, `live_inference_enabled = true`
  - `apps/web/src/components/shared/offline-demo-banner.tsx`: Reads `gemini_model` dynamically from `/health` (fallback `"gemini-3.8-flash"`), fixed during this review to call relative `/health` instead of `http://localhost:8000/api/v1/health`.

### 1.3 Vertex AI Gemini Token & Cost Estimation per Worksheet

Using published Google Cloud Vertex AI pricing (`services/worker/gemini/adapter.py`):

- **Input Payload per Worksheet:**
  - 1 handwritten worksheet image (`PNG`/`JPEG`, ~600×400 to 1600×1200 px): `~258 – 1,290 tokens`
  - System instruction + structured schema prompt: `~350 tokens`
  - **Total Input per Worksheet:** `~600 – 1,640 tokens` (average `~1,200 input tokens`)
- **Output Payload per Worksheet:**
  - Structured JSON (`GeminiVisualEvidenceSchema` observations, final answer, ambiguities) + internal thinking tokens: `~500 – 1,000 output tokens` (average `~800 output tokens`)

| Model ID | Vertex AI Location | Input Rate (per 1M tokens) | Output Rate (per 1M tokens) | Est. Cost per Worksheet | Est. Cost per 100 Worksheets | Est. Cost per 500 Worksheets |
|---|---|---|---|---|---|---|
| **`gemini-3.8-flash`** *(Default)* | `global` | `$0.75` | `$3.75` | **`~$0.0039`** | **`~$0.39`** | **`~$1.95`** |
| **`gemini-2.5-flash`** *(Supported Alternative)* | `global` / `asia-southeast1` | `$0.30` | `$2.50` | **`~$0.0024`** | **`~$0.24`** | **`~$1.20`** |
| **`gemini-3.5-flash-lite`** *(Supported Low-Cost)* | `global` | `$0.10` | `$0.40` | **`~$0.0004`** | **`~$0.04`** | **`~$0.20`** |

- **Built-in Spend Safeguards:**
  1. Single-attempt execution (`HttpRetryOptions(attempts=1)` — zero retry amplification storms).
  2. Persisted visual extraction reuse (`cached_visual_evidence` in `InlineDispatcher` — re-analyzing a response costs `$0.00`).
  3. Per-instance call ceiling (`CLASSLENS_MAX_LIVE_CALLS`) and Gate 6 fail-closed `CLASSLENS_LIVE_AUTH_KEY` verification.

---

## 2. Load Balancer Removal Analysis (`Option A` vs. `Option B`)

### 2.1 Comparison of Architectures

| Dimension | Option A: External HTTPS Load Balancer + Serverless NEGs | Option B: Simplified Cloud Run BFF Architecture *(Implemented)* |
|---|---|---|
| **Public Entry Point** | Global External Application Load Balancer (`google_compute_global_forwarding_rule`) | Cloud Run Frontend (`https://classlens-frontend-<hash>-as.a.run.app`) |
| **HTTPS / TLS Certificate** | Requires a custom domain for Google-managed cert, **OR** falls back to a self-signed certificate on raw IPv4 (`https://34.x.x.x`), triggering **browser security warnings** for judges/reviewers | **Automatic Google-managed, publicly trusted TLS certificate** (`*.a.run.app` issued by Google Trust Services) with **zero browser warnings** and **no custom domain required** |
| **Frontend-to-Backend Routing** | Load Balancer URL Map routes `/api/*` and `/health` to Backend Serverless NEG | Next.js App Router runtime BFF Route Handlers (`/api/[...path]/route.ts` and `/health/route.ts`) proxy to `INTERNAL_API_URL` |
| **Backend Isolation & Security** | Backend Cloud Run `roles/run.invoker` granted to `allUsers` (relying on `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`) | **Strict Zero-Trust IAM**: Backend Cloud Run grants `roles/run.invoker` **exclusively** to `serviceAccount:classlens-frontend-sa`. Frontend BFF mints & caches Google-signed OIDC Identity Tokens (`Authorization: Bearer <id_token>`) from the Cloud Run Metadata Server. Direct public requests to the backend URL are rejected with **`HTTP 403 Forbidden`** at Google's IAM edge |
| **Session Cookies & CSRF** | Same-origin via Load Balancer IP/domain | **100% Same-Origin** via `https://classlens-frontend-...a.run.app`. `HttpOnly; Secure; SameSite=Lax` cookies (`__session`, `csrf_token`) and `X-Requested-With: ClassLens` headers are preserved end-to-end |
| **Fixed Monthly Networking Cost** | **`~$18.15 / month`** (Forwarding rules + static global IP + data processing) | **`$0.00 / month`** *(100% eliminated)* |

### 2.2 Why Next.js Build-Time `rewrites()` Was Insufficient and How the Runtime BFF Solves It

During investigation, we identified two critical flaws if one tried to rely on `apps/web/next.config.mjs` `rewrites()` without a Load Balancer:
1. **Build-Time Evaluation Bug:** `next.config.mjs` `rewrites()` is evaluated during `npm run build` inside `apps/web/Dockerfile`, when `INTERNAL_API_URL` is not yet known, baking `http://127.0.0.1:8000` into Next.js's standalone `routes-manifest.json`.
2. **Missing OIDC Service-to-Service Token:** Built-in Next.js rewrites cannot query the Cloud Run Metadata Server to attach `Authorization: Bearer <OIDC_ID_TOKEN>`, which would force `classlens-backend` to either be public (`allUsers`) or reject all proxy requests with `HTTP 403`.

**Implemented Solution (`apps/web/src/lib/bff-proxy.ts`):**
- Removed build-time `rewrites()` from `apps/web/next.config.mjs`.
- Implemented dynamic runtime Node.js App Router handlers at `apps/web/src/app/api/[...path]/route.ts` and `apps/web/src/app/health/route.ts`.
- At request time, `proxyToBackend()` reads `process.env.INTERNAL_API_URL`, fetches and caches (for 50 minutes) an OIDC Identity Token from `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=${audienceOrigin}` when targeting an `https://` Cloud Run backend, attaches `Authorization: Bearer <id_token>`, streams binary `ArrayBuffer` request/response payloads (`multipart/form-data` worksheet uploads and `/image` downloads), and forwards all `Set-Cookie` headers (`getSetCookie()`).

---

## 3. Final Recommended GCP Architecture

```
+-----------------------------------------------------------------------------------+
|                        Teacher / AI Builder Cup Reviewer                          |
|                    Browser (HTTPS - Zero Certificate Warnings)                    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS (TLS 1.3, Google-Managed *.a.run.app Cert)
                                          v
+-----------------------------------------------------------------------------------+
|  Google Cloud Run: classlens-frontend (Public Ingress, 0-2 Instances, 1 vCPU/1GiB) |
|  Identity: classlens-frontend-sa                                                  |
|  - Next.js 14 App Router UI (/, /login, dashboard, review modals)                 |
|  - Runtime BFF Proxy (/api/[...path], /health)                                    |
|    * Mints & caches OIDC ID token from Cloud Run Metadata Server                  |
|    * Preserves __session & csrf_token cookies, X-Requested-With, multipart uploads|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS + Authorization: Bearer <OIDC ID Token>
                                          | (Direct public access blocked: HTTP 403 Forbidden)
                                          v
+-----------------------------------------------------------------------------------+
|  Google Cloud Run: classlens-backend (Private IAM Invoker Only, 0-2 Instances)    |
|  Identity: classlens-backend-sa (roles/run.invoker granted ONLY to frontend-sa)   |
|  - FastAPI REST API + InlineDispatcher (--workers 1)                              |
|  - Stage 1: GeminiVisionAdapter -> Vertex AI Gemini (gemini-3.8-flash, global)    |
|  - Stages 2-5: Deterministic SymPy Verifier, Misconception Taxonomy & Critic      |
+------------+----------------------------+----------------------------+------------+
             |                            |                            |
             | Unix Socket (/cloudsql)    | ADC IAM (objectUser)       | ADC IAM (aiplatform.user)
             v                            v                            v
+-------------------------+  +--------------------------+  +------------------------+
| Cloud SQL PostgreSQL 15 |  | Cloud Storage Bucket     |  | Vertex AI Gemini API   |
| db-f1-micro (ZONAL)     |  | *-classlens-worksheets   |  | gemini-3.8-flash       |
| 10 GB SSD, Pool max=5   |  | Private, Uniform Access  |  | 1 call / new worksheet |
+-------------------------+  +--------------------------+  +------------------------+
```

---

## 4. Cloud SQL Sizing & Cost Review

- **Instance Configuration (`infra/terraform/database.tf`):**
  - **Engine:** `POSTGRES_15`
  - **Machine Tier:** `db-f1-micro` (`ENTERPRISE` edition, shared vCPU, `0.6 GB` RAM — lowest-cost Cloud SQL tier available on GCP)
  - **Availability:** `ZONAL` (Single-zone in `asia-southeast1` — avoids the 2× cost multiplier of Regional HA)
  - **Storage:** `10 GB` `PD_SSD` (minimum selectable size) with `disk_autoresize_limit = 20` GB cap
  - **Backups:** Automated daily backup enabled (`point_in_time_recovery_enabled = false` to avoid extra WAL storage charges)
  - **Connectivity:** Cloud SQL Auth Proxy Unix domain socket (`/cloudsql/<connection_name>`) with `psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=5)` per container and `max_scale = 2` (maximum 10 concurrent connections across the entire deployment, well below `db-f1-micro`'s ~25 connection limit).

---

## 5. Updated Monthly GCP Cost Estimate (`asia-southeast1`)

### 5.1 Architecture Cost Comparison (Option A vs. Option B)

| Cost Component | Option A (With External HTTPS Load Balancer) | Option B (Simplified Cloud Run BFF — Current) | Monthly Savings |
|---|---|---|---|
| **External HTTPS Load Balancer + Static IP** | `$18.15 / mo` | **`$0.00 / mo`** | **`-$18.15 / mo` (-100%)** |
| **Cloud SQL PostgreSQL 15 (`db-f1-micro`, ZONAL, 10 GB SSD)** | `$10.55 / mo` | **`$10.55 / mo`** | `$0.00` |
| **Cloud Run (`frontend` + `backend`, `min_scale=0`, `max_scale=2`)** | `$0.00 – $0.50 / mo` | **`$0.00 – $0.50 / mo`** *(within free tier)* | `$0.00` |
| **Cloud Storage (`worksheets`, Standard, 90d lifecycle)** | `$0.02 / mo` | **`$0.02 / mo`** | `$0.00` |
| **Artifact Registry (`~450 MB` images; first `500 MB` free)** | `$0.00 – $0.05 / mo` | **`$0.00 – $0.05 / mo`** | `$0.00` |
| **Secret Manager (5 active secret versions; first 6 free)** | `$0.00 – $0.06 / mo` | **`$0.00 – $0.06 / mo`** | `$0.00` |
| **Cloud Logging (Default `_Default` bucket; first `50 GiB/mo` free)** | `$0.00 / mo` | **`$0.00 / mo`** | `$0.00` |
| **Baseline Fixed Monthly Total** | **`~$28.78 / month`** | **`~$10.65 / month`** | **`-$18.13 / month` (-63%)** |

### 5.2 Usage Scenario Breakdown vs. $300 GCP Trial Credit

| Usage Scenario | Worksheets Analyzed / Month | Cloud SQL + Storage + Registry + Secrets | Cloud Run Compute (`min_scale=0`) | Vertex AI Gemini (`gemini-3.8-flash`) | **Total Monthly Cost (USD)** | **14-Day Hackathon Window Cost** | **% of $300 Credit / Month** |
|---|---|---|---|---|---|---|---|
| **1. Minimal Testing / Demo** | 25 worksheets | `$10.65` | `$0.00` *(Free Tier)* | `$0.10` | **`~$10.75 / mo`** | **`~$5.02`** | **3.6%** |
| **2. Moderate Evaluation** | 100 worksheets | `$10.65` | `$0.00` *(Free Tier)* | `$0.39` | **`~$11.04 / mo`** | **`~$5.15`** | **3.7%** |
| **3. Increased Judge Testing** | 500 worksheets | `$10.75` | `$0.40` | `$1.95` | **`~$13.10 / mo`** | **`~$6.11`** | **4.4%** |

---

## 6. Security & HTTPS Verification

1. **Publicly Trusted HTTPS Out of the Box:**
   - `classlens-frontend` is served over `https://classlens-frontend-<hash>-as.a.run.app` with an automatic Google-managed certificate signed by Google Trust Services (`GTS CA`).
   - Browsers, `curl`, and Python `urllib` validate the TLS certificate using standard root CA stores with **zero self-signed certificate warnings** and no `--insecure` / `-k` flags needed.
2. **Private Backend Service-to-Service Isolation:**
   - `google_cloud_run_v2_service_iam_member.backend_invoker` grants `roles/run.invoker` on `classlens-backend` **exclusively** to `serviceAccount:classlens-frontend-sa@precise-equator-511303-m1.iam.gserviceaccount.com`.
   - `allUsers` is **not** bound to `classlens-backend`. Any direct request from the internet to `https://classlens-backend-<hash>-as.a.run.app` without a valid Google OIDC token signed for `classlens-frontend-sa` is rejected at the Cloud Run IAM perimeter with `HTTP 403 Forbidden`.
3. **Cookie, Session & CSRF Security:**
   - All browser traffic (`/login`, `/api/v1/*`, `/health`) terminates on the single origin `https://classlens-frontend-<hash>-as.a.run.app`.
   - `__session` (`HttpOnly; Secure; SameSite=Lax`) and `csrf_token` cookies are first-party cookies on the frontend origin and are forwarded bi-directionally by `apps/web/src/lib/bff-proxy.ts`.
   - State-mutating requests (`POST`, `PUT`, `DELETE`) enforce `X-Requested-With: ClassLens` CSRF verification.

---

## 7. Code, Terraform & Script Changes Applied

| File | Change Summary |
|---|---|
| `apps/web/src/lib/bff-proxy.ts` | **Created:** Runtime Next.js Backend-for-Frontend proxy utility with 50-minute cached Cloud Run Metadata Server OIDC Identity Token minting (`Authorization: Bearer <id_token>`), multi-cookie forwarding (`getSetCookie()`), CSRF header forwarding, and binary `ArrayBuffer` streaming for multipart uploads and image downloads. |
| `apps/web/src/app/api/[...path]/route.ts` | **Created:** Dynamic App Router catch-all route handler (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `maxDuration = 300`) delegating `/api/*` to `proxyToBackend()`. |
| `apps/web/src/app/health/route.ts` | **Created:** Dynamic App Router `/health` route handler delegating to `proxyToBackend(request, "/health")`. |
| `apps/web/next.config.mjs` | **Updated:** Removed static build-time `rewrites()` so all `/api/*` and `/health` traffic routes through the runtime BFF handlers. |
| `apps/web/src/components/shared/offline-demo-banner.tsx` | **Updated:** Fixed health check URL from `http://localhost:8000/api/v1/health` fallback to relative `/health`. |
| `services/api/main.py` | **Updated:** Fixed `from services.api.repository.memory_repo import memory_repo` import inside `/health` (and `/api/v1/health` alias) so `/health` accurately reports `database_backend`, `database_healthy`, `schema_version`, and `storage_backend`. |
| `services/api/config.py` & `services/worker/gemini/adapter.py` | **Updated:** Added `gemini-3.5-flash-lite` and `gemini-2.5-pro` to `verified_models` and `MODEL_PRICING` alongside default `gemini-3.8-flash` and `gemini-2.5-flash`. |
| `infra/terraform/load_balancer.tf` | **Deleted:** Removed all External HTTPS Load Balancer, Global Static IP, Target HTTP/HTTPS Proxies, URL Maps, Self-Signed TLS Certificates, and Serverless NEG resources (`~$18.15/mo` saved). |
| `infra/terraform/cloud_run.tf` | **Updated:** Configured `classlens-frontend` with public Google-managed HTTPS (`roles/run.invoker` = `allUsers`, `timeout = "300s"`) and `classlens-backend` with private IAM-only invoker (`roles/run.invoker` = `serviceAccount:${google_service_account.frontend.email}`, `timeout = "300s"`). |
| `infra/terraform/outputs.tf` & `versions.tf` | **Updated:** Set `application_url` to `google_cloud_run_v2_service.frontend.uri`, removed `load_balancer_ip`, and removed unused `hashicorp/tls` provider. |
| `scripts/gcp/deploy-all.sh`, `verify.sh`, `deploy.sh`, `plan.sh` | **Updated:** Aligned billable resource audits, Terraform outputs, and 10-point verification probes with the Cloud Run BFF architecture and strict CA TLS validation. |
| `tests/integration/test_api_endpoints.py` | **Updated:** Added `test_health_endpoints` verifying `/health` and `/api/v1/health` readiness payload fields. |

---

## 8. Local Test & Dry-Run Results

All validations were executed locally with **$0.00 GCP cloud spend**:

1. **Backend Test Suite (`.venv/bin/pytest -q`):**
   - **Result:** `343 passed in 11.12s` (unit, integration, math verifier, topic-aware teaching recommendations, security/CSRF, PostgreSQL translation, and health check tests).
2. **Next.js Production Build (`cd apps/web && npm run build`):**
   - **Result:** Succeeded (`exit code 0`), generating standalone bundle with dynamic `ƒ /api/[...path]` and `ƒ /health` routes.
3. **End-to-End Local Runtime BFF Proxy Test (`node .next/standalone/server.js` $\rightarrow$ `uvicorn services.api.main:app`):**
   - `GET /health` via BFF: **PASS** (`status: ok`, `gemini_model: gemini-3.8-flash`, `database_backend: sqlite`)
   - `POST /api/v1/auth/login` via BFF: **PASS** (`HTTP 200`, forwarded both `Set-Cookie: __session` and `Set-Cookie: csrf_token`)
   - `GET /api/v1/assessments` via BFF: **PASS** (`HTTP 200`, authenticated via forwarded `__session` cookie)
   - `POST /api/v1/assessments/asm_1065658/upload` via BFF: **PASS** (`HTTP 200`, binary `multipart/form-data` PNG worksheet upload preserved)
   - `GET /api/v1/responses/<id>/image` via BFF: **PASS** (`HTTP 200`, binary sanitized PNG image streamed back intact)
4. **Terraform & Shell Validation:**
   - `terraform fmt -check && terraform validate`: **PASS** (`Success! The configuration is valid.`)
   - `bash -n scripts/gcp/*.sh`: **PASS** (`exit code 0` across all 7 scripts)
5. **Master Deployment Pipeline Dry-Run (`./scripts/gcp/deploy-all.sh --dry-run precise-equator-511303-m1 asia-southeast1`):**
   - **Result:** All **13/13 stages completed with exit code 0** and zero cloud resources modified.

---

## 9. Remaining Risks & Limitations (Local vs. Live Cloud Verification Boundary)

To maintain strict engineering transparency, we distinguish between what has been verified locally and what will be verified only during live deployment:

| Verification Item | Verified Locally? | Verified on Live GCP? | Notes / Mitigation |
|---|---|---|---|
| FastAPI + Next.js BFF routing, cookies, CSRF, multipart upload | **Yes (Verified)** | Pending first live deploy | Verified end-to-end against standalone Next.js + Uvicorn. |
| Cloud Run Metadata Server OIDC token minting (`getCloudRunIdToken`) | **Code-reviewed & fallback-tested** | Pending first live deploy | Uses standard Cloud Run Metadata Server endpoint (`.../instance/service-accounts/default/identity?audience=...`). Automatically verified by `verify.sh` Check 1 & Check 10 during Stage 12. |
| Cloud SQL PostgreSQL 15 Unix socket + `ThreadedConnectionPool` | **Unit-tested (mocked `psycopg2`)** | Pending first live deploy | Automatically verified by Stage 11 (`migrate.py --verify-remote`) and Stage 12 (`verify.sh` Check 9). |
| Cloud Run Cold-Start Latency (`min_scale = 0`) | N/A | Pending first live deploy | With `min_scale = 0`, the first request after idle takes ~3–6 seconds for container cold start. If zero-cold-start is desired during live judging, `min_scale` can be temporarily set to `1`. |
| First-Time Cloud SQL Instance Creation Duration | N/A | Pending first live deploy | GCP takes ~8–12 minutes to provision a new `google_sql_database_instance` during Stage 10. |

---

## 10. Exact Live Deployment Commands

When you are ready to authorize the first live deployment to `precise-equator-511303-m1` (`asia-southeast1`), run:

### Step 1: (Optional) Pre-Initialize Secret Manager Secrets Interactively
```bash
./scripts/gcp/init-secrets.sh precise-equator-511303-m1
```
*(Note: `deploy-all.sh` automatically runs `init-secrets.sh` in Stage 4 if you skip this step.)*

### Step 2: Execute One-Command Production Deployment
```bash
./scripts/gcp/deploy-all.sh --confirm precise-equator-511303-m1 asia-southeast1
```

### Step 3: Post-Deployment Re-Verification (Anytime)
```bash
APP_URL=$(terraform -chdir=infra/terraform output -raw application_url)
./scripts/gcp/verify.sh "$APP_URL" precise-equator-511303-m1
```
