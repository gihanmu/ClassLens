# ClassLens Google Cloud Platform Deployment Guide

## Target Architecture

- **Region**: `asia-southeast1` (Singapore)
- **Frontend**: Next.js Standalone on Google Cloud Run (Autoscaling 0-5 instances)
- **Backend**: FastAPI Python 3.12 on Google Cloud Run (Autoscaling 0-10 instances)
- **Ingress Strategy**: `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` on both Cloud Run services.
- **Routing**: Global HTTPS External Load Balancer with Serverless NEGs:
  - Default path `/*` -> Frontend Cloud Run NEG
  - API path `/api/*` and `/health` -> Backend Cloud Run NEG
- **Object Storage**: Private Google Cloud Storage Bucket with Uniform Bucket-Level Access.
- **Secrets**: Google Cloud Secret Manager for sensitive environment variables.
- **Container Registry**: Google Cloud Artifact Registry (`docker.pkg.dev/{PROJECT_ID}/classlens-repo`).

---

## Deployment Prerequisites

1. **Google Cloud SDK (`gcloud`)**: Installed and authenticated (`gcloud auth login` and `gcloud auth application-default login`).
2. **Terraform / OpenTofu**: Version 1.5.0 or higher.
3. **Docker**: Running locally for container building and pushing.
4. **Permissions**: The deploying principal requires:
   - `roles/run.admin`
   - `roles/compute.loadBalancerAdmin`
   - `roles/storage.admin`
   - `roles/secretmanager.admin`
   - `roles/artifactregistry.admin`
   - `roles/iam.serviceAccountAdmin`

---

## Deployment Workflow (via `scripts/gcp/`)

ClassLens includes a complete, battle-tested deployment automation suite in `scripts/gcp/`.

### Step 1: Preflight Verification

Verify local tools, active GCP project, and required API enablement:

```bash
./scripts/gcp/preflight.sh
```

This verifies:
- `gcloud`, `docker`, `terraform` binaries.
- Current active GCP project ID.
- Enablement of `run.googleapis.com`, `compute.googleapis.com`, `storage.googleapis.com`, `secretmanager.googleapis.com`, `artifactregistry.googleapis.com`, and `aiplatform.googleapis.com`.

### Step 2: Build & Push Container Images

Build production multi-stage Docker images for both frontend and backend, tag them with git commit SHA and `latest`, and push to Artifact Registry:

```bash
# Dry-run build locally without pushing:
./scripts/gcp/build.sh

# Build and push to Artifact Registry:
./scripts/gcp/build.sh --push
```

### Step 3: Configure Terraform Variables

Create `infra/terraform/terraform.tfvars`:

```hcl
project_id  = "your-gcp-project-id"
region      = "asia-southeast1"
environment = "production"

# Optional domain name for managed SSL certificate:
domain_name = "classlens.yourdomain.edu"

# Cloud SQL PostgreSQL (Set to true for multi-instance production):
enable_cloud_sql = false
```

### Step 4: Plan Terraform Infrastructure

Generate a speculative execution plan:

```bash
./scripts/gcp/plan.sh
```

Inspect the generated `tfplan` to confirm exact resource additions, modifications, or deletions.

### Step 5: Deploy Infrastructure and Workloads

Apply the planned configuration. This script enforces safety checks and requires explicit typing of `DEPLOY` or passing `--confirm`:

```bash
./scripts/gcp/deploy.sh --confirm
```

Outputs will display:
- `load_balancer_ip`: External static IPv4 address.
- `gcs_bucket_name`: Storage bucket for worksheet uploads.
- `frontend_url`: Load balancer frontend endpoint.
- `backend_internal_url`: Cloud Run backend address.

### Step 6: Post-Deployment Verification

Smoke-test the newly deployed environment:

```bash
./scripts/gcp/verify.sh <LOAD_BALANCER_IP_OR_HOSTNAME>
```

The script verifies:
1. Backend `/health` responds with `{"status": "healthy"}`.
2. Frontend `/` loads HTML document.
3. API authentication `/api/v1/auth/me` rejects unauthenticated access with HTTP 401.
4. Security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) are present.

### Step 7: Rollback (Emergency Only)

If an issue is detected post-deployment, roll back traffic immediately to a prior stable revision:

```bash
# Roll back backend to previous revision:
./scripts/gcp/rollback.sh --service backend

# Roll back frontend to specific revision:
./scripts/gcp/rollback.sh --service frontend --revision classlens-web-00003-abc
```

---

## Cloud SQL Migration Path

For multi-instance autoscaling backend deployments:
1. Set `enable_cloud_sql = true` in `infra/terraform/terraform.tfvars`.
2. Apply Terraform to provision a Cloud SQL PostgreSQL instance and service account permissions.
3. Store database URL in Secret Manager (`classlens-database-url`).
4. Set `CLASSLENS_DATABASE_URL` in backend Cloud Run environment variables.
