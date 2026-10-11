# ClassLens — Product Requirements Document (PRD)

**Document ID:** REQ-PRD-001
**Version:** 1.1.0
**Status:** Architecture Review Approved
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Explicitly anchored P0 vertical slice to DrawEduMath `problem_1065658` ($-6 + 12 - 4 = 2$, 13 responses in `./dataset/problem_1065658/`).
- Clarified that dataset rows represent isolated response images, not continuous student cohorts or real school rosters.
- Formalized distinction between human teacher descriptions, synthetic model annotations, and provisional evaluation benchmarks.
- Reconciled batch processing performance SLA: P50 $\le 25$s, P95 $\le 45$s for 15 student responses.

---

## 1. Executive Summary & Product Promise

ClassLens is an AI-assisted mathematics teaching intelligence platform designed for upper-primary and lower-secondary educators.

> **Product Promise:**
> *"Marking tells teachers who got it wrong. ClassLens tells them what to teach next."*

Traditional grading tools merely tally scores or highlight wrong final numbers. For a mathematics teacher facing 30 photographed student worksheets, diagnosing the root misconceptions across varying handwriting styles, step layouts, and number-line diagrams requires hours of manual analysis.

ClassLens transforms photographed or scanned handwritten mathematics responses into immediate, actionable classroom intelligence:
1. **Multimodal Evidence Extraction**: Observes and transcribes handwritten calculations, diagrams, and arrow movements without inventing missing work.
2. **Deterministic Mathematical Verification**: Evaluates each computational and geometric step using Python/SymPy and geometric rule engines against canonical and acceptable alternative strategies.
3. **Misconception Diagnosis**: Identifies the *first supported erroneous step* and maps the reasoning to a standardized pedagogical error taxonomy (e.g., directional sign errors, magnitude miscounting, inverse operation flaws).
4. **Class-Wide Aggregation**: Clusters verified error patterns across the entire student cohort with mathematically rigorous denominators (distinguishing AI-proposed vs. teacher-verified states).
5. **Grounded Reteaching Plan**: Generates targeted, differentiated small-group interventions, worked examples, and formative exit tickets linked directly to the observed misconceptions.
6. **Human-in-the-Loop Auditability**: Empowers educators to review, edit, or override any AI interpretation. Teacher edits are audited and become benchmark evaluation assets.

---

## 2. Product Boundaries & Decision Support Principles

ClassLens is explicitly engineered as **Decision Support for Educators**, NOT an autonomous high-stakes grading or disciplinary system:

1. **Evidentiary Grounding**: Every diagnosis must be anchored in visible evidence on the submission image (e.g., specific arrows, equations, or circled coordinates).
2. **Explicit Abstention & Uncertainty**: When handwriting is illegible, cropped, faint, or mathematically ambiguous, the system must declare `undetermined` or `insufficient_evidence` and flag the response for teacher review rather than hallucinating steps.
3. **Alternative Valid Methods**: Mathematics allows multiple valid solution paths. For example, in $-6 + 12 - 4 = 2$, starting at $-6$, jumping $+12$ to $+6$, then jumping $-4$ to $+2$ is completely valid and must never be penalized as an error simply because it differs from an arbitrary starting point.
4. **No Automated High-Stakes Action**: AI findings are presented as *proposals* until teacher approval. No grades or report card comments are finalized without teacher consent.
5. **Privacy by Default**: Student names and identifiers are pseudonymized at intake. Raw student biometric or identifying marks are never exposed to public models or public views.

---

## 3. Scope Definition: MVP vs. Future Horizons

### 3.1 MVP Scope (AI Builder Cup 2026 Focus)
- **Problem Domain**: Focus on handwritten arithmetic and number-line operations with negative/positive integers (specifically DrawEduMath problem `1065658`: $-6 + 12 - 4 = 2$, containing 13 real student responses).
- **Intake**: Multi-file image upload (JPG/PNG/WebP) and curated demo problem importer from local DrawEduMath records.
- **Processing**: Asynchronous multi-agent analysis with deterministic Python verification tools via Google Cloud Tasks and private Cloud Run worker.
- **Datastore**: Serverless Google Cloud Firestore Native Mode with Pydantic collection models and zero standing idle cost.
- **Educator Experience**:
  - Assessment setup with expected result, acceptable paths, and rubric.
  - Per-response inspection modal with side-by-side zoom/rotate image viewer, observed steps, detected error, and teacher review toggle.
  - Class insight dashboard showing error distribution charts with clear denominators.
  - One-click generated reteaching plan with differentiated activity cards and printable exit ticket.
- **Evaluation Workbench**: Provisional 13-response evaluation suite for Problem `1065658` with double-blind adjudication protocol and automated unit testing on SymPy/geometry tools.

### 3.2 Post-MVP / Future Roadmap (Deferred)
- Student self-service feedback portal.
- Multi-question multi-page exam booklets.
- Automated handwriting style clustering.
- Integration with School Information Systems (Google Classroom, Canvas, MOE SLS).
- Automated OCR fine-tuning on regional handwriting datasets.

---

## 4. Key Success Metrics & Release Gates

| Metric | Target (MVP) | Measurement Protocol |
| :--- | :--- | :--- |
| **Step Extraction Accuracy** | $\ge 85\%$ | Ratio of correctly transcribed numbers/arrows against verified ground truth. |
| **First-Error Localization Precision** | $\ge 90\%$ | Proportion of flagged erroneous steps that truly contain the mathematical error. |
| **Abstention Calibration** | $100\%$ on unreadable | System must abstain on deliberately blurred/blank images without false positives. |
| **Alternative Method Acceptance** | $100\%$ | Golden test paths for valid alternatives (e.g. commutative jumps) must pass without penalty. |
| **Teacher Review Efficiency** | $\le 15$ sec / response | Teacher can verify and accept/edit an interpretation in under 15 seconds. |
| **End-to-End Batch Latency** | P50 $\le 25$s, P95 $\le 45$s for 15 responses | Asynchronous parallel pipeline completing an entire classroom batch under 45 seconds. |
