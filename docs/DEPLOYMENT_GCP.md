# ClassLens Google Cloud Platform Deployment Guide

## Target Production Architecture

- **Region**: `asia-southeast1` (Singapore)
- **Frontend**: Next.js Standalone on Google Cloud Run (Autoscaling 0–2 instances, non-root `nextjs` UID 1001)
- **Backend**: FastAPI Python 3.12 on Google Cloud Run (Autoscaling 0–2 instances, non-root `appuser` UID 10001)
- **Ingress Lockdown**: `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` on both Cloud Run services (blocks direct `.run.app` access).
- **Routing**: Global HTTPS External Application Load Balancer with Serverless NEGs:
  - Default path `/*` -> Frontend Cloud Run NEG
  - API paths `/api/*`, `/api`, and `/health` -> Backend Cloud Run NEG
- **Relational Database**: Managed Google Cloud SQL for PostgreSQL 15 (`db-f1-micro` baseline tier) mounted via Cloud SQL Auth Proxy Unix socket (`/cloudsql/...`). Container-local SQLite is strictly prohibited in production.
- **Object Storage**: Private Google Cloud Storage Bucket (`${PROJECT_ID}-classlens-worksheets`) with Uniform Bucket-Level Access and public access prevention enforced.
- **Secrets**: Google Cloud Secret Manager (`classlens-production-session-secret`, `classlens-production-teacher-password`, `classlens-production-live-auth-key`, `classlens-production-database-url`).
- **Container Registry**: Google Cloud Artifact Registry (`${REGION}-docker.pkg.dev/${PROJECT_ID}/classlens-repo`) using immutable Git commit SHA tags (`sha-<commit>`).

---

## One-Command Master Deployment (`scripts/gcp/deploy-all.sh`)

ClassLens provides a single, repeatable master deployment command that orchestrates all 13 validation, bootstrap, packaging, infrastructure provisioning, database migration, and verification stages.

### 1. Safe Dry-Run Preview (Zero Cloud Changes, $0.00 Cost)

```bash
./scripts/gcp/deploy-all.sh --dry-run PROJECT_ID asia-southeast1
```

### 2. Speculative Plan Generation Only

```bash
./scripts/gcp/deploy-all.sh --plan PROJECT_ID asia-southeast1
```

### 3. Full Production Deployment

```bash
./scripts/gcp/deploy-all.sh --confirm PROJECT_ID asia-southeast1
```

---

## The 13-Stage Automated Workflow

1. **Stage 1 — Tooling, Credentials, Billing & API Validation**: Verifies `gcloud`, `docker`, `terraform`, `python3`, `node`, active GCP identity, billing enablement, and required GCP APIs (`run`, `compute`, `aiplatform`, `storage`, `secretmanager`, `artifactregistry`, `sqladmin`).
2. **Stage 2 — Terraform Static Validation & Billable Resource Audit**: Runs `terraform fmt -check` and `terraform validate` and lists all billable resources before creation.
3. **Stage 3 — PostgreSQL Integration & Migration Readiness**: Verifies `scripts/migrate.py` and schema integrity. Enforces fail-closed protection against container-local SQLite in production.
4. **Stage 4 — Secret Manager Verification**: Checks required secret descriptors in Secret Manager without exposing secret payloads.
5. **Stage 5 — Artifact Registry Bootstrap**: Solves the first-time deployment chicken-and-egg dependency by bootstrapping `google_project_service.required_apis` and `google_artifact_registry_repository.classlens` before pushing images.
6. **Stage 6 — Immutable Container Image Builds**: Builds multi-stage production images for Next.js frontend and FastAPI backend tagged with immutable `sha-<git_commit>` tags (mutable `:latest` tags are rejected by Terraform variable validation).
7. **Stage 7 — Artifact Registry Push**: Authenticates Docker with `${REGION}-docker.pkg.dev` and pushes immutable frontend and backend images.
8. **Stage 8 — Terraform Speculative Plan**: Generates `infra/terraform/tfplan` binding exact immutable image URIs and `enable_cloud_sql=true`.
9. **Stage 9 — Explicit Confirmation Gate**: Requires `--confirm` or interactive `DEPLOY` confirmation before applying infrastructure changes.
10. **Stage 10 — Infrastructure Provisioning**: Applies the verified `tfplan` to provision Cloud SQL PostgreSQL, Cloud Storage, Secret Manager bindings, Cloud Run services, Serverless NEGs, and the HTTPS Load Balancer.
11. **Stage 11 — Idempotent Database Migrations**: Executes `python3 scripts/migrate.py` to initialize and verify all 8 production tables (`users`, `classes`, `students`, `assessments`, `responses`, `audit_events`, `analysis_jobs`, `app_metadata`) non-destructively.
12. **Stage 12 — Post-Deployment Security & Routing Verification**: Runs `scripts/gcp/verify.sh` using strict TLS validation (never `curl -k` in production) to verify `/health`, `/`, `/api/v1/auth/me` (HTTP 401), security headers, and Cloud Run direct-ingress lockdown (HTTP 403).
13. **Stage 13 — Deployment Summary & Handover**: Outputs the static Load Balancer IP, application URL, Cloud SQL connection name, deployed Git SHA revision, and operational runbook commands.

