# ClassLens AI Assessment Reliability Benchmark Report

**Run ID:** `run_1791814481`  
**Dataset Version:** `1.0.0`  
**Timestamp:** `2026-10-12T14:14:41.045103+00:00`  
**Git Commit:** `3960787`  
**Pipeline Mode:** `mock-offline`  
**Overall Status:** **PASS** (18/18 passed, 100.0%)  

---

## 1. Reliability Metrics Overview

| Category | Metric | Ratio | Percentage | Target | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **A. Mathematical Outcome** | Answer Status Accuracy | `18/18` | 100.0% | ≥90.0% | **PASS** |
| | Final Answer Agreement | `15/15` | 100.0% | ≥90.0% | **PASS** |
| **B. Reasoning Verification** | Reasoning Status Accuracy | `18/18` | 100.0% | ≥85.0% | **PASS** |
| | Procedural Error Detection Recall | `5/5` | 100.0% | ≥90.0% | **PASS** |
| | Error-Step Localization Accuracy | `5/5` | 100.0% | ≥80.0% | **PASS** |
| **C. Misconception Detection** | Misconception Detection Precision | `5/5` | 100.0% | ≥85.0% | **PASS** |
| | Misconception Detection Recall | `5/5` | 100.0% | ≥85.0% | **PASS** |
| | Exact Taxonomy Match Rate | `18/18` | 100.0% | ≥85.0% | **PASS** |
| | False-Positive Misconception Rate | `0/13` | 0.0% | ≤0.0% | **PASS** |
| **D. Evidence Grounding** | Evidence Sufficiency Accuracy | `18/18` | 100.0% | ≥90.0% | **PASS** |
| | Appropriate Abstention Rate | `4/4` | 100.0% | =100.0% | **PASS** |
| | Unsupported Claim Rate | `0/18` | 0.0% | =0.0% | **PASS** |
| | Contradiction Rate | `0/18` | 0.0% | =0.0% | **PASS** |
| **E. Teacher Review Routing** | Review Routing Precision | `5/5` | 100.0% | ≥80.0% | **PASS** |
| | Review Routing Recall | `5/5` | 100.0% | ≥95.0% | **PASS** |
| **F. Critic Effectiveness** | Critic Verdict Accuracy | `18/18` | 100.0% | ≥85.0% | **PASS** |
| | Critic Challenge Precision | `5/5` | 100.0% | ≥80.0% | **PASS** |
| **G. Performance** | Average Latency | — | 0.1 ms/case | <5000 ms | **PASS** |

---

## 2. Category Breakdown

| Category | Total Cases | Passed | Failed | Pass Rate |
|:---|:---:|:---:|:---:|:---:|
| `ambiguous_insufficient` | 4 | 4 | 0 | **100.0%** |
| `arithmetic_slip` | 1 | 1 | 0 | **100.0%** |
| `canonical_correct` | 8 | 8 | 0 | **100.0%** |
| `compensatory` | 1 | 1 | 0 | **100.0%** |
| `off_by_one` | 3 | 3 | 0 | **100.0%** |
| `sign_error` | 1 | 1 | 0 | **100.0%** |

---

## 3. Detailed Case Results

| Case ID | Category | Status | Answer | Reasoning | Misconception | Review | Latency |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---:|
| `case_01_canonical_correct` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.16 ms |
| `case_02_off_by_one_error` | `off_by_one` | ✅ PASS | `incorrect` | `supported_error` | `MISC-LINE-INTERVAL-MISLABEL` | No | 0.11 ms |
| `case_03_ambiguous_incomplete` | `ambiguous_insufficient` | ✅ PASS | `undetermined` | `incomplete` | `None` | Yes | 0.1 ms |
| `resp_04255753` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.09 ms |
| `resp_0a70eabf` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.08 ms |
| `resp_2292f546` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.08 ms |
| `resp_2b804ad7` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.07 ms |
| `resp_56005c1c` | `compensatory` | ✅ PASS | `correct` | `supported_error` | `MISC-ARITH-OFF-BY-ONE` | Yes | 0.09 ms |
| `resp_80545ef3` | `off_by_one` | ✅ PASS | `incorrect` | `supported_error` | `MISC-ARITH-OFF-BY-ONE` | No | 0.08 ms |
| `resp_8cbadb4e` | `arithmetic_slip` | ✅ PASS | `incorrect` | `supported_correct` | `None` | No | 0.07 ms |
| `resp_8ef9d302` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.07 ms |
| `resp_a5c95313` | `off_by_one` | ✅ PASS | `incorrect` | `supported_error` | `MISC-LINE-INTERVAL-MISLABEL` | No | 0.08 ms |
| `resp_b4214e02` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.06 ms |
| `resp_d3e07e18` | `canonical_correct` | ✅ PASS | `correct` | `supported_correct` | `None` | No | 0.16 ms |
| `resp_e33295ea` | `ambiguous_insufficient` | ✅ PASS | `correct` | `incomplete` | `REASONING_INCOMPLETE` | Yes | 0.03 ms |
| `resp_f0738571` | `ambiguous_insufficient` | ✅ PASS | `undetermined` | `undetermined` | `None` | Yes | 0.02 ms |
| `bench_sign_flip_hop2` | `sign_error` | ✅ PASS | `incorrect` | `supported_error` | `MISC-NUM-DIR-REVERSE` | No | 0.1 ms |
| `bench_faint_overlapping` | `ambiguous_insufficient` | ✅ PASS | `undetermined` | `incomplete` | `None` | Yes | 0.08 ms |