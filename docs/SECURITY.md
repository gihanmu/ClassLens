# ClassLens Security & Compliance Architecture

## Security Overview

ClassLens is engineered with educational privacy, zero-trust infrastructure, and least-privilege principles at its foundation. It protects sensitive student assessment data, teacher credentials, and cloud runtime environments.

---

## Authentication & Session Security

### 1. Password Hashing with Argon2id
- Teacher passwords are never stored in plaintext or with deprecated algorithms (e.g., MD5, SHA-1, unkeyed SHA-256).
- Hashing is implemented using **Argon2id** (`argon2-cffi`), the state-of-the-art memory-hard hashing function recommended by OWASP:
  - Time cost: 3 iterations
  - Memory cost: 65,536 KiB (64 MiB)
  - Parallelism: 4 threads
- Salting is automatic, cryptographically random, and unique per credential.

### 2. Session Management
- Teacher authentication produces cryptographically signed session tokens.
- Cookies are issued with strict defensive attributes:
  - `HttpOnly`: Prevents client-side scripts from reading tokens via XSS.
  - `SameSite=Lax`: Defends against Cross-Site Request Forgery (CSRF).
  - `Secure`: Mandated in production so cookies are transmitted exclusively over encrypted TLS connections.
- Sessions include automatic sliding-window expiration.

### 3. Login Brute-Force Rate Limiting
- The `/api/v1/auth/login` endpoint is protected by `LoginRateLimiter`:
  - Enforces a sliding 60-second window.
  - Restricts failed attempts to a maximum of 5 per client IP address and account identifier.
  - Exceeding the threshold triggers HTTP 429 (`Too Many Requests`) with a detailed retry-after interval.
  - Successful logins clear the failure tally immediately.

---

## Authorization & Multi-Tenant Data Isolation

- **Tenant Scoping (`org_id`)**: Every database record (assessments, student submissions, teacher reviews, action plans) is bound to an organization identifier (`org_id`).
- **Query Sandboxing**: Repository operations enforce tenant filters at the database engine level (`WHERE org_id = :org_id`).
- **File Storage Partitioning**: Uploaded worksheet images are stored within isolated directories or GCS prefixes (`uploads/{org_id}/{assessment_id}/{filename}`), preventing directory traversal or cross-tenant inspection.

---

## Infrastructure & Container Hardening

### 1. Non-Root Execution
- **Frontend Container**: Runs as unprivileged user `nextjs` (UID 1001, GID 1001).
- **Backend Container**: Runs as unprivileged user `appuser` (UID 10001, GID 10001).
- No container in the deployment topology runs with root privileges.

### 2. Multi-Stage Docker Builds
- Build dependencies (compilers, npm build caches, intermediate files) are completely discarded in intermediate stages.
- Production images contain only the compiled standalone JavaScript bundle or the installed Python runtime wheelhouse.

### 3. Ingress Restriction & Private Cloud Run
- Both Cloud Run services are configured with:
  ```hcl
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  ```
- Public requests cannot reach the Cloud Run `.run.app` default domains.
- All ingress must pass through the Google Cloud HTTPS Load Balancer with verified SSL certificates.

---

## Cloud IAM & Secrets Management

### 1. Least-Privilege Service Accounts
- Dedicated backend service account: `sa-classlens-backend@{PROJECT_ID}.iam.gserviceaccount.com`.
- Minimal granted roles:
  - `roles/aiplatform.user`: Required for Vertex AI Gemini inference.
  - `roles/storage.objectUser`: Scoped specifically to the private worksheet bucket.
  - `roles/secretmanager.secretAccessor`: Access to secrets stored in Secret Manager.
  - `roles/cloudtrace.agent` & `roles/logging.logWriter`: Telemetry and logging.
- No broad admin roles (`Editor`, `Owner`) are granted to runtime identities.

### 2. Secrets Management
- Sensitive values (`CLASSLENS_SECRET_KEY`, database credentials) are managed in Google Cloud Secret Manager.
- Secrets are mounted directly into Cloud Run container environments via native Cloud Run secret references, avoiding disk writes or shell environment leakage.

---

## HTTP Security Headers & Network Controls

The backend injects standard security headers via `SecurityHeadersMiddleware`:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-sniffing attacks |
| `X-Frame-Options` | `DENY` | Protects against UI redressing / Clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects referrer privacy across domains |
| `X-Correlation-ID` | Unique UUID4 | Distributed request traceability |

In production, CORS is restricted strictly to authorized origins specified in `CLASSLENS_CORS_ORIGINS`. Wildcard `*` origins are strictly prohibited when credentials are enabled.
