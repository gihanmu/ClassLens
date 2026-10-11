# ClassLens — Antigravity Master Engineering Prompt

You are the lead product architect, Google Cloud architect, AI/ML engineer, security architect, and senior full-stack engineer for **ClassLens**, an AI Builder Cup 2026 project.

## 0. Operating instructions

Work in the EXISTING repository at:
`/Users/gihanubayawardana/Documents/Projects/AiBuilder2026/ClassLens/`

**Do not overwrite, move, delete, rename, or re-download the existing datasets.** First inspect repository structure, current code, Git status, docs, configurations, and existing data artifacts. Respect local uncommitted changes. Never open or send all 2,030 images to an AI model. Use metadata-first inspection and a deliberately selected evaluation sample. Ask before executing costly GCP deployments, paid API calls at scale, destructive Terraform operations, or public releases.

The mission is to design and implement a secure, demonstrable, production-oriented MVP. Deliver an end-to-end working vertical slice before expanding functionality. Make reasoned decisions and document trade-offs; do not ask routine questions when a sensible default exists. Where source data does not support a capability, say so and design the capability for future classroom uploads rather than fabricating data.

## 1. Mandatory technology and development rules

1. **Google Skills**: https://github.com/google/skills is the official skills source. Inspect its current README, license, skill manifests, install instructions, actual skill names and versions, and Antigravity compatibility. Install or configure only applicable skills using the repository's supported mechanism. Do not assume earlier descriptions of skill names or installation commands are correct. Keep a `docs/google-skills-inventory.md` explaining which skills were actually found, why each is used, and where it influences implementation. Prefer project-scoped skills; do not blindly install everything or execute unreviewed scripts. Pin revisions/versions where feasible. Skills are development guidance, not the runtime inference engine. Optionally inspect https://github.com/google/agents-cli for complementary official ADK tooling, but `google/skills` remains mandatory.
2. **All AI-related manipulation and processing MUST be in Python**: image preprocessing for inference, Gemini/Vertex AI requests, prompt management, multimodal parsing, agent orchestration, classification, mathematical checking, evaluation, clustering, aggregation of model outputs, retrieval/embeddings if any, and recommendation generation. No Gemini SDK, LLM calls, agent logic, or AI inference in TypeScript/Next.js. Python owns the AI workflow and its business rules. TypeScript is only for UI, presentation, and optionally thin typed BFF/proxy endpoints that do not implement AI logic.
3. **UI**: Next.js App Router, React, TypeScript, responsive and accessible design. Type-safe API contracts with Python, generated OpenAPI client/types or equivalent.
4. **Infrastructure**: Google Cloud Platform exclusively for hosted application services, using Terraform as the source of truth for infrastructure. No manual console-only configuration as a required deployment step. No Firebase/Vercel/AWS as production infrastructure unless explicitly approved.
5. **Deployment**: Prefer Cloud Run for web and Python API, Cloud Run Jobs/Cloud Tasks for async workers as justified. Evaluate Cloud Run services vs jobs, event orchestration, quotas, timeouts, costs, concurrency, GPU need (unlikely), and operational complexity. Use the simplest secure managed GCP architecture that works.
6. **Multi-agent system**: Implement real collaboration with Google Agent Development Kit (ADK) in Python where justified, with specialized roles, tool boundaries, traceable handoffs, deterministic validators, and explicit failure paths. Not every step should be an LLM agent.
7. **Security**: strong security by design, with least privilege, secure data lifecycle, auditability, and no exposed raw student work by default.
8. **Infrastructure as code**: Terraform modules, environments, remote state, CI checks, reproducible bootstrap, and safe deployment instructions.
9. **Reliability and correctness**: structured evidence, explicit uncertainty/abstention, human review, evaluation, and zero fabricated ground truth.
10. **Documentation**: precise requirements, architecture, ADRs, implementation roadmap, developer setup, deployment, runbooks, and demo walkthrough.

## 2. Product vision and boundaries

