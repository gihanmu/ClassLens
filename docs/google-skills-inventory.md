# Google Skills Inventory & Verification Report — ClassLens

**Document ID:** OPS-SKL-001
**Version:** 1.1.0
**Date:** 2026-10-11
**Project:** ClassLens (AI Builder Cup 2026)
**Official Skill Repositories:** `https://github.com/google/skills` & `https://github.com/google/agents-cli`
**Lockfile:** [`skills-lock.json`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/skills-lock.json)

---

### Changelog (v1.1.0)
- Verified all 16 installed project-scoped skills against `skills-lock.json` SHA256 hashes.
- Reconciled worker implementation path to `services/worker/`.
- Re-confirmed exclusion of heavy infrastructure skills (GKE, BigQuery, AlloyDB).

---

## 1. Executive Summary & Verification

In accordance with Section 1 of `ClassLens_Master_Prompt.md`, the official repository `google/skills` and complementary ADK tooling `google/agents-cli` were inspected directly against remote source manifests and the local environment using `npx -y skills add`.

Antigravity agent integration was automatically confirmed by the tooling (`antigravity Agent detected — installing non-interactively`), and **16 project-scoped skills** were installed and pinned into `.agents/skills/` with SHA256 hashes locked in `skills-lock.json`.

Skills act as **development guidance, architectural guardrails, and operational runbooks** during engineering. Runtime execution is handled strictly by the Python backend utilizing the Google Agent Development Kit (ADK) and Vertex AI Gemini SDK.

---

## 2. Pinned Skill Inventory & Implementation Influence

| Skill Name | Source Repository | Computed Hash (skills-lock.json) | Purpose & Rationale | ClassLens Implementation Influence |
| :--- | :--- | :--- | :--- | :--- |
| **`cloud-run-basics`** | `google/skills` | `a0446f5d...` | Baseline configuration for containerized serverless hosting on Cloud Run. | Governs Dockerfiles, concurrency tuning, memory limits, and cold-start mitigations for `web`, `api`, and `worker`. |
| **`cloud-run-alert-configuration`** | `google/skills` | `e72e26e8...` | Standardized alerting policies for Cloud Run service health. | Influences Terraform alerting modules for 5xx errors, latency spikes, and worker container crashes. |
| **`google-cloud-storage-basics`** | `google/skills` | `8d243a55...` | Best practices for private GCS bucket management, uniform bucket-level access, and signed URLs. | Dictates private bucket architecture, short-lived V4 signed URLs for uploads/previews, and lifecycle retention policies. |
| **`google-cloud-recipe-auth`** | `google/skills` | `243d9127...` | Google Cloud IAM authentication patterns and service account least privilege. | Used to architect Workload Identity, service-to-service OIDC tokens between API and AI workers. |
| **`iam-helper-for-policy-management`** | `google/skills` | `8101f343...` | Policy definitions and boundary checks. | Ensures Terraform IAM role assignments are strictly least-privilege without wildcard permissions. |
| **`gemini-api`** | `google/skills` | `9f9d2663...` | Vertex AI Gemini multimodal API patterns, structured outputs, and token management. | Guides Python multimodal prompts, vision resolution parameters, JSON schema enforcement, and temperature controls. |
| **`agent-platform-inference`** | `google/skills` | `8a22f596...` | Inference lifecycle management, retries, exponential backoff, and quota protection. | Applied in AI Worker for managing Vertex AI Gemini rate limits, backoff strategies, and cost ceilings. |
| **`cloud-logging-configuration-basics`** | `google/skills` | `7c317c0e...` | Structured logging best practices in GCP. | Dictates Python structured JSON logging format and PII redaction filters to prevent student handwriting leaks in logs. |
| **`cloud-trace-querying`** | `google/skills` | `4ca041fb...` | Distributed tracing for multi-tier microservices. | Informs OpenTelemetry trace propagation across Next.js BFF -> FastAPI -> AI Worker background processing. |
| **`google-cloud-waf-security`** | `google/skills` | `ab0c355c...` | Google Cloud Well-Architected Framework: Security pillar. | Defines defense-in-depth controls: HTTPS enforcement, non-public storage, image sanitize pipeline, and tenant isolation. |
| **`google-cloud-waf-cost-optimization`** | `google/skills` | `694ea330...` | Google Cloud Well-Architected Framework: Cost Optimization pillar. | Informs zero-scale Cloud Run configuration, batch token budgeting, evaluation sample limits, and billing budget alerts. |
| **`google-cloud-solution-n-tier-serverless-web-app`** | `google/skills` | `ee97e202...` | Architecture blueprint for multi-tier serverless applications. | Informs frontend (Next.js) -> public API (FastAPI) -> private async worker (`services/worker`) topology. |
| **`sign-in-with-google-web`** | `google/skills` | `f8d9074e...` | Web client Sign in with Google (GIS) integration and backend token verification. | Dictates GIS integration on Next.js client and Google ID token validation on FastAPI backend. |
| **`google-agents-cli-onboarding`** | `google/skills` | `df6fc4a6...` | ADK framework onboarding and toolchain setup. | Bridges Google Agent Development Kit CLI tooling with the ClassLens development workflow. |
| **`google-agents-cli-adk-code`** | `google/agents-cli` | `76004328...` | Code patterns for Google ADK: tool binding, callbacks, state management, graph workflows. | Core reference for implementing Python ADK agents (`VisualEvidenceAgent`, `DiagnosticAgent`, etc.) with Pydantic contracts. |
| **`google-agents-cli-workflow`** | `google/agents-cli` | `bd4e5011...` | End-to-end agent development lifecycle and testing guidelines. | Defines our deterministic test-first approach: tool tests, mocking multimodal calls, state graph verification. |

---

## 3. Skills Evaluated and Excluded

The following skills from `google/skills` were evaluated and intentionally excluded:
1. **GKE Skills (`gke-*`)**: Excluded; ClassLens uses serverless Cloud Run. GKE incurs unnecessary baseline cluster costs ($70+/month) incompatible with hackathon MVP requirements.
2. **BigQuery AI/ML Skills (`bigquery-*`)**: Excluded; MVP cohort aggregations are calculated deterministically in Python and stored in Firestore. BigQuery is deferred to Phase 5+ enterprise scaling.
3. **Google Mobile Ads / Marketing Skills (`google-ads-*`, `google-mobile-ads-*`)**: Excluded; irrelevant to educational assessment software.
4. **AlloyDB / Spanner Skills (`alloydb-basics`, `spanner-basics`)**: Excluded; disproportionately expensive and complex for a classroom MVP.
