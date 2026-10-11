# Privacy, Compliance and Dataset Rights Policy — ClassLens

**Document ID:** SEC-PRV-002
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Explicitly flagged unresolved CC BY-NC 4.0 public hosting legal boundaries, mandating private authenticated demo access.
- Provided a synthetic/consented demo fallback for public evaluations and judging presentations.
- Clarified that Singapore PDPA and MOE considerations represent architectural design alignments, NOT certified legal compliance.
- Documented data minimization guarantees: student responses are isolated tokens, never continuous school rosters.

---

## 1. Dataset Rights, Provenance & Licensing (DrawEduMath)

### 1.1 Dataset Source & Original Context
The local evaluation dataset originates from **DrawEduMath** (derived from the ASSISTments online learning platform).
- **Filesystem Footprint**: 188 problem folders located in `./dataset/` containing 2,030 total student response images and structured JSON metadata.
- **Licensing Restrictions**:
  - The DrawEduMath dataset is provided under non-commercial educational research licensing (typically **CC BY-NC 4.0** alongside original ASSISTments terms of service).
  - **Commercial Prohibition**: The raw student images cannot be used for commercial product monetization without explicit agreements.
  - **Public Exposure Prohibition**: In compliance with responsible AI principles and human subject research ethics, raw student response images must **never be published into public open repositories, made publicly accessible on unauthenticated web storage, or exposed without authentication**.
  - **Hackathon Demo Handling**: For the AI Builder Cup 2026 judging demonstration, ClassLens operates within a private, authenticated demo environment using pre-indexed problem metadata. For any unauthenticated public judging access, an **original synthetic / consented dataset fallback** is provided to guarantee complete legal compliance.

### 1.2 Student Identity Boundaries in DrawEduMath
- **No Persistent Student IDs**: DrawEduMath **does not** contain persistent student tracking across problems. `problem_id` (e.g. `1065658`) identifies the mathematical task, NOT an individual student.
- **No Identity Reconstruction**: ClassLens strictly prohibits any attempt to reconstruct student identities, link handwriting styles across tasks, or infer demographics.
- **Demo Response Labeling**: Individual submissions within a problem are referenced solely by their random row hash / image ID (e.g. `resp_04255753` labeled within the assessment as `Student-01`).

### 1.3 Human Ground Truth vs. Synthetic Annotations
The metadata in DrawEduMath contains multiple annotation layers:
1. `teacher_description`: Human educator natural language description of observed student steps.
2. `teacher_qa_pairs_json`: Human educator single-rater QA pairs regarding number line labeling, arrow direction, final answer marking, and specific errors.
3. `synthetic_qa_gpt4o_json` & `synthetic_qa_claude_json`: Automatically generated synthetic QA pairs produced by commercial LLMs during dataset preparation.

> [!WARNING]
> **Zero Fabrication Policy**: Synthetic QA pairs (`synthetic_qa_*`) must **NEVER** be treated as ground truth correctness or misconception benchmarks. They represent model-generated artifacts. Only human teacher QA pairs and human descriptions may be used as reference evidence, and even human descriptions must be manually adjudicated before establishing a golden test case.

### 1.4 Demographic & Curriculum Context (US vs. Singapore)
DrawEduMath is a US-origin dataset collected in American middle school classrooms.
- **No Validated Singapore Performance Claim**: Performance on DrawEduMath cannot and will not be claimed as validated accuracy for Singapore Ministry of Education (MOE) students. Singapore mathematics curricula (e.g. Primary 5/6 and Secondary 1 Syllabus) feature distinct pedagogical heuristics, bar modeling methods, and presentation conventions.
- **Design for Classroom Uploads**: The system is engineered to handle new, teacher-uploaded student responses using general mathematical reasoning engines rather than being overfitted to the DrawEduMath distribution.

---

## 2. Singapore Privacy & Regulatory Alignment (PDPA & MOE Considerations)

For any prospective real-world deployment in Singapore educational institutions, ClassLens establishes the following architectural design alignments:

1. **Personal Data Protection Act (PDPA) Alignment**:
   - **Data Minimization (Section 13)**: No student names, NRIC/BC numbers, or school email addresses are collected. Submissions use pseudonymous tokens (`STU-01`, `STU-02`) managed by the classroom teacher.
   - **Purpose Limitation (Section 18)**: Uploaded student work is used solely for the immediate formative assessment and reteaching plan requested by the teacher.
   - **Retention Limitation (Section 25)**: Automated 30-day purge cycle cascades across Cloud Storage and database records unless explicitly archived by the school.
2. **Ministry of Education (MOE) Security Requirements**:
   - Real classroom deployment requires institutional Data Processing Agreements (DPA), Threat Risk Assessment (TRA), and alignment with Government Instruction Manual 8 (IM8) on cloud usage and data residency.
   - Singapore hosting (`asia-southeast1`) ensures data residency within the Republic.

> [!NOTE]
> ClassLens states these regulatory alignments as **system design considerations and engineering guardrails**, NOT as formal government or legal certification.