ClassLens transforms a set of students' handwritten mathematics responses into actionable teaching intelligence. Product promise: **“Marking tells teachers who got it wrong. ClassLens tells them what to teach next.”**

Core scenario: a teacher creates a class and assessment, provides a maths question and its expected solution/rubric, uploads multiple photographed/scanned student responses, launches analysis, reviews AI-supported diagnosis of each answer, sees class-wide misconception patterns, and receives a grounded reteaching plan and formative follow-up activities. Teachers can correct or override the AI output; those edits are audited and can improve evaluation sets, not silently retrain a model.

This is **decision support for educators, not an autonomous high-stakes grading or disciplinary system**. Show what was observed, what is inferred, and how confident the system is. Do not automatically assign definitive grades or student diagnoses without teacher review. The system must gracefully handle diagrams, number lines, arithmetic, algebra, correct alternative methods, ambiguous handwriting, low-quality images, and incomplete submissions.

### Existing dataset

There is an existing **DrawEduMath** download under `datasets/DrawEduMath/`, with approximately 2,030 real student response images organized into 188 problem folders. Inspect actual filesystem rather than assuming exact paths. Known likely artifacts include `metadata/student_answers.csv`, `metadata/problems_index.csv`, `metadata/repository/Data/DrawEduMath_QA.csv`, `problems/problem_<id>/`, and per-problem metadata. The dataset has human teacher descriptions and human teacher QA pairs, plus AI-generated facets and synthetic QA; **never confuse AI-generated annotations with human ground truth**. Some human annotations describe drawings without establishing correctness or a misconception. There is **no persistent student ID** across problems. `Problem ID` identifies a question, not a student. Do not infer or reconstruct identities from handwriting or images. Use dataset row/image IDs as response identifiers for the demo.

Google MathWriting is also present in `mathwriting-2024/`; it contains isolated mathematical expressions, not multi-step student solutions. Do not use it as a misconception ground-truth dataset. Leave it untouched.

Use DrawEduMath only within its actual license and responsible-use conditions (including CC BY-NC restrictions and original ASSISTments terms); verify terms before any hackathon demo, public hosting, redistribution, or commercial usage. Build the public demo to avoid exposing source student images without appropriate permission. Prefer private authenticated demo and/or consented/synthetic examples if licensing is uncertain. US-origin dataset is not evidence of performance on Singapore students. Do not claim a Singapore-specific validated model.

Initial focused example: DrawEduMath Problem **#712487** (if confirmed in local data). It asks about cards −6, +12, −4 and a number-line model. Correct result: **2**. Many answers include arrows, arcs, circled endpoints, handwritten number lines, photos of worksheets, faint/rotated submissions, or no discernible working. Some images contain only a response diagram; the problem statement must be supplied separately. A mathematically valid method can start at −6, move +12 to +6, then −4 to +2. Do not flag that as a misconception merely because it starts at −6. Evaluate multiple valid representations.

## 3. Personas and complete user journeys

Document detailed journeys, permissions, navigation, edge cases, and acceptance criteria for:

**A. Teacher / educator (primary user)**
- Register/sign in (or provision through admin for MVP), view dashboard and own classes.
- Create class/section and assessment; enter question text, math notation, topic, grade band, expected result, acceptable methods, rubric, and optional teacher reference solution.
- Upload multiple JPG/PNG/WebP/PDF answer files via drag-and-drop/mobile camera; optionally bulk import ZIP or dataset-backed demo collection. Associate responses with a pseudonymous student label within the class; never assume DrawEduMath has student identity.
- Preview, rotate, replace, delete, and mark unreadable submissions; view upload/processing status and per-file validation.
- Start analysis, monitor asynchronous progress, retry failures, and cancel where supported.
- Review each student answer with original image, extracted/observed reasoning, final answer if visible, correctness assessment, first verifiable error, misconception category, evidence, confidence, and alternative interpretations. Clearly show when no conclusion is possible.
- Approve/edit/reject AI interpretations, attach notes, record teacher feedback, and flag difficult examples for evaluation.
- Explore class dashboard: distributions of verified errors, possible misconceptions, incomplete/unreadable responses, common first-error patterns, and confidence/coverage. Counts must be based on clearly defined denominators; distinguish AI-proposed from teacher-confirmed labels.
- Generate, edit, approve, and export targeted reteaching activities, differentiated group suggestions, and a short formative exit ticket.
- Export class report as PDF/CSV where appropriate, with data minimization and attribution.
- Manage data retention and deletion, account profile, notification preferences, and privacy controls.

