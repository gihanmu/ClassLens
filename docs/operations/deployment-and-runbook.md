# Deployment Guide & Operations Runbook — ClassLens

**Document ID:** OPS-RNK-002
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Corrected Python service packaging path from hyphenated `services/ai-worker/` to **`services/worker/`**.
- Added complete Docker build, push, and deploy instructions for the AI Worker container.
- Added local Google Cloud Firestore Emulator and inline task adapter setup instructions.
- Added worker OIDC IAM invoker permission bindings and health checks.

---

## 1. Local Development Setup & Quickstart

### Prerequisites
- Node.js v20+ & npm / npx
- Python 3.12+ (managed via `uv` or system Python)
- Google Cloud SDK (`gcloud` CLI with Firestore emulator component)

### 1.1 Local Workspace Initialization
```bash
# 1. Clone & enter repository
cd /path/to/ClassLens

# 2. Setup Python environment for backend & worker
uv venv .venv
source .venv/bin/activate
uv pip install -r services/api/requirements.txt
uv pip install -r services/worker/requirements.txt

# 3. Setup Frontend dependencies
cd apps/web && npm install && cd ../..

# 4. Start Local Firestore Emulator (Terminal 1)
gcloud beta emulators firestore start --host-port=127.0.0.1:8080

# 5. Export Emulator Environment Variable in your shell
export FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
export LOCAL_TASK_DISPATCH="inline"

# 6. Verify Local Unit Test Suite (runs offline without cloud credentials)
pytest tests/unit/
```

### 1.2 Running Local Vertical Slice
```bash
# Terminal 2: Run FastAPI backend (port 8000)
uvicorn services.api.main:app --reload --port 8000

# Terminal 3: Run Next.js frontend (port 3000)
cd apps/web && npm run dev
```

---

## 2. Cloud Deployment Runbook (Dev Environment)

### 2.1 Pre-Flight Check & Approvals
Before any cloud deployment:
1. Confirm GCP project ID: `gcloud config get-value project`
2. Ensure user has approved budget ceiling ($50 USD max).
3. Review `terraform plan` output.

### 2.2 Container Build & Push (All 3 Components)
```bash
# Authenticate Docker with GCP Artifact Registry
gcloud auth configure-docker asia-southeast1-docker.pkg.dev

# 1. Build & Push API Image
docker build -t asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/api:v1.1.0 services/api/
docker push asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/api:v1.1.0

# 2. Build & Push Worker Image
docker build -t asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/worker:v1.1.0 services/worker/
docker push asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/worker:v1.1.0

# 3. Build & Push Frontend Image
docker build -t asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/web:v1.1.0 apps/web/
docker push asia-southeast1-docker.pkg.dev/<PROJECT_ID>/classlens/web:v1.1.0
```

### 2.3 Terraform Provisioning
```bash
cd infra/terraform/environments/dev
terraform init
terraform plan -out=tfplan
# REQUEST USER APPROVAL BEFORE PROCEEDING
terraform apply tfplan
```

### 2.4 Cloud Run Service Deployment Verification
```bash
# Verify API Service (Public with GIS Auth)
gcloud run services describe classlens-api --region=asia-southeast1

# Verify Worker Service (Internal Only)
gcloud run services describe classlens-worker --region=asia-southeast1

# Verify Worker Ingress is Restricted
gcloud run services get-iam-policy classlens-worker --region=asia-southeast1
```

---

## 3. Incident Response & Troubleshooting Runbooks

### Incident 1: Vertex AI Rate Limiting (HTTP 429)
- **Symptom**: Cloud Run worker logs report `ResourceExhausted: 429 Quota exceeded for aiplatform.googleapis.com`.
- **Immediate Mitigation**: Cloud Tasks automatically retries with exponential backoff (2s, 4s, 8s). If quota remains saturated, throttle Cloud Tasks dispatch concurrency via gcloud:
  ```bash
  gcloud tasks queues update classlens-analysis-queue \
      --max-concurrent-dispatches=2 \
      --location=asia-southeast1
  ```
- **Root Cause Fix**: Request Vertex AI quota increase in GCP Console or switch region to secondary endpoint (`asia-east1`).

### Incident 2: Decompression Bomb Image Upload
- **Symptom**: Worker rejects upload with `422 Unprocessable Entity` or terminates due to memory exhaustion.
- **Mitigation**: Pillow `Image.MAX_IMAGE_PIXELS = 16_000_000` prevents excessive memory allocation. Files triggering `DecompressionBombError` are quarantined and logged.

### Incident 3: Break-Glass Rollback
```bash
# Roll back Cloud Run service to previous stable revision
gcloud run services update-traffic classlens-api \
    --to-revisions=classlens-api-00001-abc=100 \
    --region=asia-southeast1

gcloud run services update-traffic classlens-worker \
    --to-revisions=classlens-worker-00001-abc=100 \
    --region=asia-southeast1
```
