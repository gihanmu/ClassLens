# ClassLens Google Cloud Platform Deployment Guide

## Target Production Architecture (Simplified Cloud Run BFF + Private IAM Backend)

- **Region**: `asia-southeast1` (Singapore)
- **Public Frontend & BFF Proxy**: Next.js 14 Standalone on Google Cloud Run (`classlens-frontend`, `linux/amd64`, Autoscaling `0–2` instances, `1 vCPU / 1 GiB RAM`, `timeout = 300s`, non-root `nextjs` UID `1001`).
  - Publicly reachable via Google-managed `https://classlens-frontend-<hash>-as.a.run.app` with an automatic, publicly trusted Google Trust Services SSL/TLS certificate (zero browser certificate warnings and no custom domain required).
  - Includes Next.js App Router runtime Backend-for-Frontend (BFF) route handlers (`/api/[...path]/route.ts` and `/health/route.ts`) that read `INTERNAL_API_URL` at runtime, mint and cache 50-minute Google OIDC Identity Tokens (`Audience = INTERNAL_API_URL`) from the local Cloud Run Metadata Server, attach `Authorization: Bearer <id_token>`, and forward cookies (`classlens_session`), CSRF headers (`X-Requested-With`, `X-CSRF-Token`), and binary `multipart/form-data` worksheet uploads to the private backend.
- **Private Backend**: FastAPI Python 3.12 on Google Cloud Run (`classlens-backend`, `linux/amd64`, Autoscaling `0–2` instances, `1 vCPU / 1 GiB RAM`, `--workers 1`, `timeout = 300s`, non-root `appuser` UID `1001`).
  - **Strict IAM Isolation**: Does **not** grant `roles/run.invoker` to `allUsers`. Only `serviceAccount:classlens-frontend-sa@precise-equator-511303-m1.iam.gserviceaccount.com` is granted `roles/run.invoker`. Direct unauthenticated requests to the backend `.run.app` URL are blocked at the Google Cloud Run IAM perimeter with `HTTP 403 Forbidden`.
- **AI Inference**: Live Vertex AI Gemini Multimodal Vision (`CLASSLENS_GEMINI_MODEL=gemini-3.8-flash`, `GOOGLE_CLOUD_LOCATION=global`, `CLASSLENS_AI_MODE=live`, `CLASSLENS_LIVE_INFERENCE_ENABLED=true`).
  - Neuro-symbolic 5-stage pipeline: **Stage 1 (`VisualEvidenceAgent`)** executes a single bounded multimodal Gemini call (`attempts=1`, `temperature=0.0`, `GeminiVisualEvidenceSchema`), while **Stages 2–5** (Task Routing, Step Hypotheses, SymPy Symbolic Verification & Misconception Taxonomy Diagnosis, Independent Adversarial Critic, and Topic-Aware Teaching Action Plans) execute deterministically in Python + SymPy with zero additional LLM calls.
- **Relational Database**: Managed Google Cloud SQL for PostgreSQL 15 (`db-f1-micro`, `ENTERPRISE` edition, Single-Zone `ZONAL`, `10 GB` SSD with `20 GB` autoresize cap) mounted via Cloud SQL Auth Proxy Unix domain socket (`/cloudsql/<connection_name>`) and managed via `psycopg2.pool.ThreadedConnectionPool` (`minconn=1, maxconn=5`). Container-local SQLite is strictly prohibited in production.
- **Object Storage**: Private Google Cloud Storage Bucket (`${PROJECT_ID}-classlens-worksheets`) with Uniform Bucket-Level Access, `public_access_prevention = "enforced"`, object versioning, and 90-day lifecycle policy.
- **Secrets**: Google Cloud Secret Manager:
  - `classlens-production-session-secret` (`SECRET_KEY` — 256-bit CSPRNG hex for HMAC-SHA256 stateless session signing)
  - `classlens-production-teacher-password` (`CLASSLENS_DEMO_PASSWORD` — Argon2id-verified password for `teacher@classlens.demo`)
  - `classlens-production-live-auth-key` (`CLASSLENS_LIVE_AUTH_KEY` — 256-bit CSPRNG hex authorization token for live Gemini calls)
  - `classlens-production-database-url` & `classlens-production-db-password` (automatically generated and populated by Terraform)
- **Container Registry**: Google Cloud Artifact Registry (`${REGION}-docker.pkg.dev/${PROJECT_ID}/classlens-repo`) using immutable Git commit SHA tags (`sha-<commit>`).