**B. School administrator / organization manager**
- Manage organization, teacher memberships, classes and access policies; optional for MVP but design tenancy and permissions now.
- View usage/operational metrics without unnecessary student-level content; configure retention, permitted file types/size, and privacy policies.
- Review audit trails and handle access/deletion requests within authorized scope.
- No access to unrelated organizations; explicit policy for whether admin can view student work.

**C. AI quality reviewer / curriculum specialist**
- Access only approved/de-identified samples and relevant reference labels.
- Compare AI output against human-reviewed reference annotations, inspect error taxonomies and false positives, annotate disagreements, approve benchmark examples, and run evaluation suites.
- Maintain prompt/agent/evaluation versions; never edit original dataset annotations.

**D. Platform operator / DevOps engineer**
- Deploy via Terraform/CI, observe service health, job queues, costs, error rates, model latency, agent traces with redaction, alerts, backups, and rollback.
- Manage secrets without reading student work by default. Investigate incidents using least-privilege break-glass procedures.

**E. Demo judge / invited observer**
- Read-only, curated, licensed/consented sample assessment and results; cannot see private classes or mutate records. Optionally a guided demo mode with precomputed results clearly identified as such.

Do not add a direct student portal to MVP unless it improves the core judging demo; describe a possible later phase for student feedback with appropriate permissions.

## 4. Functional modules and detailed requirements

Produce numbered, testable requirements with IDs (e.g. AUTH-001, ASM-001, AI-001) and priorities (P0/P1/P2), dependencies, API/data implications, and acceptance criteria. At minimum cover:

