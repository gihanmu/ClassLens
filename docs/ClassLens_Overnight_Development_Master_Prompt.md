# ClassLens — Overnight Autonomous Development Master Prompt

## Mission
You are the lead coding agent for the **existing** ClassLens repository (`gihanmu/ClassLens`). Finish the application locally, end to end: repair defects, implement reliable SQLite database and image persistence, complete teacher workflows, redesign the UI elegantly, run only offline tests, and document the handoff. **Do not rebuild features that already work.** Work autonomously through the phases, keeping a checklist. The goal is a polished **local competition-demo build**, not an unverified claim of production readiness.

## Absolute constraints
- **Branch `main` only.** Last reported commit `36880e9` (Gate 6.1 Checkpoint C); inspect for newer commits. No new branches or PRs.
- **Zero separately billable spend:** no real Gemini, Vertex AI, cloud API, paid AI services, remote deployments, cloud provisioning, managed databases, or paid browser automation. No cloud deployment of any kind.
- Keep `CLASSLENS_AI_MODE=mock` and `CLASSLENS_LIVE_INFERENCE_ENABLED=false` during all work. Inspect tests before running; mock any model network boundary. Do not invoke real inference, even for testing.
- Never reset, stash, overwrite, force-push, or discard existing changes. If local changes or divergence exist, stop destructive Git actions, document them, and proceed only with safe independent work.
- Commit and push **verified** milestones incrementally to `origin/main`, without force pushing. No secrets, local databases, uploaded images, research datasets, or student data in commits.
- Only Gemini visual extraction is LLM-powered; the downstream math verifier, misconception classification and critic are deterministic. Do not claim five independent AI agents.
- Existing number-line reasoning scope is the baseline. No speculative expansion to all math topics, extra agents, enterprise RBAC, or unrelated functionality.
- Previous dataset audit reported 20/20 evaluation records lacked physical images. **Never invent handwriting accuracy, fabricated real results, or real-model success.**
- Autonomously continue safe development; skip and report anything requiring paid resources, real student data, security weakening, or irreversible actions.

## Phase 0 — Repository inventory and baseline
1. Run `git status -sb`, `git log -1 --oneline`, inspect branch, remote, and uncommitted work. Preserve everything.
2. Read `README.md`, `pyproject.toml`, `requirements.txt`, `docs/DEVELOPMENT_ROADMAP.md`, Gate 6.1 artifacts, `evaluation/runner.py`, `services/worker/security/provenance_guard.py`, backend routers/contracts/storage, frontend routes/components, and existing tests.
3. Inventory implemented features, incomplete flows, TODOs, known failures, current storage, styling, and tests. Create/update `docs/OVERNIGHT_COMPLETION_CHECKLIST.md` with actionable status and evidence.
4. Verify `.gitignore` protects `.env` secrets, `.venv`, `node_modules`, `.next`, SQLite files, uploads, and generated artifacts while retaining safe examples.
5. Run only a small baseline subset of tests confirmed to be fully offline. Record actual failures before modifying code.

## Phase 1 — Fix issues and complete Gate 6.1 offline readiness
1. Verify Checkpoint C integration tests from `36880e9`. Review the reported stale error-message assertions in `test_gate4a_pipeline.py` and `test_live_gemini_authorization_gate6.py`. Fix brittle assertions only if security behavior is preserved.
2. Complete Checkpoint D: implement/finish `--dry-run` in the **existing** `evaluation/runner.py`, not a second runner. Validate configuration, expected image files, ground truth, schema, and authorization; output accurate missing-data/readiness reports. Dry-run must never instantiate or call live Gemini.
3. Complete Checkpoint E: all evaluation screens and reports distinguish `MOCK/OFFLINE`, `AWAITING_LIVE_ANALYSIS`, `LIVE NOT PERFORMED`, and `LIVE MEASURED` only where backed by actual evidence. No fake accuracy metrics.
4. Preserve five-case blind evaluation spec and ground truth. If physical handwriting images are missing, document the blocker; do not fabricate them.
5. Fix malformed Gemini-schema handling, missing images, incomplete reasoning, ambiguous evidence, unsupported mathematics, and safe review routing. Add narrow regression tests.
6. Review Section 10 persistence recommendations; implement local persistence below, not cloud persistence.

## Phase 2 — Durable local database and image storage (highest implementation priority)
Prefer **SQLite** with existing `aiosqlite` or the current storage abstraction. Do not introduce Firestore, Neon, managed Postgres, cloud services, or a Docker requirement.
- Persist assessments, classes/cohorts if present, pseudonymous students, worksheet submissions, statuses, available evidence/diagnoses, teacher review overrides, and audit history. Preserve existing IDs, domain contracts, and APIs wherever possible.
- Keep original uploaded images in a configurable local data directory; store safe file references in SQLite. Use secure filenames, content/MIME and size checks, path confinement, symlink protection, and atomic writes.
- Use schema initialization/migrations that are idempotent, transactional, and non-destructive. Preserve `local-data/state.json` and existing uploads. Back up before migration; if uncertain, offer an explicit opt-in migration command. Never silently erase or overwrite old records.
- Use foreign keys, indexes, unique IDs, timestamps, transactions, and appropriate concurrency handling.
- An upload in mock mode must remain `AWAITING_LIVE_ANALYSIS`; **never invent an AI diagnosis for real uploaded work**.
- Teacher overrides must survive restarts and preserve review provenance. Dashboard stats must reflect durable records, not temporary in-memory state.
- Provide clearly marked synthetic/demo seed data, separate from genuine student records.
- Add tests for restart persistence, CRUD, review overrides, migration safety, duplicates, invalid uploads, rollback, and relevant concurrent operations.
- Exclude SQLite files and uploaded student images from Git.

