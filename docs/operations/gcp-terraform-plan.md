# GCP Terraform Infrastructure Plan — ClassLens

**Document ID:** OPS-TER-001
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Replaced Cloud SQL module with **`modules/firestore`** (Google Cloud Firestore Native Mode).
- Added **`modules/tasks`** to provision the regional Cloud Tasks queue (`classlens-analysis-queue`).
- Configured 3 Cloud Run services in `modules/compute`: `web` (public), `api` (public with GIS auth), `worker` (internal-only with OIDC auth).
- Narrowed IAM role bindings: `sa-classlens-api` granted `roles/run.invoker` on worker and `roles/cloudtasks.enqueuer`.

---

## 1. Terraform Architecture & Module Layout

```
infra/terraform/
├── bootstrap/                      # One-time bootstrap for remote state storage
│   ├── main.tf                     # GCS bucket for remote state with versioning
│   └── outputs.tf
├── modules/                        # Reusable infrastructure building blocks
│   ├── services/                   # Enables GCP APIs (run, aiplatform, storage, firestore, tasks)
│   ├── iam/                        # Service accounts & least-privilege IAM bindings
│   ├── storage/                    # Private GCS buckets, retention & CORS rules
│   ├── firestore/                  # Firestore Native Mode database instance
│   ├── tasks/                      # Cloud Tasks queue for async dispatch
│   ├── compute/                    # Cloud Run services (web, api, worker)
│   └── monitoring/                 # Cloud Monitoring alerting policies & budget alerts
└── environments/
    ├── dev/                        # Development / Hackathon Demo stack
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars.example
    └── prod/                       # Production isolated stack (Future)
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## 2. Resource Specifications & Least-Privilege IAM

### 2.1 Google Cloud APIs to Enable (`modules/services`)
- `run.googleapis.com` (Cloud Run serverless containers)
- `storage.googleapis.com` (Cloud Storage private buckets)
- `firestore.googleapis.com` (Firestore Native database)
- `cloudtasks.googleapis.com` (Cloud Tasks async queue)
- `aiplatform.googleapis.com` (Vertex AI Gemini multimodal API)
- `secretmanager.googleapis.com` (Secret Manager runtime secrets)
- `logging.googleapis.com` (Cloud Logging)
- `monitoring.googleapis.com` (Cloud Monitoring)
- `billingbudgets.googleapis.com` (Budget alerts)

### 2.2 Service Accounts & Role Bindings (`modules/iam`)
1. **`sa-classlens-api` (API Service Account)**:
   - `roles/datastore.user` (Read/write Firestore documents).
   - `roles/cloudtasks.enqueuer` (Enqueue response tasks into Cloud Tasks).
   - `roles/run.invoker` on `classlens-worker` service (OIDC token minting).
   - `roles/storage.objectAdmin` on `gs://classlens-source-images-*` (to sign V4 upload URLs).
2. **`sa-classlens-worker` (AI Worker Service Account)**:
   - `roles/aiplatform.user` (Invoke Vertex AI Gemini multimodal inference in `asia-southeast1`).
   - `roles/datastore.user` (Read/write analysis versions and job states).
   - `roles/storage.objectViewer` on `gs://classlens-source-images-*`.
   - `roles/storage.objectAdmin` on `gs://classlens-derived-artifacts-*`.
3. **`sa-classlens-frontend` (Frontend Web Service Account)**:
   - Minimal Cloud Run execution role.

> [!CAUTION]
> **No Primitive Roles**: Neither `roles/owner` nor `roles/editor` will ever be granted to application service accounts.

---

## 3. Storage & Bucket Security Rules (`modules/storage`)

- **Uniform Bucket-Level Access**: Enabled unconditionally.
- **Public Access Prevention**: Enforced (`publicAccessPrevention = "enforced"`).
- **Encryption**: Google-managed encryption keys (`AES-256`).
- **Lifecycle Rule**: Automated deletion of objects older than 30 days (`Age = 30, Action = Delete`).
- **CORS Policy**: Configured to permit `PUT` requests exclusively from authorized ClassLens frontend origins.

---

## 4. Firestore Database Specification (`modules/firestore`)

```hcl
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = "asia-southeast1"
  type        = "FIRESTORE_NATIVE"

  concurrency_mode = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  deletion_policy = "DELETE"
}
```

---

## 5. Cloud Tasks Queue Specification (`modules/tasks`)

```hcl
resource "google_cloud_tasks_queue" "analysis_queue" {
  name     = "classlens-analysis-queue"
  location = "asia-southeast1"

  rate_limits {
    max_concurrent_dispatches = 5
    max_dispatches_per_second = 10
  }

  retry_config {
    max_attempts = 3
    min_backoff  = "2s"
    max_backoff  = "60s"
    max_doublings = 4
  }
}
```

---

## 6. Cloud Run Compute Services (`modules/compute`)

1. **`classlens-web`**:
   - Ingress: `all` (Public)
   - Port: 3000
   - Concurrency: 80
2. **`classlens-api`**:
   - Ingress: `all` (Public with GIS ID token verification)
   - Port: 8000
   - Concurrency: 40
3. **`classlens-worker`**:
   - Ingress: `internal-and-cloud-load-balancing` (Private, no public internet access)
   - Port: 8080
   - Concurrency: 4
   - CPU: `no-cpu-throttling` during request handling
   - Timeout: 300 seconds

---

## 7. State Management & Bootstrap Instructions

### 7.1 State Bootstrap
Remote state is stored in an encrypted GCS bucket with object versioning enabled:
```bash
gcloud storage buckets create gs://classlens-tfstate-<project-id> \
    --location=asia-southeast1 \
    --uniform-bucket-level-access
gcloud storage buckets update gs://classlens-tfstate-<project-id> --versioning
```

### 7.2 Safe Execution Protocol
- No `terraform apply` or `terraform destroy` will ever be run autonomously.
- CI/CD executes `terraform fmt -check`, `terraform validate`, and outputs `terraform plan`.
- Manual user approval is mandatory before any cloud state modification.