1. **Identity, authentication, RBAC and multi-tenancy**: OIDC or Google Identity Platform/Firebase Authentication on GCP as justified; teacher/admin/reviewer/operator/demo roles; org-level isolation; session expiration; authorization on every API and object; service-to-service IAM; rate limiting; CSRF/CORS protections.
2. **Organization, class and pseudonymous student management**: org, class, assessment, class-scoped anonymous student identifiers; membership, archival, access and deletion; no DrawEduMath student linking.
3. **Question and rubric authoring**: question text, LaTeX rendering, grade band, skill/topic tags, expected answer, accepted methods, marking criteria, canonical solution steps, source/attribution, versioning, validation, optional diagram/reference assets.
4. **Assessment lifecycle**: draft → ready → processing → review → published/archived; safe re-analysis and immutable versions.
5. **Image/PDF intake**: presigned/signed upload or secure API design, MIME/content validation, malware scanning strategy, per-file quotas, page extraction, orientation, safe image normalization, metadata stripping, duplicate detection, integrity hashing, storage encryption, upload progress, partial failures, privacy warnings, retention.
6. **Dataset explorer/demo importer**: import metadata for 188 DrawEduMath problems and selected images without copying/redistributing them publicly; browse by problem and annotation quality; keep human and synthetic annotation provenance; use a small controlled demo subset; prevent accidental cross-student grouping.
7. **Asynchronous analysis orchestration**: idempotent jobs, queueing, retries/backoff, dead-letter handling, progress events or polling, concurrency limits, cancellation semantics, budget ceilings, model quotas, and versioned results.
8. **Multimodal interpretation**: read handwriting, symbols, equations, drawings, number-line tick labels, arcs, arrow directions, endpoints, intermediate steps, and ambiguity. Return structured JSON with observed elements and image regions where supportable; do not invent missing work. Include visual-quality classification and abstention.
9. **Math verification**: use Python/SymPy and custom geometry/number-line rule checks where appropriate; compare against expected answer and multiple accepted methods; distinguish correct result vs valid reasoning vs insufficient evidence; deterministic checks must be unit tested.
10. **Error diagnosis**: identify first *supported* erroneous step, error type, likely misconception, alternatives, citations to observed work, severity and confidence; differentiate careless slip from conceptual misunderstanding where evidence permits; use “possible misconception” rather than definitive diagnosis when uncertain.
11. **Cross-response misconception aggregation**: group equivalent error patterns, avoid counting multiple overlapping labels without disclosure, denominator definitions, sample-size caveats, low-confidence exclusion, teacher-confirmed vs AI-proposed breakdowns, class-level summaries.
12. **Reteaching planning**: targeted activities aligned to observed errors, prerequisites, differentiation by error pattern, estimated time, materials, worked examples, check-for-understanding questions, exit ticket, rationale and editable plan; no unsupported pedagogical claims.
13. **Teacher review workflow**: approve/edit/reject, per-field correction, override reason, side-by-side original evidence, audit history, re-analysis without destroying human edits, batch actions where safe.
14. **Dashboards**: assessment overview, status, response list, student-response detail, misconception distribution, per-question analysis, review queue, quality/coverage, teaching plan, export. Responsive desktop/tablet/mobile; accessible charts with text equivalents.
15. **Reports and export**: PDF/CSV, clear “AI-generated / teacher-reviewed” status, source/attribution, no raw student identifiers in aggregated reports by default, authorized downloads only.
16. **AI evaluation workbench**: human-written DrawEduMath captions/QA as *reference evidence*, not automatically as correctness labels; curated manually verified benchmark for correctness, number-line movements, first-error localization, misconception classification, abstention and agent plan usefulness. Keep train/dev/test separation if using dataset for tuning. Version datasets/prompts/models/results; measure agreement and calibration; report failure cases.
17. **Observability and operations**: structured logs, tracing, metrics, cost and token usage, alerting, queue health, redaction, dashboards, SLOs, incident and recovery runbooks.
18. **Settings, privacy, security and compliance**: retention, delete/export, attribution, consent and lawful basis where applicable, encryption, secure defaults, DPA/PDPA considerations for Singapore deployment, region/residency, threat modeling, admin controls, abuse prevention.
19. **Guided hackathon demo**: one-click curated scenario, explainable agent trace, class insight dashboard, before/after teaching plan, optional simulated re-assessment explicitly labelled simulation, predictable latency/cost, fallback precomputed demo clearly disclosed.
20. **Non-functional requirements**: accessibility WCAG 2.2 AA target, performance budgets, scalability, reliability, recoverability, cost, browser support, maintainability, testability, internationalization-ready architecture, data portability.

## 5. Multi-agent design — meaningful responsibilities

Implement Python ADK orchestration with explicit state and typed schemas. Proposed roles (revise if justified, but preserve genuine multi-agent reasoning):

- **Intake & Evidence Agent**: checks question context and image suitability; uses Python image-quality tools; identifies uncertain/partial submissions; does not diagnose math.
- **Visual Reasoning Agent**: calls Gemini multimodal to extract only observable numbers, equations, diagram geometry, arrows, start/end positions, and candidate step sequence, with evidence and uncertainty. Can propose multiple plausible interpretations.
- **Mathematical Reasoning / Diagnosis Agent**: compares extracted reasoning with question/rubric and verified deterministic tool outputs; identifies first supported error and possible misconception; does not claim certainty unsupported by image.
- **Class Insight Agent**: aggregates individual results, finds recurring patterns, validates counts/denominators through Python code, produces grounded class insights. Do not ask an LLM to perform arithmetic aggregation that code can do.
- **Teaching Strategy Agent**: uses grounded class insights and curriculum context to propose differentiated reteaching activities and an exit ticket; explicitly links each recommendation to diagnosed patterns.
- **Quality / Critic Agent**: independently checks logical consistency, evidential grounding, mathematical contradictions, and unsupported claims; routes ambiguous cases to teacher review, not endless agent loops.

