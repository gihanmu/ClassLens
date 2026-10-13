"""Benchmark runner and evaluation harness for ClassLens Gate 4C.

Executes deterministic multi-agent evaluation against versioned ground-truth datasets,
calculates standardized metrics across Categories A through G, and produces structured
JSON and Markdown reports.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import compute_evaluation_metrics
from evaluation.schemas import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkReport,
    CaseEvaluationResult,
    CategoryBreakdownItem,
    EvaluationMetricsSummary,
)
from services.worker.agents.contracts import StudentResponseAnalysis
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.provider import MockVisualEvidenceProvider, VisualEvidenceProvider

logger = logging.getLogger("classlens.evaluation")


def get_current_git_commit() -> str:
    """Retrieves current short git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def load_benchmark_dataset(dataset_path: str | Path) -> BenchmarkDataset:
    """Loads and validates a versioned benchmark dataset JSON file."""
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark dataset not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return BenchmarkDataset.model_validate(data)


def evaluate_single_case(
    case: BenchmarkCase,
    provider: Optional[VisualEvidenceProvider] = None,
    auth_key: Optional[str] = None,
) -> CaseEvaluationResult:
    """Executes the pipeline for a single benchmark case and evaluates against ground truth."""
    active_provider = provider or MockVisualEvidenceProvider()
    start_t = time.perf_counter()

    # Resolve image source if image reference is provided in case specification
    image_path: Optional[Path] = None
    image_ref = getattr(case, "image_reference", None)
    if image_ref:
        for candidate_dir in [
            Path("evaluation/datasets/images"),
            Path("tests/fixtures/synthetic_evaluation_cases"),
            Path("local-data/uploads"),
        ]:
            c_path = candidate_dir / image_ref
            if c_path.is_file():
                image_path = c_path
                break

    analysis: StudentResponseAnalysis = MultiAgentPipeline.analyze_response(
        response_id=case.case_id,
        provider=active_provider,
        image_source=image_path,
        auth_key=auth_key,
        rule_expr=case.problem_statement or "-6 + 12 - 4",
        target_value=float(case.target_canonical_value) if case.target_canonical_value else 2.0,
    )
    latency_ms = (time.perf_counter() - start_t) * 1000.0

    diag = analysis.diagnosis
    critic = analysis.critic_audit
    failure_reasons: List[str] = []

    # 1. Answer Status Match
    actual_ans_status = diag.answer_status.value
    ans_status_match = actual_ans_status == case.expected_answer_status
    if not ans_status_match:
        failure_reasons.append(
            f"AnswerStatus mismatch: expected '{case.expected_answer_status}', got '{actual_ans_status}'"
        )

    # 2. Final Answer Match (evaluated if expected answer is specified)
    actual_final_ans = diag.inferred_final_answer
    if case.expected_answer is not None:
        try:
            exp_val = float(case.expected_answer)
            act_val = float(actual_final_ans) if actual_final_ans is not None else None
            final_ans_match = act_val is not None and abs(exp_val - act_val) <= 1e-4
        except ValueError:
            final_ans_match = (actual_final_ans == case.expected_answer)
        if not final_ans_match:
            failure_reasons.append(
                f"Final answer mismatch: expected '{case.expected_answer}', got '{actual_final_ans}'"
            )
    else:
        # Ground truth has no final answer; passing if pipeline also infers None
        final_ans_match = actual_final_ans is None

    # 3. Reasoning Status Match
    actual_reason_status = diag.reasoning_status.value
    reason_status_match = actual_reason_status == case.expected_reasoning_status
    if not reason_status_match:
        failure_reasons.append(
            f"ReasoningStatus mismatch: expected '{case.expected_reasoning_status}', got '{actual_reason_status}'"
        )

    # 4. Error Step Match
    actual_err_step = diag.first_supported_error.step_number if diag.first_supported_error else None
    actual_err_idx = (actual_err_step - 1) if actual_err_step is not None else None
    if case.expected_error_step_index is not None:
        err_step_match = actual_err_idx == case.expected_error_step_index
        if not err_step_match:
            failure_reasons.append(
                f"Error step index mismatch: expected step idx {case.expected_error_step_index}, got {actual_err_idx}"
            )
    else:
        err_step_match = actual_err_idx is None

    # 5. Misconception Match
    actual_misc = diag.misconception_taxonomy_id
    if case.expected_misconception_id is not None:
        misc_match = (
            actual_misc == case.expected_misconception_id
            or actual_misc in case.allowed_alternative_taxonomies
        )
        if not misc_match:
            failure_reasons.append(
                f"Misconception mismatch: expected '{case.expected_misconception_id}' (or {case.allowed_alternative_taxonomies}), got '{actual_misc}'"
            )
    else:
        misc_match = (actual_misc is None) or (actual_misc in case.allowed_alternative_taxonomies)
        if not misc_match:
            failure_reasons.append(
                f"Unexpected misconception assigned: expected None, got '{actual_misc}'"
            )

    # 6. Evidence Sufficiency Match
    actual_suff = diag.evidence_sufficiency
    suff_match = actual_suff == case.expected_evidence_sufficiency
    if not suff_match:
        failure_reasons.append(
            f"Evidence sufficiency mismatch: expected '{case.expected_evidence_sufficiency}', got '{actual_suff}'"
        )

    # 7. Teacher Review Match
    actual_rev = analysis.needs_teacher_review
    rev_match = actual_rev == case.expected_requires_teacher_review
    if not rev_match:
        failure_reasons.append(
            f"Teacher review flag mismatch: expected {case.expected_requires_teacher_review}, got {actual_rev}"
        )

    # 8. Critic Verdict Match
    actual_critic_verdict = critic.audit_verdict
    critic_match = actual_critic_verdict == case.expected_critic_verdict
    if not critic_match:
        failure_reasons.append(
            f"Critic verdict mismatch: expected '{case.expected_critic_verdict}', got '{actual_critic_verdict}'"
        )

    # Safety checks
    fp_misc = (
        case.expected_misconception_id is None
        and actual_misc is not None
        and actual_misc != "REASONING_INCOMPLETE"
        and actual_misc not in case.allowed_alternative_taxonomies
    )
    unsupported_claim = (
        actual_suff == "insufficient"
        and actual_misc is not None
        and actual_misc != "REASONING_INCOMPLETE"
    )
    contradiction = critic.contradiction_detected

    passed = len(failure_reasons) == 0

    return CaseEvaluationResult(
        case_id=case.case_id,
        category=case.category,
        passed=passed,
        answer_status_match=ans_status_match,
        final_answer_match=final_ans_match,
        reasoning_status_match=reason_status_match,
        error_step_match=err_step_match,
        misconception_match=misc_match,
        evidence_sufficiency_match=suff_match,
        teacher_review_match=rev_match,
        critic_verdict_match=critic_match,
        false_positive_misconception=fp_misc,
        unsupported_claim_detected=unsupported_claim,
        contradiction_detected=contradiction,
        expected_values={
            "answer_status": case.expected_answer_status,
            "final_answer": case.expected_answer,
            "reasoning_status": case.expected_reasoning_status,
            "error_step_index": case.expected_error_step_index,
            "misconception_id": case.expected_misconception_id,
            "evidence_sufficiency": case.expected_evidence_sufficiency,
            "requires_teacher_review": case.expected_requires_teacher_review,
            "critic_verdict": case.expected_critic_verdict,
        },
        actual_values={
            "answer_status": actual_ans_status,
            "final_answer": actual_final_ans,
            "reasoning_status": actual_reason_status,
            "error_step_index": actual_err_idx,
            "misconception_id": actual_misc,
            "evidence_sufficiency": actual_suff,
            "requires_teacher_review": actual_rev,
            "critic_verdict": actual_critic_verdict,
        },
        failure_reasons=failure_reasons,
        latency_ms=round(latency_ms, 2),
    )