---

## Modular Scripts Reference (`scripts/gcp/`)

Each stage can also be invoked independently:

| Script | Purpose | Safe Preview Command |
|---|---|---|
| `scripts/gcp/preflight.sh` | Non-destructive prerequisite, billing, API, secret, and schema check | `./scripts/gcp/preflight.sh --dry-run PROJECT_ID asia-southeast1` |
| `scripts/gcp/build.sh` | Multi-stage Docker build & optional Artifact Registry push with immutable SHA tag | `./scripts/gcp/build.sh --dry-run PROJECT_ID asia-southeast1` |
| `scripts/gcp/plan.sh` | Speculative Terraform plan generation (`tfplan`) | `./scripts/gcp/plan.sh --dry-run PROJECT_ID asia-southeast1` |
| `scripts/gcp/deploy.sh` | Applies verified `tfplan` with `--confirm` guard | `./scripts/gcp/deploy.sh --dry-run PROJECT_ID asia-southeast1` |
| `scripts/gcp/verify.sh` | Strict TLS smoke tests, auth checks, security headers, and ingress lockdown probe | `./scripts/gcp/verify.sh --dry-run https://classlens.yourdomain.edu` |
| `scripts/gcp/rollback.sh` | Instantaneous Cloud Run traffic rollback to previous revision | `./scripts/gcp/rollback.sh --dry-run PROJECT_ID asia-southeast1` |
| `scripts/migrate.py` | Idempotent ANSI SQL / PostgreSQL schema migration & verification CLI | `python3 scripts/migrate.py --dry-run` |

---

## Prerequisites Checklist Before Live Execution (`--confirm`)

1. **Docker Daemon Running**: Ensure Docker Desktop / Docker Engine is running locally before executing a live build (`docker info`).
2. **Populate Secret Manager Versions**: After initial secret container creation (or prior to live student intake), populate secret versions without committing plaintext values:
   ```bash
   echo -n "$(openssl rand -hex 32)" | gcloud secrets versions add classlens-production-session-secret --data-file=- --project=PROJECT_ID
   echo -n "<STRONG_TEACHER_PASSWORD>" | gcloud secrets versions add classlens-production-teacher-password --data-file=- --project=PROJECT_ID
   echo -n "$(openssl rand -hex 32)" | gcloud secrets versions add classlens-production-live-auth-key --data-file=- --project=PROJECT_ID
   ```
3. **Custom Domain & TLS Certificate Validation**: For production HTTPS with a Google-managed certificate, set `domain_name` in `infra/terraform/terraform.tfvars` and point your DNS A-record to the `load_balancer_ip` output.