Important: deterministic Python services are **tools**, not fake agents: SymPy arithmetic/algebra verifier, number-line movement validator, image metadata/quality processor, schema validator, aggregation/statistics engine, PII filter, and policy checks. Document exact tool contracts and which agents may call which tools. Use typed Pydantic input/output models, explicit agent handoffs, retry limits, per-step model/cost budgets, safety filters, prompt injection defenses for text embedded in uploaded images, and structured provenance. Use a bounded workflow rather than open-ended autonomous execution.

Suggested versioned response schema fields: `response_id`, `assessment_question_id`, `analysis_version`, `source_image_refs`, `quality_status`, `observations[]` (kind, value, evidence_region, confidence), `candidate_interpretations[]`, `inferred_final_answer`, `answer_status` (`correct|incorrect|undetermined`), `reasoning_status` (`supported_correct|supported_error|incomplete|undetermined`), `verified_steps[]`, `first_supported_error`, `misconceptions[]` (taxonomy ID, evidence, confidence), `alternative_valid_methods[]`, `limitations[]`, `needs_teacher_review`, `model_metadata`, `tool_verifications[]`, `teacher_review_status`. Do not fabricate pixel bounding boxes if model output cannot reliably provide them.

Provide sequence diagrams for single response analysis, class aggregation, human review, failed image, retry, and teacher re-analysis. Distinguish agent-generated narratives from deterministic verified values.

## 6. Recommended GCP reference architecture — validate before implementation

- **Frontend**: Next.js TypeScript deployed as container to Cloud Run, server-side auth and protected pages.
- **Backend**: Python FastAPI on Cloud Run; REST/OpenAPI for classes, questions, uploads, analysis jobs, results, reviews, and reports.
- **AI worker**: separate Python Cloud Run service (private) or Cloud Run Jobs for long-running batches; use Cloud Tasks and/or Pub/Sub appropriately. Explain choice based on 10–15-image MVP, execution limits, retries, cost, and concurrency. Prefer asynchronous API with job status.
- **Gemini**: Vertex AI Gemini multimodal in an explicitly selected supported GCP region, using Workload Identity/ADC and service accounts, not embedded API keys.
- **Agent runtime**: Google ADK inside Python worker, with typed tool calls and bounded workflow; do not deploy an additional managed agent runtime unless benefits justify cost and complexity.
- **Image storage**: private Cloud Storage bucket(s), separate source images and derived artifacts, uniform bucket-level access, public access prevention, lifecycle rules, encryption and least privilege; short-lived signed URLs only if needed.
- **Application data**: choose Firestore Native Mode vs Cloud SQL PostgreSQL based on relational needs, transactions, cost, query patterns, Terraform support, tenancy isolation, and operational complexity. Make one firm recommendation and record ADR. A hackathon MVP should avoid unnecessary database complexity.
- **Analytics**: use application DB/Python for MVP class-level counts; BigQuery only when justified for multi-class trends, evaluation datasets, or larger-scale analytics. Do not introduce BigQuery solely to look sophisticated.
- **Secrets**: Secret Manager, no credentials in Git, Terraform state, logs, browser, or images.
- **Observability**: Cloud Logging, Monitoring, Error Reporting, traces with redaction, budget alerts, API quotas, per-assessment cost estimate.
- **Build/deploy**: Artifact Registry, Cloud Build or GitHub Actions via Workload Identity Federation, no long-lived JSON service-account keys; image scanning, CI checks, automated deployment to dev, gated prod.
- **Network/security**: Cloud Run ingress/auth choices, authenticated worker invocation, egress policy if needed, private service access only if required, Cloud Armor/HTTPS load balancer as risk/cost justify; avoid claiming Cloud Run default URL has WAF protection. If public UI/API, secure user auth and API authorization independently of service-to-service IAM.
- **Environment**: dev and prod as distinct Terraform-managed stacks/projects if practical; choose lowest-cost defensible arrangement for hackathon while keeping isolation and reproducibility.
- **Region**: recommend a Singapore region (e.g. `asia-southeast1`) for app/data if supported; check Gemini model/Vertex AI regional availability and document any cross-region processing/data residency implications rather than assuming co-location.