---

## One-Command Master Deployment (`scripts/gcp/deploy-all.sh`)

ClassLens provides a single, repeatable master deployment command that orchestrates all 13 validation, secret bootstrap, state synchronization, `linux/amd64` container packaging, infrastructure provisioning, remote PostgreSQL schema verification, and 10-point smoke test stages.

### 1. Safe Dry-Run Preview (Zero Cloud Changes, $0.00 Cost)

```bash
./scripts/gcp/deploy-all.sh --dry-run precise-equator-511303-m1 asia-southeast1
```

### 2. Initialize or Verify Secret Manager Secrets (Interactive or Automated)

```bash
./scripts/gcp/init-secrets.sh precise-equator-511303-m1
```

- Automatically enables `secretmanager.googleapis.com` if not yet active.
- Creates `classlens-production-session-secret`, `classlens-production-teacher-password`, and `classlens-production-live-auth-key` if missing.
- Preserves existing `ENABLED` secret versions on re-runs.
- Generates 256-bit CSPRNG hex values (`openssl rand -hex 32`) for `session-secret` and `live-auth-key`, and prompts with hidden input (`read -rsp`) for `teacher-password` (or reads `CLASSLENS_INIT_TEACHER_PASSWORD` in non-interactive pipelines) without ever printing or logging secret values.

### 3. Full Production Deployment

```bash
./scripts/gcp/deploy-all.sh --confirm precise-equator-511303-m1 asia-southeast1
```

---

## The 13-Stage Automated Workflow

1. **Stage 1 — Tooling, Credentials, Billing & API Validation**: Verifies `gcloud`, `docker`, `terraform`, `python3`, `node`, active GCP identity, billing enablement, and required GCP APIs (`run`, `compute`, `aiplatform`, `storage`, `secretmanager`, `artifactregistry`, `sqladmin`).
2. **Stage 2 — Terraform Static Validation & Billable Resource Audit**: Runs `terraform fmt -check` and `terraform validate` and lists all billable resources before creation.
3. **Stage 3 — PostgreSQL Integration & Migration Readiness**: Verifies `scripts/migrate.py` and schema integrity. Enforces fail-closed protection against container-local SQLite in production.
4. **Stage 4 — Secret Manager Bootstrap & Version Verification**: Invokes `scripts/gcp/init-secrets.sh` in live mode so all 3 application secrets exist and have `ENABLED` versions *before* Cloud Run services are provisioned.
5. **Stage 5 — Artifact Registry Bootstrap & Terraform State Synchronization**: Imports any pre-existing Secret Manager containers or Artifact Registry repositories into Terraform state (preventing HTTP 409 conflicts) and bootstraps `google_project_service.required_apis` and `google_artifact_registry_repository.classlens`.
6. **Stage 6 — Immutable `linux/amd64` Container Image Builds**: Builds multi-stage `linux/amd64` production images for Next.js frontend and FastAPI backend tagged with immutable `sha-<git_commit>` tags (including verified synthetic evaluation fixtures and demo dataset assets).
7. **Stage 7 — Artifact Registry Push**: Authenticates Docker with `${REGION}-docker.pkg.dev` and pushes immutable frontend and backend images.
8. **Stage 8 — Terraform Speculative Plan**: Generates `infra/terraform/tfplan` binding exact immutable image URIs and `enable_cloud_sql=true`.
9. **Stage 9 — Explicit Confirmation Gate**: Requires `--confirm` or interactive `DEPLOY` confirmation before applying infrastructure changes.
10. **Stage 10 — Infrastructure Provisioning**: Applies the verified `tfplan` in strict dependency order: APIs -> Secrets & IAM -> Cloud SQL PostgreSQL 15 -> Cloud Storage -> Cloud Run Private Backend -> Cloud Run Public Frontend BFF -> Cloud Run IAM Invoker Bindings.
11. **Stage 11 — Remote Cloud SQL PostgreSQL 15 Schema Verification**: Executes `python3 scripts/migrate.py --verify-remote "${APP_URL}"` to verify that Cloud Run has initialized all 8 PostgreSQL tables (`users`, `classes`, `students`, `assessments`, `responses`, `audit_events`, `analysis_jobs`, `app_metadata`) at schema version `1.0.0`.
12. **Stage 12 — Comprehensive 10-Point Security & Functional Verification**: Runs `scripts/gcp/verify.sh` to verify Cloud Run HTTPS reachability, Google-managed TLS certificate status, `/` and `/login` rendering, `/health` status via BFF OIDC proxy, unauthenticated `401` enforcement, authenticated `POST /api/v1/auth/login` with `HttpOnly; Secure` session cookies, authenticated `GET /api/v1/assessments`, PostgreSQL health, GCS storage backend, and private backend direct-access `403` IAM lockdown.
13. **Stage 13 — Deployment Summary & Handover**: Outputs the public Cloud Run HTTPS application URL, private backend URL, Cloud SQL connection name, deployed Git SHA revision, and operational runbook commands.