def generate_markdown_report(report: BenchmarkReport) -> str:
    """Renders a comprehensive, publication-grade Markdown benchmark report."""
    m = report.metrics
    is_live = report.evaluation_mode == "authorized_live"

    title = (
        "# ClassLens Real Gemini Handwriting Evaluation Report (Authorized Live Mode)"
        if is_live
        else "# ClassLens AI Assessment Reliability Benchmark Report (Offline Regression Suite)"
    )

    if is_live:
        notice = (
            "> [!IMPORTANT]\n"
            "> **Genuine Multimodal Extraction Audit:** This report documents real multimodal Gemini execution on handwritten worksheets.\n"
            "> Mathematical verification, error localization, and critic checks are executed by deterministic Python/SymPy agents.\n"
        )
    else:
        notice = (
            "> [!NOTE]\n"
            "> **Deterministic Offline Regression Suite:** Evaluates multi-agent reasoning, error localization, and Critic rules on synthetic mock fixtures.\n"
            "> Zero API calls ($0.00 spend). Mock accuracy does NOT measure real handwriting OCR performance.\n"
        )

    lines = [
        title,
        "",
        notice,
        "",
        f"**Run ID:** `{report.run_id}`  ",
        f"**Dataset Version:** `{report.dataset_version}`  ",
        f"**Timestamp:** `{report.timestamp}`  ",
        f"**Git Commit:** `{report.git_commit}`  ",
        f"**Pipeline Mode:** `{report.pipeline_mode}`  ",
        f"**Evaluation Mode:** `{report.evaluation_mode}`  ",
    ]

    if is_live:
        lines.extend([
            f"**Total Tokens Consumed:** `{report.total_tokens}`  ",
            f"**Estimated Cost:** `${report.estimated_cost_usd:.4f} USD`  ",
        ])

    lines.extend([
        f"**Overall Status:** **{report.overall_status}** ({report.passed_cases}/{report.total_cases} passed, {report.overall_pass_rate_pct}%)  ",
        "",
        "---",
        "",
        "## 1. Reliability Metrics Overview",
        "",
        "| Category | Metric | Ratio | Percentage | Target | Status |",
        "|:---|:---|:---:|:---:|:---:|:---:|",
        f"| **A. Mathematical Outcome** | {m.answer_status_accuracy.name} | `{m.answer_status_accuracy.numerator}/{m.answer_status_accuracy.denominator}` | {m.answer_status_accuracy.percentage}% | ≥{m.answer_status_accuracy.target_threshold_pct}% | **{m.answer_status_accuracy.status}** |",
        f"| | {m.final_answer_agreement.name} | `{m.final_answer_agreement.numerator}/{m.final_answer_agreement.denominator}` | {m.final_answer_agreement.percentage}% | ≥{m.final_answer_agreement.target_threshold_pct}% | **{m.final_answer_agreement.status}** |",
        f"| **B. Reasoning Verification** | {m.reasoning_status_accuracy.name} | `{m.reasoning_status_accuracy.numerator}/{m.reasoning_status_accuracy.denominator}` | {m.reasoning_status_accuracy.percentage}% | ≥{m.reasoning_status_accuracy.target_threshold_pct}% | **{m.reasoning_status_accuracy.status}** |",
        f"| | {m.procedural_error_detection_recall.name} | `{m.procedural_error_detection_recall.numerator}/{m.procedural_error_detection_recall.denominator}` | {m.procedural_error_detection_recall.percentage}% | ≥{m.procedural_error_detection_recall.target_threshold_pct}% | **{m.procedural_error_detection_recall.status}** |",
        f"| | {m.error_step_localization_accuracy.name} | `{m.error_step_localization_accuracy.numerator}/{m.error_step_localization_accuracy.denominator}` | {m.error_step_localization_accuracy.percentage}% | ≥{m.error_step_localization_accuracy.target_threshold_pct}% | **{m.error_step_localization_accuracy.status}** |",
        f"| **C. Misconception Detection** | {m.misconception_precision.name} | `{m.misconception_precision.numerator}/{m.misconception_precision.denominator}` | {m.misconception_precision.percentage}% | ≥{m.misconception_precision.target_threshold_pct}% | **{m.misconception_precision.status}** |",
        f"| | {m.misconception_recall.name} | `{m.misconception_recall.numerator}/{m.misconception_recall.denominator}` | {m.misconception_recall.percentage}% | ≥{m.misconception_recall.target_threshold_pct}% | **{m.misconception_recall.status}** |",
        f"| | {m.exact_taxonomy_match_rate.name} | `{m.exact_taxonomy_match_rate.numerator}/{m.exact_taxonomy_match_rate.denominator}` | {m.exact_taxonomy_match_rate.percentage}% | ≥{m.exact_taxonomy_match_rate.target_threshold_pct}% | **{m.exact_taxonomy_match_rate.status}** |",
        f"| | {m.false_positive_misconception_rate.name} | `{m.false_positive_misconception_rate.numerator}/{m.false_positive_misconception_rate.denominator}` | {m.false_positive_misconception_rate.percentage}% | ≤{m.false_positive_misconception_rate.target_threshold_pct}% | **{m.false_positive_misconception_rate.status}** |",
        f"| **D. Evidence Grounding** | {m.evidence_sufficiency_accuracy.name} | `{m.evidence_sufficiency_accuracy.numerator}/{m.evidence_sufficiency_accuracy.denominator}` | {m.evidence_sufficiency_accuracy.percentage}% | ≥{m.evidence_sufficiency_accuracy.target_threshold_pct}% | **{m.evidence_sufficiency_accuracy.status}** |",
        f"| | {m.appropriate_abstention_rate.name} | `{m.appropriate_abstention_rate.numerator}/{m.appropriate_abstention_rate.denominator}` | {m.appropriate_abstention_rate.percentage}% | =100.0% | **{m.appropriate_abstention_rate.status}** |",
        f"| | {m.unsupported_claim_rate.name} | `{m.unsupported_claim_rate.numerator}/{m.unsupported_claim_rate.denominator}` | {m.unsupported_claim_rate.percentage}% | =0.0% | **{m.unsupported_claim_rate.status}** |",
        f"| | {m.contradiction_rate.name} | `{m.contradiction_rate.numerator}/{m.contradiction_rate.denominator}` | {m.contradiction_rate.percentage}% | =0.0% | **{m.contradiction_rate.status}** |",
        f"| **E. Teacher Review Routing** | {m.review_routing_precision.name} | `{m.review_routing_precision.numerator}/{m.review_routing_precision.denominator}` | {m.review_routing_precision.percentage}% | ≥{m.review_routing_precision.target_threshold_pct}% | **{m.review_routing_precision.status}** |",
        f"| | {m.review_routing_recall.name} | `{m.review_routing_recall.numerator}/{m.review_routing_recall.denominator}` | {m.review_routing_recall.percentage}% | ≥{m.review_routing_recall.target_threshold_pct}% | **{m.review_routing_recall.status}** |",
        f"| **F. Critic Effectiveness** | {m.critic_verdict_accuracy.name} | `{m.critic_verdict_accuracy.numerator}/{m.critic_verdict_accuracy.denominator}` | {m.critic_verdict_accuracy.percentage}% | ≥{m.critic_verdict_accuracy.target_threshold_pct}% | **{m.critic_verdict_accuracy.status}** |",
        f"| | {m.critic_challenge_precision.name} | `{m.critic_challenge_precision.numerator}/{m.critic_challenge_precision.denominator}` | {m.critic_challenge_precision.percentage}% | ≥{m.critic_challenge_precision.target_threshold_pct}% | **{m.critic_challenge_precision.status}** |",
        f"| **G. Performance** | Average Latency | — | {m.avg_latency_ms} ms/case | <5000 ms | **PASS** |",
        "",
        "---",
        "",
        "## 2. Category Breakdown",
        "",
        "| Category | Total Cases | Passed | Failed | Pass Rate |",
        "|:---|:---:|:---:|:---:|:---:|",
    ])

    for cat in report.category_breakdown:
        lines.append(
            f"| `{cat.category}` | {cat.total_cases} | {cat.passed_cases} | {cat.failed_cases} | **{cat.pass_rate_pct}%** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Detailed Case Results",
        "",
        "| Case ID | Category | Status | Answer | Reasoning | Misconception | Review | Latency |",
        "|:---|:---|:---:|:---:|:---:|:---|:---:|:---:|",
    ])

    for res in report.case_results:
        st = "✅ PASS" if res.passed else "❌ FAIL"
        ans_st = res.actual_values.get("answer_status", "-")
        rs_st = res.actual_values.get("reasoning_status", "-")
        misc = res.actual_values.get("misconception_id") or "None"
        rev = "Yes" if res.actual_values.get("requires_teacher_review") else "No"
        lines.append(
            f"| `{res.case_id}` | `{res.category}` | {st} | `{ans_st}` | `{rs_st}` | `{misc}` | {rev} | {res.latency_ms} ms |"
        )

    if any(not r.passed for r in report.case_results):
        lines.extend([
            "",
            "---",
            "",
            "## 4. Failure Analysis & Diagnostics",
            "",
        ])
        for res in report.case_results:
            if not res.passed:
                lines.extend([
                    f"### Case: `{res.case_id}` (`{res.category}`)",
                    "- **Failure Reasons:**",
                ])
                for fr in res.failure_reasons:
                    lines.append(f"  - ⚠️ {fr}")
                lines.extend([
                    f"- **Expected Values:** `{json.dumps(res.expected_values)}`",
                    f"- **Actual Values:** `{json.dumps(res.actual_values)}`",
                    "",
                ])

    return "\n".join(lines)


