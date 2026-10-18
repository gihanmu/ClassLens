# ClassLens — Live Google Cloud Production Deployment Report

**Date:** 18 October 2026  
**Team:** Token Titans (AI Builder Cup 2026)  
**Deployment Status:** **LIVE & VERIFIED (ALL 12/12 CHECKS PASSED)**  
**Production HTTPS URL:** **[https://classlens-frontend-zd46yyht3q-as.a.run.app](https://classlens-frontend-zd46yyht3q-as.a.run.app)**

---

## 1. Executive Summary & Production Endpoints

ClassLens has been deployed to Google Cloud Platform (`precise-equator-511303-m1`) in the Singapore region (`asia-southeast1`) using the cost-optimised, serverless Cloud Run BFF architecture (`~$11/month`, saving `$20+/month` by eliminating the external Global Application Load Balancer).

| Component | Production Value / Resource Identifier | Status |
| :--- | :--- | :--- |
| **Public Production HTTPS URL** | **`https://classlens-frontend-zd46yyht3q-as.a.run.app`** | **ACTIVE (`HTTP 200`, Google-Managed TLS)** |
| **Frontend Cloud Run Service** | `classlens-frontend` (`asia-southeast1`, `min=0, max=2`, `1 vCPU / 1 GiB`) | **ACTIVE (`allUsers` Invoker)** |
| **Private Backend Cloud Run Service** | `classlens-backend` (`https://classlens-backend-zd46yyht3q-as.a.run.app`) | **ACTIVE (Private IAM OIDC Only — `HTTP 403` to public)** |
| **Database Engine** | Cloud SQL for PostgreSQL 15 (`classlens-production-pg`, `db-f1-micro`, `10 GB` Zonal SSD) | **HEALTHY (`schema_version=1.0.0`)** |
| **Worksheet Object Storage** | Google Cloud Storage (`precise-equator-511303-m1-classlens-worksheets`) | **ACTIVE (`storage_backend=gcs`, `PAP=enforced`)** |
| **Artifact Registry** | `asia-southeast1-docker.pkg.dev/precise-equator-511303-m1/classlens-repo` | **ACTIVE (`sha-9da60ab` immutable images)** |
| **Vertex AI Live Model** | `gemini-3.8-flash` (`GOOGLE_CLOUD_LOCATION=global`) | **ACTIVE & VERIFIED (`is_mock=False`)** |

---

## 2. Deployed Service Accounts, IAM & Secret Manager Posture

### Least-Privilege Service Accounts
- **Frontend Service Account (`classlens-frontend-sa@precise-equator-511303-m1.iam.gserviceaccount.com`):**
  - Granted `roles/run.invoker` exclusively on `classlens-backend`.
  - Mints short-lived Google OIDC identity tokens via the Cloud Run metadata server inside Next.js App Router BFF routes (`/api/[...path]/route.ts` and `/health/route.ts`).
  - Zero access to Cloud SQL, GCS, Secret Manager, or Vertex AI.
- **Backend Service Account (`classlens-backend-sa@precise-equator-511303-m1.iam.gserviceaccount.com`):**
  - `roles/aiplatform.user` (Vertex AI `gemini-3.8-flash` multimodal inference)
  - `roles/cloudsql.client` (Unix socket connection at `/cloudsql/precise-equator-511303-m1:asia-southeast1:classlens-production-pg`)
  - `roles/storage.objectUser` on bucket `precise-equator-511303-m1-classlens-worksheets`
  - `roles/secretmanager.secretAccessor` on the 4 mounted runtime secrets

### Secret Manager Secrets (All Populated with `ENABLED` Versions)
1. `classlens-production-session-secret` -> Mounted as `SECRET_KEY`
2. `classlens-production-teacher-password` -> Mounted as `CLASSLENS_DEMO_PASSWORD`
3. `classlens-production-live-auth-key` -> Mounted as `CLASSLENS_LIVE_AUTH_KEY`
4. `classlens-production-database-url` -> Mounted as `CLASSLENS_DATABASE_URL`
5. `classlens-production-db-password` -> Managed by Terraform for `classlens_app` PostgreSQL user

*Note: Zero secret values, passwords, or tokens are printed in deployment logs or stored in source control.*

---

## 3. Production Smoke Test & Live Gemini Verification Results

Executed via `./scripts/gcp/verify.sh --with-live-gemini "https://classlens-frontend-zd46yyht3q-as.a.run.app" precise-equator-511303-m1`:

| Check | Verification Target | Result | Measured Details |
| :--- | :--- | :--- | :--- |
| **[1/12]** | Public Cloud Run HTTPS & BFF OIDC Proxy (`/health`) | **PASS** | `HTTP 200 OK` |
| **[2/12]** | Google-Managed TLS Certificate Handshake | **PASS** | `CN=*.a.run.app`, Issuer: `Google Trust Services (WR2)` |
| **[3/12]** | Frontend Root (`/`) & Login Page (`/login`) | **PASS** | `/` -> `HTTP 200` (`0.059s`), `/login` -> `HTTP 200` (`0.047s`) |
| **[4/12]** | Backend Health Payload & Security Headers | **PASS** | `status=ok`, `ai_mode=live`, `is_live_authorized=true`, `gemini_model=gemini-3.8-flash`, `database_backend=postgresql`, `storage_backend=gcs`; headers `x-correlation-id`, `x-content-type-options`, `x-frame-options` verified |
| **[5/12]** | Unauthenticated API Protection (`/api/v1/assessments`) | **PASS** | Rejected unauthenticated request with `HTTP 401 Unauthorized` |
| **[6/12]** | Authenticated Teacher Login (`POST /api/v1/auth/login`) | **PASS** | `HTTP 200 OK`; `HttpOnly; Secure; SameSite=Lax` `__session` cookie issued |
| **[7/12]** | Authenticated Assessment Listing (`GET /api/v1/assessments`) | **PASS** | `HTTP 200 OK` |
| **[8/12]** | Assessment Persistence in Cloud SQL PostgreSQL 15 | **PASS** | Verified assessment `asm_f5fa57d1` in PostgreSQL |
| **[9/12]** | Worksheet Upload to GCS, Binary Image Retrieval & Cohort Insights | **PASS** | Uploaded worksheet to GCS (`HTTP 201`), downloaded sanitized PNG (`HTTP 200`), verified `/api/v1/assessments/asm_1065658/insights` (`HTTP 200`) |
| **[10/12]** | Cloud SQL PostgreSQL 15 Health & Schema Version | **PASS** | `database_backend=postgresql`, `database_healthy=True`, `schema_version=1.0.0` |
| **[11/12]** | Private GCS Storage & Direct Backend IAM Lockdown | **PASS** | `storage_backend=gcs`; direct unauthenticated call to `https://classlens-backend-zd46yyht3q-as.a.run.app/health` rejected with `HTTP 403 Forbidden` |
| **[12/12]** | Controlled Single-Worksheet Live Gemini 3.8 Flash + SymPy Check | **PASS** | `status=COMPLETED \| model=gemini-3.8-flash \| is_mock=False \| answer=incorrect \| reasoning=supported_error \| misconception=MISC-LINE-INTERVAL-MISLABEL` |

---

## 4. Infrastructure Cost & Budget Protection Summary

| Resource | Configuration | Estimated Monthly Cost (USD) |
| :--- | :--- | :--- |
| **Cloud Run (`classlens-frontend` & `classlens-backend`)** | `min_instance_count = 0`, `max_instance_count = 2`, `1 vCPU / 1 GiB` | `$0.00` (Covered by Cloud Run Free Tier + scales to zero when idle) |
| **External HTTPS Load Balancer** | Removed (Replaced by native Cloud Run Google-managed HTTPS + OIDC BFF Proxy) | `$0.00` (Saved `~$20.25/month`) |
| **Cloud SQL for PostgreSQL 15** | `db-f1-micro`, `ENTERPRISE`, `ZONAL`, `10 GB` SSD, no backups | `~$11.07/month` (`~$0.37/day`) |
| **Cloud Storage + Artifact Registry + Secret Manager** | `< 1 GB` storage, 5 active secrets | `< $0.30/month` |
| **Vertex AI (`gemini-3.8-flash`)** | Pay-per-use (`~$0.004` per analyzed worksheet) | `~$0.004` per live worksheet |
| **Total Estimated Monthly Run-Rate** | **Full Production Stack** | **`~$11.37 / month`** |