Provide architecture diagram (Mermaid), component/deployment diagram, data flow, trust boundaries, and monthly cost scenarios (demo/low/medium), stating assumptions and using pricing as estimates rather than invented precise amounts.

## 7. Terraform requirements

Create reusable modules and documented stacks for: API/service enablement; Artifact Registry; Cloud Run frontend/API/worker; IAM/service accounts; private GCS buckets; selected DB; Cloud Tasks/PubSub as appropriate; Secret Manager; logging/monitoring/budget alerts; optional DNS/domain and load balancer. Terraform state remote GCS bucket with versioning, access controls, bootstrap instructions, and documented locking/state caveats. No sensitive secret values in Terraform variables/state when avoidable. Explicit dependency ordering, labels, cost controls, deletion protection for critical resources, least privilege, `terraform fmt/validate/plan`, security scanning (`tfsec`/Checkov as feasible), outputs, environment-specific variables, and safe `destroy` policy. Avoid granting project Editor/Owner to application service accounts. Never run `terraform apply` or `destroy` without user approval.

## 8. Security architecture and threat model

Threat-model: cross-tenant data leakage, malicious uploaded content, decompression bombs, image-borne prompt injection, adversarial student text, unauthorized signed URLs, SSRF, IDOR/BOLA, session hijacking, XSS, CSRF, overbroad IAM, secrets exfiltration, malicious dependencies/skills, logs leaking student data, model hallucinations, data retention failure, denial-of-wallet via repeated Gemini requests, and insecure Terraform state. For each specify likelihood/impact, prevention, detection, and test.

Implement security controls including: OIDC-based login; server-side RBAC and tenant scoping on every endpoint; strict input validation; size/page/pixel limits; file signature checks; isolated image processing; non-public buckets; least-privilege IAM; encryption in transit/at rest; authenticated private worker; secure headers and cookies; secret rotation; API quotas/rate limiting; audit trails for review/export/deletion; sanitized logs and model traces; dependency/SBOM/vulnerability checks; retention/deletion workflows; and cost ceilings. Clarify compliance is a design consideration, not legal certification. For real Singapore school deployment, require school/organizational approval, PDPA and relevant MOE/security requirements assessment, consent/lawful basis and appropriate vendor/data processing terms. Do not expose real student images in public demos without rights.

## 9. Frontend UX / design requirements

Build a polished, educator-friendly UI, not an admin-template demo. Key pages:
- Landing/product explanation (public, no real student content)
- Sign-in/invite/access denied
- Teacher dashboard (classes, assessments, recent analyses)
- Class detail and assessment list
- Assessment creation wizard (question → rubric → uploads → review → analyze)
- Bulk upload with progress and per-file feedback
- Processing/status page with safe retries
- Assessment results overview
- Student response detail (original image zoom/rotate, observed working, verification, misconception, evidence, confidence, teacher review)
- Class misconception dashboard (counts, confidence/coverage, grouping, filters, accessible charts)
- Reteaching plan editor and export
- Quality review/evaluation workbench
- Org/settings/retention/audit (role-limited)
- Guided demo mode with licensed/consented or synthetic samples

Responsive across desktop, tablet, mobile. Use accessible semantic controls, keyboard navigation, WCAG 2.2 AA target, color-independent status indicators, clear error/empty/loading states, reduced-motion support, and accessible math via KaTeX/MathJax. Never visually imply a low-confidence AI inference is verified fact. Make demo visually compelling with a transparent “evidence → error pattern → teaching action” narrative.

