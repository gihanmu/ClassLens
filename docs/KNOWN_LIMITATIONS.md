# ClassLens Known Limitations & Technical Constraints

## 1. Database Architecture & Multi-Instance Concurrency
- **Current State**: ClassLens uses SQLite (`classlens.db`) by default. SQLite operates with single-writer WAL mode on a shared local volume.
- **Limitation**: In a serverless container environment like Google Cloud Run where container instances scale dynamically from 0 to N, an ephemeral local SQLite database cannot be shared across multiple concurrent container instances.
- **Production Resolution**: For multi-instance Cloud Run deployments, set `enable_cloud_sql = true` in Terraform to provision a managed PostgreSQL database, or run with `max_instances = 1` if using a single serverless instance.

---

## 2. Mathematical Task Domains
- **Current Supported Domains**:
  1. `INTEGER_OPERATIONS_NUMBER_LINE`: Directed integer arithmetic (-6 + 12 - 4) with interval counting, vectors, and hops.
  2. `FRACTION_DIVISION`: Rational division (e.g. 8/9 ÷ 4/9) via unit form, visual tape models, and invert-and-multiply algorithms.
- **Limitation**: Freeform word problems, multi-variable algebraic proofs, geometric constructions, and calculus are not currently verified symbolically.
- **Behavior**: The `TaskRouter` identifies unsupported domains and gracefully flags submissions as `UNSUPPORTED_TASK` rather than hallucinating answers.

---

## 3. Teacher Authentication & Identity Model
- **Current State**: Single-teacher authentication model with Argon2id password hashing, session tokens, and sliding-window rate limiting.
- **Limitation**: Does not currently include multi-tenant organization self-registration, student accounts, or automated enterprise Single Sign-On (SAML 2.0 / Google Workspace OAuth).
- **Roadmap**: Google Identity Services (SiwG) and Clever / Canvas LMS LTI 1.3 integrations are planned for subsequent milestones.

---

## 4. Serverless Cold Starts
- **Current State**: Cloud Run services are configured to scale to zero instances during idle periods (`min_instances = 0`) to achieve zero baseline hosting cost ($0.00/mo when idle).
- **Limitation**: The first incoming request after an idle window experiences a 1.2s to 2.5s container cold-start delay (Node.js runtime bootstrapping or Python Uvicorn initialization).
- **Mitigation**: Setting `min_instances = 1` in `infra/terraform/cloud_run.tf` maintains a warm instance 24/7 if sub-second latency is required during scheduled school hours.

---

## 5. Visual Handwriting Artifacts & Lighting
- **Current State**: Submissions with illegible handwriting, severe camera blur, extreme perspective distortion, or incomplete edge cropping are classified as `Insufficient Evidence` requiring teacher review.
- **Design Decision**: This is an intentional educational safety guarantee to prevent false diagnostic attributions.