## Phase 3 — Finish end-to-end teacher workflows
Inspect and repair all existing frontend/backend integration:
1. Dashboard: assessment counts, review queue, recent work, meaningful primary actions and empty states.
2. Assessment/class creation, listing, details, edit/archive where existing product model supports them.
3. Worksheet upload: file picker/drag-drop, preview, multi-upload if supported, validation, progress, retry, duplicate handling, truthful pending states.
4. Submission detail: original image, actual available evidence, mathematical verification, misconception analysis, uncertainty, review requirements. Do not display fabricated mock diagnoses for real uploads.
5. Teacher review: inspect evidence, override, save, view history, refresh/restart persistence, update dashboard counts.
6. Cohort insights: misconception groups, status breakdown, filtering, review counts; no metrics from nonexistent analysis.
7. API validation, stable TypeScript contracts, loading/error/retry states, navigation and refresh resilience.
8. Eliminate dead buttons and broken links. For unsupported capabilities, show honest limitation or review-required state.

## Phase 4 — Elegant competition-quality UI/UX
Build a cohesive **teacher-centered premium education SaaS** interface, not a generic chatbot. Reuse the existing frontend framework and components. Suggested palette: navy `#12233F`, indigo `#4F46E5`, teal `#0F9D92`, off-white `#F7F9FC`, restrained amber for review warnings; adapt to existing branding.
- Consistent typography, spacing, subtle shadows, readable charts, semantic status colors, purposeful icons, tasteful motion.
- Responsive on desktop, laptop, tablet and mobile; no horizontal overflow or broken modals.
- WCAG AA contrast, visible focus, keyboard navigation, accessible form labels, reduced motion.
- Improve **every existing page/subpage**: app shell/sidebar/mobile navigation, home/dashboard, assessments, upload, submission/evidence detail, teacher review, cohort insights, evaluation/developer pages, and existing settings/help/error/loading screens.
- Clear teacher journey: create assessment → upload → inspect status/evidence → review → class insights.
- Strong skeletons, empty states, confirmations, errors, and retry paths. All visible controls must work; remove placeholder actions.
- Evaluation UI must unmistakably distinguish mock/pending from measured live results.
- Do not spend the night adding unrelated admin portals or design libraries.

## Phase 5 — Security, privacy and reliability
- Preserve SHA-256 synthetic fixture allowlist, canonical path/symlink protection, owner authorization and fail-closed live inference. Never weaken production guards to pass tests.
- Validate upload MIME and bytes, size, paths, unsafe file serving, malformed requests, and error handling.
- Avoid secrets in frontend, logs, Git, SQLite or committed env files. Review local CORS and existing auth; label demo-only auth accurately instead of claiming enterprise security.
- Add privacy-safe logging, local data retention/cleanup guidance, and explicit prototype limitations.
- Confirm no UI or test path can trigger real Gemini/Vertex calls.

## Phase 6 — Offline testing and local QA
- Inspect test scripts for external effects before execution. Run targeted Python tests, then full **offline** suite if safe.
- Run frontend lint/typecheck/build using the existing package manager; fix actual failures.
- Test SQLite initialization/migration, restart durability, uploads, teacher reviews, dashboard statistics, mock/live disclosures, and fail-closed authorization.
- Perform local API/UI smoke checks with explicitly synthetic data. Use local browser automation only if already available and free.
- Check mobile layouts and accessibility using local tooling.
- Fix root causes; don't remove meaningful assertions, skip tests without explanation, or claim tests ran when they did not.
- Report exact passed/failed/not-run results and distinguish pre-existing from introduced failures.

## Phase 7 — Documentation and handoff
- Update README with Python `>=3.11`, `python -m pip install -e ".[dev]"`, frontend install/start commands, local SQLite setup, migration/backup, upload directory, and mock-mode operation.
- Provide safe `.env.example` with mock defaults and no required real API key.
- Document supported number-line scope, Gemini extraction boundary, deterministic verification/critic, privacy limitations, and how to seed a synthetic demo.
- Produce `docs/OVERNIGHT_COMPLETION_REPORT.md` listing starting/final commits, completed features, changed files, DB schema/migration approach, UI screens improved, exact tests/build results, local startup commands, blockers, and **real handwriting/Gemini validation NOT PERFORMED**.
- Keep `docs/OVERNIGHT_COMPLETION_CHECKLIST.md` current.

## Execution and Git discipline
Work autonomously through all feasible phases. After each substantial verified milestone, commit and push to `origin/main` with descriptive message. Never force push or create PRs. If a phase is blocked, document it and continue independent safe work. Do not stop for routine confirmation.

**If time or coding tokens run low, prioritize:** (1) safe baseline, (2) durable persistence, (3) complete teacher flows, (4) UI polish, (5) offline evaluation readiness, (6) tests/security/docs. Do not waste time on speculative features.

At finish, report `git status -sb`, latest commit, push confirmation, exact local launch commands, implemented functionality, test/build evidence, and honest remaining limitations. **Never claim zero defects, real handwriting accuracy, or production readiness based only on offline mocks.**

**Begin now with Phase 0 and continue overnight. Absolutely no cloud deployment or separately billable AI calls.**