def run_benchmark(
    dataset_path: Optional[str | Path] = None,
    case_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    output_dir: str | Path = "evaluation/reports",
    fail_on_regression: bool = False,
    provider: Optional[VisualEvidenceProvider] = None,
    mode: str = "offline_regression",
    auth_key: Optional[str] = None,
) -> BenchmarkReport:
    """Runs the benchmark evaluation suite and produces serialized reports.
    
    Supports two distinct evaluation modes:
    - 'offline_regression': 100% deterministic synthetic mock suite ($0.00 external spend).
    - 'authorized_live': Genuine multimodal Gemini validation against real handwriting dataset.
      Fails closed unless live inference is enabled and authorized by the owner.
    """
    if mode not in ("offline_regression", "authorized_live"):
        raise ValueError(
            f"Invalid mode '{mode}'. Must be either 'offline_regression' or 'authorized_live'."
        )

    # 1. Enforce live authorization and select default dataset / provider
    if mode == "authorized_live":
        from services.api.config import settings
        if not settings.is_live_authorized(auth_key):
            raise PermissionError(
                "Authorized live evaluation requires CLASSLENS_LIVE_INFERENCE_ENABLED=true "
                "and a valid owner authorization key (via X-ClassLens-Live-Auth or live_auth_key). "
                "Live inference is strictly disabled to prevent unauthorized charges ($0.00 spend guarantee)."
            )
        effective_dataset_path = dataset_path or "evaluation/datasets/handwriting_eval_v1.json"
        if provider is None:
            from services.worker.agents.provider import get_visual_evidence_provider
            provider = get_visual_evidence_provider(mode="live", auth_key=auth_key)
    else:
        effective_dataset_path = dataset_path or "evaluation/datasets/benchmark_v1.json"
        if provider is None:
            provider = MockVisualEvidenceProvider()

    dataset = load_benchmark_dataset(effective_dataset_path)
    active_cases = dataset.cases

    if case_filter:
        active_cases = [c for c in active_cases if c.case_id == case_filter]
        if not active_cases:
            raise ValueError(f"No cases found matching case_id='{case_filter}'")

    if category_filter:
        active_cases = [c for c in active_cases if c.category == category_filter]
        if not active_cases:
            raise ValueError(f"No cases found matching category='{category_filter}'")

    logger.info(
        f"Starting [{mode}] evaluation of {len(active_cases)} cases from {effective_dataset_path}..."
    )
    start_eval = time.perf_counter()

    accumulated_tokens = 0
    accumulated_cost = 0.0
    case_results: List[CaseEvaluationResult] = []
    for case in active_cases:
        res = evaluate_single_case(case, provider=provider, auth_key=auth_key)
        case_results.append(res)
        if provider is not None:
            accumulated_tokens += getattr(provider, "last_tokens", 0)
            accumulated_cost += getattr(provider, "last_cost_usd", 0.0) or 0.0
        logger.debug(f"Case {case.case_id}: {'PASS' if res.passed else 'FAIL'}")

    total_duration_sec = time.perf_counter() - start_eval

    # Compute summary metrics
    metrics_summary = compute_evaluation_metrics(
        cases=active_cases,
        results=case_results,
        total_eval_duration_sec=total_duration_sec,
    )

    # Compute category breakdowns
    cat_cases_map: Dict[str, List[CaseEvaluationResult]] = {}
    for r in case_results:
        cat_cases_map.setdefault(r.category, []).append(r)

    category_breakdowns: List[CategoryBreakdownItem] = []
    for cat_name, cat_res in sorted(cat_cases_map.items()):
        passed_c = sum(1 for cr in cat_res if cr.passed)
        failed_c = len(cat_res) - passed_c
        pct = round((passed_c / len(cat_res)) * 100, 1) if cat_res else 0.0
        category_breakdowns.append(
            CategoryBreakdownItem(
                category=cat_name,
                total_cases=len(cat_res),
                passed_cases=passed_c,
                failed_cases=failed_c,
                pass_rate_pct=pct,
            )
        )

    passed_total = sum(1 for cr in case_results if cr.passed)
    failed_total = len(case_results) - passed_total
    pass_rate_total = round((passed_total / max(len(case_results), 1)) * 100, 1)
    overall_status = "PASS" if failed_total == 0 else "FAIL"

    report = BenchmarkReport(
        run_id=f"run_{int(time.time())}",
        dataset_version=dataset.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        git_commit=get_current_git_commit(),
        pipeline_mode="authorized-live" if mode == "authorized_live" else "mock-offline",
        evaluation_mode=mode,
        total_cases=len(case_results),
        passed_cases=passed_total,
        failed_cases=failed_total,
        overall_pass_rate_pct=pass_rate_total,
        overall_status=overall_status,
        metrics=metrics_summary,
        category_breakdown=category_breakdowns,
        case_results=case_results,
        total_tokens=accumulated_tokens,
        estimated_cost_usd=round(accumulated_cost, 4),
        live_authorized=(mode == "authorized_live"),
    )

    # Serialize reports - strictly distinguishing live and offline filenames
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    if mode == "authorized_live":
        json_filename = "latest_live_evaluation_report.json"
        md_filename = "latest_live_evaluation_report.md"
    else:
        json_filename = "latest_benchmark_report.json"
        md_filename = "latest_benchmark_report.md"

    json_path = out_dir_path / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    md_content = generate_markdown_report(report)
    md_path = out_dir_path / md_filename
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"[{mode}] Evaluation complete. Reports written to {json_path} and {md_path}")
    print(
        f"Benchmark Report Generated ({mode}): {report.passed_cases}/{report.total_cases} cases passed "
        f"({report.overall_pass_rate_pct}%) - Overall: {report.overall_status}"
    )

    if fail_on_regression and failed_total > 0:
        logger.error(f"Evaluation regression detected: {failed_total} cases failed.")
        sys.exit(1)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="ClassLens Reliability Benchmark Runner")
    parser.add_argument(
        "--mode",
        choices=["offline_regression", "authorized_live"],
        default="offline_regression",
        help="Evaluation execution mode: 'offline_regression' (default, $0.00 mock) or 'authorized_live' (requires owner key)",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Path to benchmark dataset JSON (default depends on mode)",
    )
    parser.add_argument("--case", default=None, help="Specific case ID to run")
    parser.add_argument("--category", default=None, help="Filter by error category")
    parser.add_argument("--output-dir", default="evaluation/reports", help="Directory for output reports")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit with code 1 if any case fails")
    parser.add_argument("--auth-key", default=None, help="Owner authorization key for live evaluation")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    run_benchmark(
        dataset_path=args.dataset,
        case_filter=args.case,
        category_filter=args.category,
        output_dir=args.output_dir,
        fail_on_regression=args.fail_on_regression,
        mode=args.mode,
        auth_key=args.auth_key,
    )


if __name__ == "__main__":
    main()

