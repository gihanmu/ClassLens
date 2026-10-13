# ClassLens — Real Handwriting Evaluation Dataset Audit & Collection Protocol

**Document Version:** 1.0.0  
**Milestone:** Gate 6.1 — Live Gemini Proof of Capability (Phase A: Offline Readiness)  
**Author:** Principal Applied AI Engineer, Mathematics Evaluation Specialist, & AI Safety Lead  
**Status:** AUDITED — MISSING PHYSICAL IMAGES (PREREQUISITE FOR PHASE B)  

---

## 1. Executive Summary & Inventory Audit

In Gate 6, a comprehensive 20-case evaluation specification was authored at `evaluation/datasets/handwriting_eval_v1.json`. This specification defines ground truth for 10 distinct error, perceptual ambiguity, and cognitive slip categories centered on Singapore Secondary 1 integer number line arithmetic (Problem #1065658: Evaluate $-6 + 12 - 4$).

### Disk Audit Findings
A comprehensive physical disk audit of the repository was conducted:
- Directory `evaluation/datasets/images/`: **DOES NOT EXIST ON DISK**.
- All 20 referenced `.png` image files (`hw_eval_01_clear_correct.png` through `hw_eval_20_answer_only_no_hops.png`): **MISSING FROM DISK**.
- Existing images in workspace:
  - `tests/fixtures/synthetic_evaluation_cases/`: Contains 3 synthetic test fixtures (`case_01_canonical_correct.png`, `case_02_off_by_one_error.png`, `case_03_ambiguous_incomplete.png`) generated programmatically via PIL.
  - `local-data/uploads/org_cedar_sec/asm_1065658/`: Contains 1 test upload (`test_worksheet.png`).

**Audit Conclusion:** While `evaluation/datasets/handwriting_eval_v1.json` provides an exemplary mathematical ground-truth schema, **zero physical handwritten images currently exist in the evaluation dataset directory**. In accordance with strict AI Builder Cup integrity and Gate 6.1 Phase A requirements, all 20 cases are classified as **Image exists: No** and **Ready for live evaluation: No**.

---

## 2. Complete 20-Case Dataset Inventory Table

| Case ID | Category | Target Canonical Value | Image Reference | Image Exists on Disk? | Image Readable? | Ground Truth in JSON? | Ready for Live Evaluation? |
|---|---|---|---|:---:|:---:|:---:|:---:|
| `hw_eval_01_clear_correct_hop_from_zero` | `clear_correct_solution` | `2` | `hw_eval_01_clear_correct.png` | **No** | **No** | Verified | **No** |
| `hw_eval_02_clear_correct_direct_start` | `clear_correct_solution` | `2` | `hw_eval_02_direct_start.png` | **No** | **No** | Verified | **No** |
| `hw_eval_03_off_by_one_under_jump` | `off_by_one_tick_count` | `2` | `hw_eval_03_off_by_one_under.png` | **No** | **No** | Verified | **No** |
| `hw_eval_04_off_by_one_over_jump` | `off_by_one_tick_count` | `2` | `hw_eval_04_off_by_one_over.png` | **No** | **No** | Verified | **No** |
| `hw_eval_05_direction_error_reversed_second_hop` | `direction_error` | `2` | `hw_eval_05_direction_reverse.png` | **No** | **No** | Verified | **No** |
| `hw_eval_06_direction_error_reversed_third_hop` | `direction_error` | `2` | `hw_eval_06_hop3_reversed.png` | **No** | **No** | Verified | **No** |
| `hw_eval_07_sign_inversion_initial_term` | `sign_inversion` | `2` | `hw_eval_07_sign_inversion_start.png` | **No** | **No** | Verified | **No** |
| `hw_eval_08_sign_inversion_double_flip` | `sign_inversion` | `2` | `hw_eval_08_sign_inversion_double.png` | **No** | **No** | Verified | **No** |
| `hw_eval_09_misaligned_zero_point_start_at_one` | `misaligned_zero_point` | `2` | `hw_eval_09_zero_misalign_one.png` | **No** | **No** | Verified | **No** |
| `hw_eval_10_misaligned_zero_point_start_at_neg_one` | `misaligned_zero_point` | `2` | `hw_eval_10_zero_misalign_neg_one.png` | **No** | **No** | Verified | **No** |
| `hw_eval_11_contradiction_correct_hops_wrong_answer` | `arithmetic_numberline_contradiction` | `2` | `hw_eval_11_contradiction_hops_answer.png` | **No** | **No** | Verified | **No** |
| `hw_eval_12_contradiction_compensatory_lucky_answer` | `arithmetic_numberline_contradiction` | `2` | `hw_eval_12_compensatory_lucky.png` | **No** | **No** | Verified | **No** |
| `hw_eval_13_ambiguous_digit_one_vs_seven` | `ambiguous_digit_hop` | `2` | `hw_eval_13_digit_ambiguity_1_7.png` | **No** | **No** | Verified | **No** |
| `hw_eval_14_ambiguous_hop_landing_between_ticks` | `ambiguous_digit_hop` | `2` | `hw_eval_14_landing_mid_tick.png` | **No** | **No** | Verified | **No** |
| `hw_eval_15_faint_pencil_low_contrast` | `faint_low_contrast_pencil` | `2` | `hw_eval_15_faint_pencil.png` | **No** | **No** | Verified | **No** |
| `hw_eval_16_erased_ghost_marks_smudge` | `faint_low_contrast_pencil` | `2` | `hw_eval_16_erased_ghost_marks.png` | **No** | **No** | Verified | **No** |
| `hw_eval_17_ambiguous_number_line_missing_labels` | `ambiguous_number_lines` | `2` | `hw_eval_17_missing_tick_labels.png` | **No** | **No** | Verified | **No** |
| `hw_eval_18_ambiguous_number_line_non_uniform_spacing` | `ambiguous_number_lines` | `2` | `hw_eval_18_non_uniform_spacing.png` | **No** | **No** | Verified | **No** |
| `hw_eval_19_partially_completed_first_hop_only` | `partially_completed_work` | `2` | `hw_eval_19_first_hop_only.png` | **No** | **No** | Verified | **No** |
| `hw_eval_20_partially_completed_answer_only_no_working` | `partially_completed_work` | `2` | `hw_eval_20_answer_only_no_hops.png` | **No** | **No** | Verified | **No** |

---

## 3. Adult-Created / Consenting Handwriting Collection Protocol

To protect minor privacy and comply with competition ethics, ClassLens strictly prohibits scraping or collecting student work from real classrooms without institutional ethics approval. All evaluation samples must be created by consenting adults (educators, software engineers, or adult volunteers) mimicking realistic student handwriting patterns.

### 3.1. Target Problem & Standardized Worksheet Layout
- **Curriculum Context:** Singapore Ministry of Education (MOE) Secondary 1 Mathematics (Grade 7 equivalent).
- **Topic:** Negative Numbers & Integer Arithmetic on the Number Line.
- **Problem Statement:** `"Evaluate -6 + 12 - 4 on the number line provided below."`
- **Worksheet Components:**
  1. Header with dummy student ID (e.g. `SAMPLE-SEC1-01`) and problem statement.
  2. Horizontal number line spanning from $-10$ to $+10$, with tick marks spaced every $1$ unit and primary numbers labeled every $2$ or $5$ units (or all integers labeled).
  3. Work space above the number line for drawing curved arc hops.
  4. Final Answer Box: Prominently outlined rectangle labeled `"Answer: [   ]"`.

### 3.2. Physical Capture & Imaging Specifications
- **Medium:** Standard 2B or HB graphite pencil, or standard black/blue ballpoint pen on white A4 paper.
- **Scanning / Photography Requirements:**
  - Minimum Resolution: $1200 \times 800$ pixels (recommended: $300$ DPI flatbed scan or sharp smartphone photo).
  - Lighting: Uniform, diffuse lighting without harsh smartphone shadows across the number line.
  - Perspective: Overhead orthogonal view (no steep angled perspective distortions).
  - File Format: PNG or high-quality JPEG (`image/png` or `image/jpeg`).
  - Size Limit: Under 5 MB per image (well within the ClassLens 10 MB upload ceiling).

### 3.3. Ethical Guardrails & Zero PII Guarantee
- **No Real Student Identifiers:** Never include real student names, school names, class registers, or birthdates.
- **Anonymized Identifiers:** Use standardized synthetic student tags (e.g., `ADULT-SAMP-01` through `ADULT-SAMP-05`).
- **Adult Written:** All handwriting must be hand-drawn by consenting adults following specified pedagogical test scripts.

---

## 4. Human Annotation Template & Double-Blind Protocol

To maintain evaluation integrity, evaluation follows a strict **double-blind procedure**:
1. **Pre-Inference Human Annotation:** Human expert annotates the physical worksheet before the image is submitted to the evaluation harness.
2. **Ground-Truth Isolation:** Ground truth annotations are stored separately from the model input. The multimodal model receives only the raw image bytes, problem statement, and target canonical value.
3. **Adversarial Scoring:** The evaluation runner compares the model's extracted visual observations and SymPy-derived diagnostic output against the human ground truth.

### Human Annotation Schema (Per Sample)

```json
{
  "sample_id": "blind_eval_01",
  "category": "clear_correct_solution",
  "intended_student_behavior": "Student begins at 0, draws arc left to -6, draws arc right by 12 landing at 6, draws arc left by 4 landing at 2, writes 2 in answer box.",
  "ground_truth": {
    "final_answer_text": "2",
    "final_answer_numeric": 2.0,
    "final_answer_status": "correct",
    "number_line_hops": [
      {
        "step_index": 1,
        "start_coord": 0.0,
        "end_coord": -6.0,
        "stated_magnitude": -6.0,
        "actual_displacement": -6.0,
        "direction": "left",
        "is_valid": true,
        "visible_annotation": "-6"
      },
      {
        "step_index": 2,
        "start_coord": -6.0,
        "end_coord": 6.0,
        "stated_magnitude": 12.0,
        "actual_displacement": 12.0,
        "direction": "right",
        "is_valid": true,
        "visible_annotation": "+12"
      },
      {
        "step_index": 3,
        "start_coord": 6.0,
        "end_coord": 2.0,
        "stated_magnitude": -4.0,
        "actual_displacement": -4.0,
        "direction": "left",
        "is_valid": true,
        "visible_annotation": "-4"
      }
    ],
    "reasoning_status": "supported_correct",
    "error_step_index": null,
    "misconception_id": null,
    "is_compensatory": false,
    "evidence_sufficiency": "sufficient",
    "requires_teacher_review": false,
    "expected_critic_verdict": "audit_passed"
  }
}
```

---

## 5. Phase B Readiness Gate

Until physical handwriting files are captured and stored in `evaluation/datasets/images/`:
- **Offline regression test suite remains the sole operational evaluation mode.**
- **Live inference execution remains blocked.**
- **Estimated live inference cost remains $0.00.**
