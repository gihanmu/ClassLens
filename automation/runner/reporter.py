"""Report generation engine for ClassLens autonomous development.

Generates both machine-readable (JSON) and human-readable (Markdown) reports
documenting task execution, observed test results, security findings, and costs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.runner.config import REPORTS_DIR


@dataclass
class ExecutionReportData:
    task_id: str
    task_title: str
    status: str  # "SUCCESS", "FAILED", "SAFETY_VIOLATION", "DRY_RUN"
    branch: str
    base_branch: str
    commit_sha: Optional[str]
    pull_request_url: Optional[str]
    summary_of_changes: str
    files_modified: List[str]
    test_results: List[Dict[str, Any]]
    build_results: List[Dict[str, Any]]
    security_findings: List[str]
    external_api_calls_made: int
    estimated_external_cost_usd: float
    repair_attempts_used: int
    blockers: List[str] = field(default_factory=list)
    next_recommended_task: Optional[str] = None
    agent_assumptions: List[str] = field(default_factory=list)
    observed_results: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReportGenerator:
    """Generates JSON and Markdown reports in automation/reports/."""

    def __init__(self, reports_dir: Path = REPORTS_DIR) -> None:
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_reports(self, data: ExecutionReportData) -> Tuple[Path, Path]:
        """Write both JSON and Markdown reports to disk."""
        json_path = self.reports_dir / f"{data.task_id.lower()}_report.json"
        md_path = self.reports_dir / f"{data.task_id.lower()}_report.md"

        # 1. Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=2)

        # 2. Write Markdown
        md_content = self._render_markdown(data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path

    def _render_markdown(self, d: ExecutionReportData) -> str:
        status_badge = "✅ PASSED" if d.status in ["SUCCESS", "DRY_RUN"] else "❌ FAILED"
        if d.status == "SAFETY_VIOLATION":
            status_badge = "🛑 SAFETY VIOLATION"

        lines = [
            f"# ClassLens Autonomous Execution Report — {d.task_id}",
            "",
            f"**Task Title:** {d.task_title}  ",
            f"**Execution Status:** {status_badge} (`{d.status}`)  ",
            f"**Execution Timestamp:** {d.timestamp}  ",
            f"**Branch:** `{d.branch}` (Base: `{d.base_branch}`)  ",
            f"**Commit:** `{d.commit_sha or 'N/A'}`  ",
            f"**Pull Request:** {d.pull_request_url or 'N/A'}  ",
            "",
            "---",
            "",
            "## 1. Safety & Financial Compliance (Observed)",
            "",
            f"- **External API Calls Made:** `{d.external_api_calls_made}`",
            f"- **Estimated External Cost (USD):** `${d.estimated_external_cost_usd:.2f}`",
            f"- **Repair Attempts Used:** `{d.repair_attempts_used}` / 3",
            f"- **Security Findings:** `{len(d.security_findings)}` issue(s) detected",
            "",
        ]

        if d.security_findings:
            lines.append("### Security Alerts:")
            for s in d.security_findings:
                lines.append(f"- ⚠️ {s}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 2. Summary of Changes",
            "",
            d.summary_of_changes,
            "",
            "### Files Modified:",
            "",
        ])

        if d.files_modified:
            for f in d.files_modified:
                lines.append(f"- `{f}`")
        else:
            lines.append("- *No files modified (Dry run or verification only)*")

        lines.extend([
            "",
            "---",
            "",
            "## 3. Observed Test & Build Results",
            "",
            "| Command | Exit Code | Duration | Status |",
            "|---|---|---|---|",
        ])

        for tr in d.test_results:
            st = "PASS ✅" if tr.get("passed") else "FAIL ❌"
            lines.append(f"| `{tr.get('command')}` | `{tr.get('exit_code')}` | `{tr.get('duration_seconds')}s` | {st} |")

        for br in d.build_results:
            st = "PASS ✅" if br.get("passed") else "FAIL ❌"
            lines.append(f"| `{br.get('command')}` | `{br.get('exit_code')}` | `{br.get('duration_seconds')}s` | {st} |")

        if not d.test_results and not d.build_results:
            lines.append("| *None executed* | - | - | - |")

        lines.extend([
            "",
            "---",
            "",
            "## 4. Distinction Between Observed Results vs Agent Assumptions",
            "",
            "### Observed Execution Results (Facts):",
        ])

        for k, v in d.observed_results.items():
            lines.append(f"- **{k}:** {v}")

        lines.extend([
            "",
            "### Agent Assumptions & Hypotheses:",
        ])

        if d.agent_assumptions:
            for a in d.agent_assumptions:
                lines.append(f"- {a}")
        else:
            lines.append("- *No unverified agent assumptions recorded.*")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Blockers & Next Recommended Task",
            "",
        ])

        if d.blockers:
            lines.append("### Blockers:")
            for b in d.blockers:
                lines.append(f"- 🛑 {b}")
        else:
            lines.append("- **Blockers:** None")

        lines.append(f"- **Next Recommended Task:** `{d.next_recommended_task or 'Awaiting review'}`")
        lines.append("")

        return "\n".join(lines)
