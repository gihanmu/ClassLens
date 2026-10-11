# ClassLens Dataset Manifest & Responsible Data Governance

**Document ID:** DATA-MAN-001  
**Version:** 1.0.0  
**Compliance Standard:** ClassLens Security & Privacy Policy (SEC-PRV-002) / CC BY-NC 4.0  

---

## 1. Overview and Provenance

ClassLens was developed using research data from **DrawEduMath** (derived from the ASSISTments online learning platform).

- **Source Corpus**: DrawEduMath dataset of student mathematical drawings and handwritten number lines.
- **Scope in Development Workspace**: 188 mathematics problems containing 2,030 student response images and structured JSON problem metadata.
- **Reference Problem Slice (Problem #1065658)**:
  - **Task**: Evaluate $-6 + 12 - 4$ on a number line.
  - **Target Canonical Value**: $+2$
  - **Observed Cohort**: 13 student responses (`Student-01` through `Student-13`), exhibiting canonical correct paths, interval miscounts (off-by-one errors), compensatory arithmetic errors, and directional reversals.

---

## 2. Redistribution Policy & Privacy Protection

In accordance with responsible AI practices, human subjects research ethics, and institutional policy:

> [!IMPORTANT]
> **Raw Student Handwriting Images are Excluded from Version Control.**  
> - **Student Privacy**: Handwritten student artifacts collected in classroom environments must not be mirrored or redistributed to public repositories without explicit parental/institutional consent.
> - **Licensing Terms**: The DrawEduMath research dataset is distributed under non-commercial educational research terms (**CC BY-NC 4.0** alongside original ASSISTments terms). Commercial redistribution and unauthenticated public file serving are strictly prohibited.
> - **Repository Hygiene**: The complete raw dataset comprises 201 MB across 2,030 image files, with single archive downloads exceeding 199 MB (violating GitHub's 100 MB hard limit).

---

## 3. Synthetic Fixtures for Deterministic Offline Verification

To guarantee that the entire ClassLens application, test suite, and CI/CD pipelines are **100% reproducible without downloading third-party student handwriting**, ClassLens provides comprehensive synthetic fixtures:

1. **Structured Mathematical Observations**: Located in `tests/fixtures/synthetic_math_fixtures.py`.
   - Contains 13 synthetic test fixtures (`SYNTH-ROW-00` through `SYNTH-ROW-12`).
   - Models all 13 observed mathematical variations:
     - Hop from zero vs. direct start.
     - Commutative addition paths.
     - Off-by-one interval counting errors (MISC-ARITH-OFF-BY-ONE).
     - Number-line mislabeling.
     - Compensatory errors (incorrect intermediate hops leading to a coincidental correct final answer).
     - Missing or incomplete reasoning.
2. **Synthetic Visual Canvas Fixtures**: Located in `tests/fixtures/synthetic_image_fixtures.py`.
   - Programmatically synthesizes clean, non-PII number-line diagrams for unit and integration testing of the image intake pipeline.
3. **Deterministic Mock Analysis**:
   - The offline demonstration mode runs entirely against these deterministic schemas and SymPy rules with zero external network or model calls.

---

## 4. Local Evaluation Setup (For Authorized Researchers)

If you are an authorized educational researcher with legitimate access to DrawEduMath and wish to run local evaluations on the raw benchmark:

1. Place the uncompressed problem folders under `./dataset/` in the project root:
   ```text
   dataset/
   ├── problem_1065658/
   │   ├── problem_metadata.json
   │   ├── 04255753-3765-4f36-8c4d-9a99fa2908fa.jpeg
   │   └── ... (13 images)
   ├── problem_1228910/
   └── ... (188 problem folders)
   ```
2. Verify integrity:
   ```bash
   .venv/bin/pytest tests/unit/test_image_intake.py -v
   ```
3. Run the FastAPI development server:
   ```bash
   .venv/bin/uvicorn services.api.main:app --port 8000
   ```
4. Access the demo endpoint at `http://localhost:3000` to interact with the local vertical slice.