---

## Modular Scripts Reference (`scripts/gcp/`)

| Script | Purpose | Safe Preview Command |
|---|---|---|
| `scripts/gcp/preflight.sh` | Non-destructive prerequisite, billing, API, secret, and schema check | `./scripts/gcp/preflight.sh --dry-run precise-equator-511303-m1 asia-southeast1` |
| `scripts/gcp/init-secrets.sh` | Idempotent Secret Manager container & version bootstrap (zero secret logging) | `./scripts/gcp/init-secrets.sh --dry-run precise-equator-511303-m1` |
| `scripts/gcp/build.sh` | Multi-stage `linux/amd64` Docker build & optional Artifact Registry push | `./scripts/gcp/build.sh --dry-run precise-equator-511303-m1 asia-southeast1` |
| `scripts/gcp/plan.sh` | Speculative Terraform plan generation (`tfplan`) | `./scripts/gcp/plan.sh --dry-run precise-equator-511303-m1 asia-southeast1` |
| `scripts/gcp/deploy.sh` | Applies verified `tfplan` with `--confirm` guard | `./scripts/gcp/deploy.sh --dry-run precise-equator-511303-m1 asia-southeast1` |
| `scripts/gcp/verify.sh` | 10-point post-deployment functional, auth, DB, GCS, and IAM lockdown verification | `./scripts/gcp/verify.sh --dry-run https://classlens-frontend-simulated-as.a.run.app precise-equator-511303-m1` |
| `scripts/gcp/rollback.sh` | Instantaneous Cloud Run traffic rollback to previous revision | `./scripts/gcp/rollback.sh --dry-run precise-equator-511303-m1 asia-southeast1` |
| `scripts/migrate.py` | Idempotent PostgreSQL / SQLite schema migration & remote verification CLI | `python3 scripts/migrate.py --dry-run` |

---

## Monthly GCP Cost Estimate (`asia-southeast1` — Simplified Cloud Run BFF Architecture)

| Resource | Configuration / Guardrail | Est. Monthly Cost (USD) | Est. 14-Day Hackathon Window |
|---|---|---|---|
| **Cloud SQL PostgreSQL 15** | `db-f1-micro` (`ENTERPRISE`, Single-Zone `ZONAL`, `10 GB` SSD, max `20 GB`) | ~$10.55 / mo | ~$4.90 |
| **External HTTPS Load Balancer** | **Eliminated** (Replaced by Cloud Run native Google-managed HTTPS + Next.js BFF OIDC proxy) | **$0.00 / mo** *(saves ~$18.15/mo)* | **$0.00** |
| **Cloud Run (Frontend + Backend)** | `min_instance_count = 0` (scale-to-zero when idle), `max_instance_count = 2`, `1 vCPU / 1 GiB` | ~$0.00 – $1.00 / mo (within free tier for demo traffic) | ~$0.00 – $0.25 |
| **Cloud Storage (`worksheets`)** | Standard regional bucket (`asia-southeast1`), 90-day lifecycle auto-delete | < $0.05 / mo | < $0.02 |
| **Artifact Registry (`classlens-repo`)** | 2 multi-stage container images (~450 MB total; first 0.5 GB free) | < $0.05 / mo | < $0.02 |
| **Secret Manager** | 5 active secret versions (first 6 versions + 10,000 accesses/mo free) | ~$0.00 – $0.06 / mo | ~$0.00 |
| **Vertex AI Gemini Inference** | `gemini-3.8-flash` (`$0.75/1M` input, `$3.75/1M` output; 1 call/worksheet, ~`$0.0045`/worksheet) | ~$0.45 per 100 worksheets | ~$0.45 |
| **Total Estimated Spend** | **~62% reduction vs. Load Balancer architecture (~3.8% of $300 GCP Trial Credit / month)** | **~$11.15 / month** | **~$5.40 / 2 weeks** |
