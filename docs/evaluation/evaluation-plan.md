# Evaluation Framework & Benchmark Protocol — ClassLens

**Document ID:** EVL-PLN-001
**Version:** 1.2.0
**Date:** 2026-10-11

---

### Changelog (v1.2.0 — Final Technical-Validity Revision)
- Formalized provenance separation: Category A (Original teacher descriptive notes) vs Category B (Synthetic LLM annotations — strictly barred from golden benchmarking).
- Reclassified all 13 responses in Problem #1065658 as **provisional** until double-blind adjudication is completed.
- Clarified distinction between **final answer correctness** and **visible reasoning correctness** across all rows.
- Labeled all proposed performance thresholds as **engineering design targets**, prohibiting claims of achieved results prior to empirical adjudication.

---

## 1. Evaluation Methodology & Integrity Principles

Automated evaluation of multimodal mathematical handwriting cannot rely naively on LLM self-evaluation or unverified dataset claims. ClassLens follows five strict evaluation principles:

1. **Teacher Descriptions as Qualitative Evidence, Not Consensus Ground Truth**: Human teacher descriptions in DrawEduMath provide single-rater qualitative evidence of what was observed on the page; they do not represent multi-expert pedagogical consensus.
2. **Synthetic Labels Excluded from Benchmarking**: `synthetic_qa_gpt4o_json` and `synthetic_qa_claude_json` are synthetic outputs produced by third-party LLMs and are strictly excluded from golden benchmark evaluation to prevent self-evaluation leakage.
3. **Double-Blind Adjudication Protocol**: The 13 provisional responses from Problem #1065658 must undergo independent multi-expert adjudication before claiming formal benchmark pass rates.
4. **Answer vs Reasoning Separation**: A student may arrive at the correct final number (+2) through flawed or compensatory arithmetic (e.g. Row 4) or with zero working (Row 11). Correct final answers must never be credited as valid reasoning without verified supporting steps.
5. **Deterministic Golden Path Unit Tests**: Deterministic tools (`SymPyChecker`, `NumberLineDisplacementCalculator`) run in `tests/unit/` using synthetic fixtures without live API calls.

---

## 2. Audited Benchmark: Problem #1065658 (`-6 + 12 - 4 = 2`)

Problem #1065658 contains 13 real student submissions in `dataset/problem_1065658/`. The table below records actual audited source metadata, explicitly separating answer correctness from reasoning correctness:

| Row Index | Image Filename | Actual Teacher Description & QA Evidence | Final Answer Status | Visible Reasoning Status | Reconciled Provisional Ground Truth Status & Test Assertion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Row 0** | `04255753-*.jpeg` | Intervals of 2 from -12 to 12. Arrows: $0 \to -6 \to +6 \to +2$. Circled 2. "No error in student response." | `correct` (2) | `correct` | **`supported_correct`**: Standard hops from zero ($0 \to -6 \to +6 \to +2$). |
| **Row 1** | `0a70eabf-*.jpeg` | Horizontal line -9 to 10. Circled 2. Arrows $0 \to -6 \to +6 \to +2$. "No errors in student response." | `correct` (2) | `correct` | **`supported_correct`**: Standard hop from zero. |
| **Row 2** | `2292f546-*.jpeg` | Graph paper, line -7 to 10. Arrows end at 2. "Student makes no error, final answer inferred from terminal position." | `correct` (2) | `correct` | **`supported_correct`**: Final answer inferred from arrow terminal; absence of circle around 2 accepted. |
| **Row 3** | `2b804ad7-*.png` | Digitally drawn bracket curves. $0 \to -6$, curved blue arrow to 6, green arrow to 2. "Makes no errors." | `correct` (2) | `correct` | **`supported_correct`**: Bracket curve notation accepted as valid representation. |
| **Row 4** | `56005c1c-*.png` | Line from -6 to +5 (magnitude 11 instead of 12); line from +5 to +2 (magnitude -3 instead of -4). Answer stops at 2. | `correct` (2) | **`error`** (Compensatory) | **`supported_error`** (`MISC-ARITH-OFF-BY-ONE`): Correct final answer achieved via two compensating magnitude errors. First error on Step 2. |
| **Row 5** | `80545ef3-*.jpeg` | Lined paper. "Student makes an error... draws a line that hops with a magnitude of 11 instead of 12." | `incorrect` (1) | **`error`** | **`supported_error`**: Magnitude off-by-one error (hopped 11 units instead of 12). |
| **Row 6** | `8cbadb4e-*.jpeg` | Modeling on number line correct, but student circled **+3** as final answer instead of +2. | **`incorrect`** (3) | `correct` | **`supported_error`**: Number line reasoning correct, but terminal mark/label incorrect (+3 vs +2). |
| **Row 7** | `8ef9d302-*.png` | Digital drawing. Student circled 2. "There is no error in the student's response." | `correct` (2) | `correct` | **`supported_correct`**: Standard execution pass (correcting prior false error label). |
| **Row 8** | `a5c95313-*.png` | Student mislabeled integers on number line ($0, 1, 2, 4, 5, 6...$ skipping 3). | `incorrect` | **`error`** | **`supported_error`** (`MISC-LINE-INTERVAL-MISLABEL`): Detects irregular tick interval labels. |
| **Row 9** | `b4214e02-*.png` | Digitally drawn. Student rearranged equation: $12 - 4 - 6 = 2$. "No errors in student response." | `correct` (2) | `correct` | **`supported_correct`**: Valid commutative rearrangement accepted ($12 - 4 - 6 = 2$). |
| **Row 10** | `d3e07e18-*.jpeg` | Pre-printed paper. Hopping curved arrows: $0 \to -6 \to +6 \to +2$. "No error in student response." | `correct` (2) | `correct` | **`supported_correct`**: Standard hop pass (correcting prior false error label). |
| **Row 11** | `e33295ea-*.jpeg` | Circled 2 on number line, but **zero working or arrows shown**. "No evidence of using addends." | `correct` (2) | **`incomplete`** | **`incomplete`**: Final answer marked, but reasoning absent. Must NOT verify reasoning as correct. |
| **Row 12** | `f0738571-*.jpeg` | Number line drawn, but completely incomplete (no arrows, addends, or final sum present). | `undetermined` | **`unreadable`** | **`undetermined`**: Triggers abstention guardrail (`needs_teacher_review: true`). |

