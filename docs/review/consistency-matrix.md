# ClassLens — Cross-Document Consistency Matrix

**Document ID:** REV-MAT-003
**Version:** 1.2.1
**Date:** 2026-10-11
**Status:** Verification Complete (Final Technical-Validity Revision)

---

## 1. Cross-Cutting Consistency Matrix

This matrix tracks the final reconciliation of every core architectural topic across all review and planning documents in `docs/`.

| Architectural Topic | Prior Conflict / Ambiguity | Reconciled Single Decision (v1.2.1) | Documents Affected & Updated | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Model Selection & Lifecycle** | Relied on deprecated Gemini 1.5/2.0 Flash models and historical pricing. | **Vertex AI Gemini 3.8 Flash (`gemini-3.8-flash`) in `asia-southeast1` (Singapore)** as primary GA model; `gemini-3.8-pro` as optional complex fallback. Official lifecycle status, launch date (Sep 2, 2026), and GA status verified. | `decision-register.md`, `cost-model.md`, `agent-design.md`, `system-architecture.md`, `cost-and-capacity.md`, `non-functional-requirements.md` | **Resolved** |
| **Vision Tiling & Token Model** | Assumed flat 258 tokens for 1024x1024 images; quoted inaccurate unit costs. | Dynamic vision tiling model: $\le 384\text{px} = 258$ tokens; $768\text{px} \approx 516 – 774$ tokens; $1024\text{px} \approx 1,120 – 1,290$ tokens. Bounded by 768px normalization. Explicitly marked as estimates pending empirical measurement. | `cost-model.md`, `cost-and-capacity.md`, `decision-register.md`, `non-functional-requirements.md` | **Resolved** |
| **Pricing & Cost Amplification** | Outdated $0.00053/response based on obsolete $0.075/$0.30 Gemini 1.5 rates. | Updated to Gemini 3.8 Flash intro rates ($0.75/$3.75 per 1M): **Base response: ~$0.00819 USD**; **Expected with 15% Critic retry: ~$0.00905 USD**; **15-student batch: ~$0.1405 USD** (exact mathematical expectation) or **~$0.1389 USD** (discrete 2 retries). | `cost-model.md`, `cost-and-capacity.md`, `non-functional-requirements.md`, `decision-register.md` | **Resolved** |
| **Queue Reliability & Idempotency** | Assumed Cloud Tasks delivery is unique; lacked lease claim and stale recovery. | **At-least-once delivery documented**. Application-level idempotency via Firestore atomic lease claims (`lease_expires_at = now() + 300s`), deterministic task names (`resp_{id}_{version}`), max 3 retries, and stale job recovery. | `decision-register.md`, `system-architecture.md`, `data-model.md`, `api-contracts.md` | **Resolved** |
| **Queue Identity & Ingress** | Ambiguity between `internal-only` ingress and Cloud Tasks invocation. | Cloud Tasks uses OIDC token for `sa-classlens-tasks`; Worker configured with `--ingress all` and `--no-allow-unauthenticated` (IAM-authenticated private access). | `system-architecture.md`, `security-threat-model.md`, `api-contracts.md`, `threat-model.md` | **Resolved** |
| **Upload Security & Quarantine** | Conflated signed URL parameter checks with server-side file inspection. | Clarified signed URL limits. Uploads go to `raw_quarantine/` with status `UPLOADED_UNVERIFIED`. Worker executes post-upload magic bytes, size (<10MB), dimensions (<4096px), and decompression bomb checks before moving to `validated_images/`. | `security-threat-model.md`, `threat-model.md`, `decision-register.md`, `api-contracts.md` | **Resolved** |
| **Cookie Auth & CSRF** | Vague token transport; lacked explicit CSRF protection on API mutations. | GIS ID token exchanged for `HttpOnly; Secure; SameSite=Lax` cookie (`__session`). Mutations require double-submit CSRF cookie + `X-Requested-With: ClassLens`. | `security-threat-model.md`, `api-contracts.md`, `threat-model.md` | **Resolved** |
| **Prompt Injection Realism** | Claimed SymPy and JSON schemas "completely neutralize" prompt injection. | Acknowledged that multi-layered defense mitigates grading manipulation, but **residual risk remains**: adversarial handwriting can confuse transcription, alter tick marks, or trigger false abstentions. | `security-threat-model.md`, `threat-model.md`, `decision-register.md` | **Resolved** |
| **Agent Inventory & Count** | Inconsistency between 5 vs 6 vs 7 agents across different files. | Standardized to **1 Deterministic Python Service (`ImageQualityService`) + 5 Bounded ADK Agents** (`VisualEvidenceAgent`, `MathInterpretationAgent`, `DiagnosticAgent`, `IndependentCriticAgent`, `CohortIntelligenceAgent`). | `agent-design.md`, `decision-register.md`, `system-architecture.md` | **Resolved** |
| **Gate 2 Deterministic Scope** | Ambiguity whether Python tools read handwritten images directly. | Corrected: Deterministic Python tools (`SymPyChecker`, `NumberLineDisplacementCalculator`) validate structured observation vectors and synthetic fixtures representing Problem #1065658; they do **not** interpret raw handwritten pixels without Gemini. | `implementation-gates.md`, `implementation-roadmap.md`, `decision-register.md` | **Resolved** |
| **Live Feasibility Test Caps** | Claimed guaranteed $0.15 hard cap at billing layer. | Replaced with estimated budget ($\approx \$0.12 – \$0.14\text{ USD}$), enforced application quota (`MAX_TEST_RESPONSES = 13`), and a **$0.50 stop-on-threshold circuit breaker**. Documented residual billing risk. | `implementation-gates.md`, `cost-model.md`, `implementation-roadmap.md` | **Resolved** |
| **Accessibility Verification Status** | Claimed Playwright tests prove WCAG 2.2 AA compliance. | Clarified that Playwright / `@axe-core` tests are automated linters detecting baseline rules, **not proof of full WCAG 2.2 AA compliance**, which requires human manual assistive technology audits. | `implementation-gates.md`, `implementation-roadmap.md`, `non-functional-requirements.md` | **Resolved** |
| **Evaluation Provenance & Labels** | Synthetic QA mixed with teacher notes; claims of multi-expert consensus. | All 13 labels classified as **provisional**. Provenance split: Teacher notes (descriptive evidence) vs Synthetic QA (barred from golden benchmarking). Double-blind adjudication workflow added. | `evaluation-readiness.md`, `evaluation-plan.md`, `decision-register.md` | **Resolved** |
| **Answer vs Reasoning Status** | Conflated final answer correctness with reasoning correctness. | Explicit separation of `answer_status` from `reasoning_status` (e.g. Row 11 has correct answer but incomplete reasoning; Row 4 has correct answer with compensatory errors; Row 6 has correct number line with wrong circled answer). | `evaluation-readiness.md`, `evaluation-plan.md`, `data-model.md` | **Resolved** |
| **Cost Safeguards & Kill Switch** | Claimed "absolute financial containment"; kill switch only on API layer. | Removed absolute containment claims. Added **worker pre-inference kill switch** checked immediately before every Vertex AI call (including already-queued tasks). Documented that Cloud Storage free tier does NOT apply in Singapore. | `cost-model.md`, `cost-and-capacity.md`, `security-threat-model.md`, `decision-register.md` | **Resolved** |

---

## 2. Document Verification Sign-Off

All 7 review documents in `docs/review/` and all affected planning documents across `docs/` have been audited and updated to version `1.2.1` in complete alignment with this consistency matrix.
