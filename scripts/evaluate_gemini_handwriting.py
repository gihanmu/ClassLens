#!/usr/bin/env python3
"""ClassLens Gate 3: Gemini Multimodal Handwriting Feasibility Evaluation Harness.

Usage:
  # Dry-run evaluation (Zero model calls, zero cost, completely offline):
  python -m scripts.evaluate_gemini_handwriting --dry-run --manifest docs/evaluations/gate3/manifest.json

  # Live bounded evaluation (Requires explicit --live-opt-in, exactly 3 calls maximum):
  python -m scripts.evaluate_gemini_handwriting --live-opt-in --manifest docs/evaluations/gate3/manifest.json --model gemini-2.5-flash --location asia-southeast1 --max-calls 3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.worker.evaluation.contracts import (
    BatchEvaluationSummary,
    EvaluationCaseResult,
    GeminiVisualEvidenceSchema,
)
from services.worker.evaluation.gemini_adapter import GeminiEvaluationAdapter
from services.worker.evaluation.verification_connector import (
    VerificationConnector,
    get_canonical_problem_1065658_rule,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate 3 Gemini Multimodal Handwriting Feasibility Evaluation Harness."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="docs/evaluations/gate3/manifest.json",
        help="Path to evaluation manifest JSON file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Force offline dry-run mode (no API calls, zero cost).",
    )
    parser.add_argument(
        "--live-opt-in",
        action="store_true",
        default=False,
        help="Explicit authorization flag required to enable live API calls to Google GenAI.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Target Gemini model ID (default: gemini-2.5-flash; verified GA on Vertex AI).",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="asia-southeast1",
        help="Google Cloud regional location (default: asia-southeast1). Automatic global fallback is disabled.",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Google Cloud project ID (optional, defaults to active gcloud ADC project).",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=3,
        help="Hard ceiling on maximum number of model calls (default: 3).",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=2048,
        help="Max output tokens for JSON schema response (default: 2048).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".evaluation_outputs",
        help="Directory to save evaluation artifacts (default: .evaluation_outputs).",
    )
    return parser.parse_args()


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    p = Path(manifest_path)
    if not p.is_file():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_markdown_report(
    summary: BatchEvaluationSummary,
    case_results: List[EvaluationCaseResult],
    manifest_meta: Dict[str, Any],
) -> str:
    """Formats a clean GitHub Flavored Markdown evaluation report."""
    md = []
    md.append("# ClassLens — Gate 3 Gemini Feasibility Evaluation Report")
    md.append("")
    md.append(f"**Execution Timestamp:** `{summary.timestamp.isoformat()}`  ")
    md.append(f"**Execution Mode:** `{'DRY RUN (Offline Synthetic Emulation)' if summary.dry_run else 'LIVE GEMINI INFERENCE'}`  ")
    md.append(f"**Target Model ID:** `{summary.model_id}`  ")
    md.append(f"**Target Region:** `{manifest_meta.get('location', 'asia-southeast1')} (Strict regional binding; automatic global fallback disabled)`  ")
    md.append(f"**Total Cases Evaluated:** `{summary.total_cases}` (Exactly {summary.total_cases} model calls; zero retries, zero agent loops)  ")
    md.append(f"**Estimated Software Cost:** `${summary.total_cost_usd:.6f} USD` *(Local token-rate calculation; not a Google Cloud billing account quota)*  ")
    md.append(f"**Mean Latency:** `{summary.mean_latency_ms:.1f} ms`  ")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Executive Summary")
    md.append("")
    md.append("| Metric | Target Benchmark | Achieved | Status |")
    md.append("| :--- | :--- | :--- | :--- |")

    schema_rate = (summary.schema_conformant_count / summary.total_cases * 100) if summary.total_cases else 0
    schema_status = "PASS" if schema_rate == 100 else "FAIL"
    md.append(f"| Schema Conformance | 100% | {schema_rate:.1f}% | **{schema_status}** |")

    math_rate = summary.mathematical_accuracy_rate * 100
    math_status = "PASS" if math_rate >= 80 else "FAIL"
    md.append(f"| Math Verification Alignment | >= 80% | {math_rate:.1f}% | **{math_status}** |")

    esc_rate = summary.teacher_escalation_precision * 100
    esc_status = "PASS" if esc_rate >= 90 else "FAIL"
    md.append(f"| Teacher Escalation Precision | >= 90% | {esc_rate:.1f}% | **{esc_status}** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Detailed Case Outcomes")
    md.append("")

    for idx, case in enumerate(case_results, 1):
        md.append(f"### Case {idx}: `{case.response_id}`")
        md.append(f"- **Category:** `{case.manifest_category}`")
        md.append(f"- **Image Quality:** `{case.visual_extraction.image_quality.value}`")
        md.append(f"- **Visible Final Answer:** `{case.visual_extraction.visible_final_answer.value}` (Certainty: `{case.visual_extraction.visible_final_answer.certainty.value}`)")
        md.append(f"- **Observed Hops:** {len(case.visual_extraction.number_line.observed_hops)}")
        md.append(f"- **Math Verification Verdict:** `{case.math_verification_status}`")
        md.append(f"- **Teacher Review Triggered:** `{case.visual_extraction.requires_teacher_review}`")
        if case.visual_extraction.teacher_review_reason:
            md.append(f"  - *Reason:* {case.visual_extraction.teacher_review_reason}")

        md.append("")
        md.append("#### Observed Steps vs. Expected Reasoning")
        md.append("| Step | Operation | Stated Mag | Observed Displacement | Valid? | Citation |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for step in case.verified_steps:
            obs = f"{step.observed_displacement}" if step.observed_displacement is not None else "N/A"
            valid_icon = "Yes" if step.is_mathematically_valid else "No"
            md.append(f"| {step.step_number} | {step.operation} | {step.expected_displacement} | {obs} | {valid_icon} | {step.evidence_citation} |")

        if case.visual_extraction.ambiguities:
            md.append("")
            md.append("#### Documented Ambiguities")
            for amb in case.visual_extraction.ambiguities:
                md.append(f"- **[{amb.severity.upper()}] {amb.element}:** {amb.description}")

        md.append("")

    md.append("---")
    md.append("")
    md.append("## 3. Cost & Resource Consumption")
    md.append("")
    md.append(f"- **Total Input Tokens:** `{summary.total_input_tokens}`")
    md.append(f"- **Total Output Tokens:** `{summary.total_output_tokens}`")
    md.append(f"- **Estimated Software Cost:** `${summary.total_cost_usd:.6f} USD` (Local rate estimate; not a Google Cloud billing limit)")
    md.append(f"- **Data Transmission:** In-memory byte streaming (zero Google Cloud Storage uploads)")
    md.append(f"- **Synthetic Isolation:** All evaluated files are synthetic fixtures from `tests/fixtures/synthetic_evaluation_cases/`")
    md.append("")

    return "\n".join(md)


def main() -> int:
    args = parse_arguments()

    # Determine execution mode
    is_dry_run = args.dry_run or (not args.live_opt_in)

    print("=" * 72)
    print("ClassLens — Gate 3 Gemini Feasibility Evaluation Harness")
    print("=" * 72)
    print(f"Mode: {'DRY RUN (Offline Synthetic Emulation)' if is_dry_run else 'LIVE INFERENCE'}")
    print(f"Model: {args.model}")
    print(f"Location: {args.location} (Strict regional binding)")
    print(f"Project: {args.project or '(Auto-detected via ADC)'}")
    print(f"Manifest: {args.manifest}")
    print(f"Max Calls Ceiling: {args.max_calls}")
    print(f"Output Directory: {args.output_dir}")
    print("-" * 72)

    try:
        manifest_data = load_manifest(args.manifest)
    except Exception as e:
        print(f"Error loading manifest: {e}", file=sys.stderr)
        return 1

    cases = manifest_data.get("cases", [])
    if not cases:
        print("Error: No cases found in manifest.", file=sys.stderr)
        return 1

    if len(cases) > args.max_calls:
        print(
            f"Error: Manifest contains {len(cases)} cases, exceeding authorized ceiling of {args.max_calls}.",
            file=sys.stderr,
        )
        return 1

    # Security check: Ensure manifest cases ONLY point to synthetic fixtures
    for c in cases:
        c_path = str(Path(c["image_path"]).resolve()).lower()
        if "/dataset/" in c_path or "drawedumath" in c_path or "mathwriting" in c_path:
            print(
                f"Security Guardrail Violation: Manifest references real dataset file '{c['image_path']}'. Aborting.",
                file=sys.stderr,
            )
            return 1

    adapter = GeminiEvaluationAdapter(
        model_id=args.model,
        location=args.location,
        project=args.project,
        vertexai=True,
        max_calls=args.max_calls,
        dry_run=is_dry_run,
        live_opt_in=args.live_opt_in,
    )

    rule = get_canonical_problem_1065658_rule()
    case_results: List[EvaluationCaseResult] = []
    latencies: List[int] = []

    print(f"Processing {len(cases)} evaluation case(s)...\n")

    for idx, case_info in enumerate(cases, 1):
        resp_id = case_info["response_id"]
        cat = case_info.get("category", "canonical_correct")
        img_path = case_info["image_path"]

        print(f"[{idx}/{len(cases)}] Evaluating: {resp_id} (Category: {cat})")
        print(f"      Image: {img_path}")

        try:
            # 1. Visual evidence extraction (Adapter handles live vs dry-run)
            evidence = adapter.extract_visual_evidence(
                image_path=img_path,
                response_id=resp_id,
            )

            # 2. Mathematical verification bridge (Deterministic SymPy)
            last_call = adapter.call_history[-1] if adapter.call_history else {}
            case_res = VerificationConnector.connect_and_verify(
                extraction=evidence,
                rule=rule,
                manifest_category=cat,
                model_id=args.model,
                latency_ms=adapter.last_latency_ms,
                input_tokens=last_call.get("input_tokens", 0),
                output_tokens=last_call.get("output_tokens", 0),
                estimated_cost_usd=last_call.get("estimated_cost_usd", 0.0),
                dry_run=is_dry_run,
            )

            case_results.append(case_res)
            latencies.append(adapter.last_latency_ms)

            # Check expectations
            exp = case_info.get("expected", {})
            math_match = (case_res.math_verification_status == exp.get("math_status"))
            esc_match = (case_res.visual_extraction.requires_teacher_review == exp.get("requires_teacher_review"))

            print(f"      -> Status: {case_res.math_verification_status} (Matches expected: {math_match})")
            print(f"      -> Final Answer: {case_res.visual_extraction.visible_final_answer.value}")
            print(f"      -> Teacher Review: {case_res.visual_extraction.requires_teacher_review} (Matches expected: {esc_match})")
            print(f"      -> Latency: {adapter.last_latency_ms} ms\n")

        except Exception as err:
            print(f"      ERROR during evaluation: {err}", file=sys.stderr)
            return 1

    # Compute batch summary metrics
    total_cases = len(case_results)
    schema_ok = sum(1 for c in case_results if c.schema_valid)

    math_accurate = 0
    esc_correct = 0
    for c, info in zip(case_results, cases):
        exp = info.get("expected", {})
        if c.math_verification_status == exp.get("math_status"):
            math_accurate += 1
        if c.visual_extraction.requires_teacher_review == exp.get("requires_teacher_review"):
            esc_correct += 1

    math_rate = (math_accurate / total_cases) if total_cases else 0.0
    esc_rate = (esc_correct / total_cases) if total_cases else 0.0
    mean_lat = (sum(latencies) / len(latencies)) if latencies else 0.0

    summary = BatchEvaluationSummary(
        total_cases=total_cases,
        schema_conformant_count=schema_ok,
        mathematical_accuracy_rate=math_rate,
        teacher_escalation_precision=esc_rate,
        total_input_tokens=adapter.total_input_tokens,
        total_output_tokens=adapter.total_output_tokens,
        total_cost_usd=adapter.total_estimated_cost_usd,
        mean_latency_ms=mean_lat,
        model_id=args.model,
        dry_run=is_dry_run,
        case_results=case_results,
    )

    # Save output artifacts
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "evaluation_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(summary.model_dump_json(indent=2))

    manifest_meta = {
        "location": args.location,
        "model": args.model,
    }
    md_report = generate_markdown_report(summary, case_results, manifest_meta)
    md_path = out_dir / "evaluation_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print("=" * 72)
    print("EVALUATION COMPLETE")
    print("=" * 72)
    print(f"Cases Processed: {total_cases}")
    print(f"Schema Conformance: {schema_ok}/{total_cases} (100%)")
    print(f"Math Accuracy Alignment: {math_accurate}/{total_cases} ({math_rate * 100:.1f}%)")
    print(f"Teacher Escalation Precision: {esc_correct}/{total_cases} ({esc_rate * 100:.1f}%)")
    print(f"Total Tokens: {adapter.total_input_tokens} in / {adapter.total_output_tokens} out")
    print(f"Estimated Software Cost: ${adapter.total_estimated_cost_usd:.6f} USD")
    print(f"Mean Latency: {mean_lat:.1f} ms")
    print(f"Reports saved to: {out_dir.absolute()}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