## 10. Data design and API contracts

Design explicit entities, IDs, tenant keys, indexes, TTL/retention and audit history for: Organization, User, Membership, Class, PseudonymousStudent, Assessment, Question, Rubric, ResponseSubmission, StoredAsset, AnalysisJob, AnalysisVersion, Observation, VerifiedStep, ErrorTaxonomy, MisconceptionFinding, TeacherReview, ClassInsightSnapshot, ReteachingPlan, EvaluationCase, EvaluationRun, AuditEvent, and UsageCostRecord. Only create the entities necessary for the MVP immediately; design migrations/extension points for later.

Provide API endpoints with OpenAPI examples, authentication/authorization matrix, pagination, sorting, validation, idempotency, error codes, job state machine, signed-upload approach, and schema versioning. Frontend consumes typed Python API contracts. Ensure image references never expose raw private bucket paths to unauthorized users.

## 11. Testing and evaluation

Automated testing layers:
- Python pytest for preprocessing, schemas, number-line movement math, SymPy checks, error taxonomy, aggregations, auth and API.
- Contract/integration tests for FastAPI ↔ Next.js and Cloud Storage/DB/queue adapters; mocks/emulators where practical.
- Agent tool and prompt tests with deterministic fixtures, invalid JSON, contradictory interpretations, missing images, prompt injection, and cost limits.
- Playwright end-to-end tests for teacher journeys and access control; accessibility checks.
- Terraform validate/plan and IaC security checks in CI.
- Evaluation set drawn from curated DrawEduMath records with teacher-reviewed labels. Teacher descriptions/QA alone are NOT necessarily ground-truth misconception classifications. Preserve raw source and provenance. Manually verify a modest subset. Include clear images, faint images, rotated images, alternative valid methods, correct final answer but insufficient working, incorrect direction, ambiguous arrowheads, empty response, and out-of-scope diagrams.
- Metrics: extraction accuracy, final-answer correctness, diagram movement interpretation, first-error localization precision/recall, misconception precision/recall (where labels exist), abstention calibration/coverage, teacher override rate, hallucination/evidence rate, latency per response and batch, and approximate cost per response. Define scoring rubrics and minimum release gates; do not invent achieved metrics.

For Problem #712487, create a golden fixture for `-6 + 12 - 4 = 2` with multiple accepted number-line paths. Test that `start=-6 → +12 → -4` is accepted. Do not classify a response from a circled `2` alone as verified correct reasoning.

## 12. Suggested repository layout (adapt to existing structure)

```
ClassLens/
  apps/
    web/                    # Next.js / React / TypeScript
  services/
    api/                    # Python FastAPI
    ai-worker/              # Python ADK, Gemini, tools, evaluation
  packages/
    contracts/              # generated TypeScript/OpenAPI contracts
  infra/
    terraform/
      modules/
      environments/dev/
      environments/prod/
      bootstrap/
  datasets/
    DrawEduMath/            # existing; do not modify originals
  mathwriting-2024/         # existing; leave untouched
  scripts/                  # safe local/dev scripts
  tests/
  docs/
    requirements/
    architecture/
    security/
    operations/
    evaluation/
    google-skills-inventory.md
  .github/workflows/
  README.md
```

Avoid storing large datasets, raw student images, API keys, or Terraform state in Git. Verify `.gitignore` and `.gcloudignore`/Docker contexts. Avoid build context accidentally uploading datasets to Cloud Build.

## 13. Implementation phases and stop/go checkpoints

**Phase 0 — Repository audit and Google Skills setup**
- Inspect existing code/data, repo status, README, project scripts, installed skills and actual Google Skills repository.
- Report what already exists, what must be preserved, skill installation/compatibility, and blockers.