---

## 3. Double-Blind Human Adjudication Protocol

To graduate from provisional status to certified ground truth:
1. Two independent mathematics educators annotate each response blindly.
2. Annotators record visual elements, step transitions, first error location, and misconception codes in a standardized JSON template.
3. Discrepancies are adjudicated by a curriculum specialist.
4. The adjudicated output is committed as `golden_benchmark_v1.json` with an immutable SHA256 checksum.

### Standardized Annotation Schema Template
```json
{
  "response_id": "resp_56005c1c",
  "problem_id": "1065658",
  "annotator_id": "annotator_sarah_lim",
  "provenance": "human_adjudicated",
  "visual_elements": {
    "has_number_line": true,
    "line_orientation": "horizontal",
    "range": [-10, 10],
    "arrow_count": 3,
    "arrows": [
      {"start": 0, "end": -6, "direction": "left", "expected_magnitude": 6, "actual_magnitude": 6},
      {"start": -6, "end": 5, "direction": "right", "expected_magnitude": 12, "actual_magnitude": 11},
      {"start": 5, "end": 2, "direction": "left", "expected_magnitude": 4, "actual_magnitude": 3}
    ],
    "final_answer_marked": "none"
  },
  "answer_status": "correct",
  "reasoning_status": "supported_error",
  "first_supported_error": {
    "step_number": 2,
    "error_type": "magnitude_miscount",
    "description": "Arrow from -6 to 5 has displacement of +11 instead of +12"
  },
  "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
  "confidence": 1.0,
  "notes": "Student arrived at answer 2 by compounding two compensatory magnitude errors."
}
```

---

## 4. Evaluation Separation & Metrics Protocol

### 4.1 Strict Test Separation
1. **Tier 1: Offline Unit Fixtures (`tests/unit/`)**:
   - Tests SymPy and geometry tools against synthetic vector fixtures. Zero LLM calls; runs in $< 1$s.
2. **Tier 2: Adjudicated Benchmark (`tests/evaluation/`)**:
   - Evaluates multi-agent pipeline against the adjudicated 13 responses of Problem #1065658 with explicit `--run-live-gemini` flag.
3. **Tier 3: Cross-Problem Holdout Suite (`tests/holdout/`)**:
   - Evaluates generalization across 3 additional DrawEduMath problems from the repository.

### 4.2 Target Performance Metrics (Design Specifications)
- **Observation Extraction Precision**: $\frac{\text{Correctly extracted numbers, arrows, endpoints}}{\text{Total extracted elements}}$ (Target: $\ge 90\%$)
- **First-Error Localization Accuracy**: $\frac{\text{Flagged error steps matching ground truth error}}{\text{Total error responses}}$ (Target: $\ge 85\%$)
- **Abstention Calibration**: $\frac{\text{Correct abstentions on unreadable/empty images}}{\text{Total unreadable/empty test images}}$ (Target: $100\%$)
- **Alternative Method Retention**: Ratio of valid commutative/alternative paths marked correct (Target: $100\%$)
- **False-Confident Diagnosis Rate**: Model claiming high confidence ($> 0.8$) on an incorrect diagnosis (Target: $< 5\%$)