**Phase 1 — Requirements and architecture (FIRST REQUIRED DELIVERABLE)**
- Write complete product requirements with numbered acceptance criteria, personas, user journeys, P0/P1/P2 scope, user stories, security and non-functional requirements.
- Write architecture, multi-agent interaction/sequence diagrams, Terraform plan, data schema, API contract, ADRs, cost/region assumptions, risk register, and detailed milestone backlog.
- Explicitly identify which features are real in MVP vs planned, and any data/rights limitations.
- Present an executive summary, major choices, estimated scope, and decisions needing owner approval. **Stop and request review before broad implementation or cloud provisioning.**

**Phase 2 — Local vertical slice**
- Scaffold Next.js + FastAPI + Python ADK and unit tests.
- Use a curated 10–15 response subset from one problem, initially with local/private image paths and no public redistribution.
- Implement image interpretation → deterministic math check → diagnosis/critic → class aggregation → reteaching recommendation.
- Return structured results, provenance and abstentions; show them in an interactive teacher UI.
- Evaluate against manually reviewed examples; record errors, latency and cost. Only use real Gemini calls after configuring a user-approved project and budget.

**Phase 3 — Secure persistence and classroom workflow**
- Add authentication, RBAC, class/assessment/question/upload lifecycle, asynchronous jobs, review corrections, audit, secure GCS and DB adapters.

**Phase 4 — Terraform and GCP deployment**
- Provision dev environment only with explicit approval; deploy Cloud Run web/API/worker, GCS, DB, queue, Vertex AI access, IAM, observability, CI/CD. Smoke-test, verify costs/security, and document rollback.

**Phase 5 — Hackathon demo hardening**
- Polish dashboard and guided demo, benchmark quality, create privacy-safe demo data, load test, security test, build a concise architecture/evaluation explanation and demo script. Only consider prod deployment with approval.

## 14. Required documentation deliverables

Create or update at least:
- `docs/requirements/product-requirements.md`
- `docs/requirements/personas-and-user-journeys.md`
- `docs/requirements/functional-requirements.md`
- `docs/requirements/non-functional-requirements.md`
- `docs/requirements/mvp-scope-and-acceptance.md`
- `docs/architecture/system-architecture.md` (Mermaid)
- `docs/architecture/agent-design.md` (agents, tools, handoffs, schemas, failure paths)
- `docs/architecture/data-model.md`
- `docs/architecture/api-contracts.md`
- `docs/architecture/architecture-decisions.md`
- `docs/security/threat-model.md`
- `docs/security/privacy-and-dataset-rights.md`
- `docs/operations/gcp-terraform-plan.md`
- `docs/operations/deployment-and-runbook.md`
- `docs/operations/cost-and-capacity.md`
- `docs/evaluation/evaluation-plan.md`
- `docs/evaluation/dataset-curation-plan.md`
- `docs/google-skills-inventory.md`
- `docs/implementation-roadmap.md`

## 15. First response expected from Antigravity

Before writing large amounts of code, respond with:
1. **Repository audit**: actual structure, existing implementation, dataset paths/counts and Git state.
2. **Google Skills verification**: actual relevant skill names, installation plan and whether installation was successful; no invented skills.
3. **Architecture recommendation**: a firm GCP service choice for frontend, API, worker, storage, DB, queue, Gemini and ADK, with alternatives rejected and rationale.
4. **Personas and modules**: full module list and user journeys.
5. **Multi-agent orchestration**: exact responsibilities, typed data flow and deterministic tool boundaries.
6. **Security/privacy**: top risks and controls, including DrawEduMath licensing.
7. **Phased implementation plan**: prioritized tasks, acceptance criteria, MVP vs future scope, cost and testing strategy.
8. **Approval gates**: clearly identify actions requiring user approval.

Then create the Phase 1 documentation files. **Do not launch cloud infrastructure, run paid bulk AI inference, modify source datasets, or begin broad implementation until the architecture and requirements are reviewed.**

Build ClassLens as a trustworthy teacher decision-support product with genuinely useful agentic reasoning, not a superficial multi-agent demo. Optimize for a working, impressive AI Builder Cup vertical slice while keeping the architecture secure, maintainable and extensible.
