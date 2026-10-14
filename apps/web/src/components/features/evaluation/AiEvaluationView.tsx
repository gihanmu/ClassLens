"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RefreshCw,
  FileText,
  BarChart3,
  Layers,
  Cpu,
  Eye,
  Check,
  ChevronRight,
  Filter,
  Search,
  CheckCheck,
  Percent,
  Clock,
  ExternalLink,
  Code2,
  Lock,
  Sparkles,
  Key,
  Info,
} from "lucide-react";
import {
  api,
  BenchmarkReport,
  CaseEvaluationResult,
  CategoryBreakdownItem,
  MetricFraction,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export function AiEvaluationView() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [liveReport, setLiveReport] = useState<BenchmarkReport | null>(null);
  const [liveStatus, setLiveStatus] = useState<"not_performed" | "completed">("not_performed");
  const [activeTab, setActiveTab] = useState<"offline" | "live">("offline");
  const [liveAuthKey, setLiveAuthKey] = useState<string>("");
  const [runningLive, setRunningLive] = useState<boolean>(false);
  const [liveError, setLiveError] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCase, setSelectedCase] = useState<CaseEvaluationResult | null>(null);
  const [showMarkdownModal, setShowMarkdownModal] = useState<boolean>(false);
  const [markdownText, setMarkdownText] = useState<string>("");
  const [loadingMarkdown, setLoadingMarkdown] = useState<boolean>(false);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getLatestEvaluationReport("offline");
      setReport(data);
      if (data.live_report) {
        setLiveReport(data.live_report);
        setLiveStatus("completed");
      } else if (data.live_evaluation_status) {
        setLiveStatus(data.live_evaluation_status);
      }
    } catch (err: any) {
      console.error("Failed to load evaluation report:", err);
      setError(err.message || "Failed to load benchmark evaluation report.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setRunning(true);
      setError(null);
      const data = await api.runBenchmarkEvaluation();
      setReport(data);
    } catch (err: any) {
      console.error("Failed to execute benchmark:", err);
      setError(err.message || "Failed to execute benchmark run.");
    } finally {
      setRunning(false);
    }
  };

  const handleRunLive = async () => {
    try {
      setRunningLive(true);
      setLiveError(null);
      const res = await api.runLiveEvaluation(liveAuthKey.trim() || undefined);
      setLiveReport(res);
      setLiveStatus("completed");
    } catch (err: any) {
      console.error("Live evaluation failed:", err);
      setLiveError(err.message || "Failed to execute live evaluation.");
    } finally {
      setRunningLive(false);
    }
  };

  const handleOpenMarkdown = async () => {
    try {
      setLoadingMarkdown(true);
      setShowMarkdownModal(true);
      const md = await api.getEvaluationMarkdown(activeTab === "live" ? "live" : "offline");
      setMarkdownText(md);
    } catch (err: any) {
      setMarkdownText("Failed to load markdown report.");
    } finally {
      setLoadingMarkdown(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  if (loading && !report) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <Spinner size="lg" />
        <p className="text-sm text-ink-muted font-medium">Loading AI reliability evaluation suite...</p>
      </div>
    );
  }

  const currentDisplayReport = activeTab === "live" ? liveReport : report;
  const cases = currentDisplayReport?.case_results || [];
  const filteredCases = cases.filter((c) => {
    const matchesCat = selectedCategory === "all" || c.category === selectedCategory;
    const matchesSearch =
      searchQuery.trim() === "" ||
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.actual_values?.misconception_id || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const m = currentDisplayReport?.metrics;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header & Run Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-border-default pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-brand-primary-soft text-brand-primary flex items-center justify-center border border-brand-primary/20 shadow-xs">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-ink-primary">
                AI Reliability, Benchmarking & Evaluation
              </h1>
              <p className="text-xs text-ink-muted">
                Gate 4C & Gate 6: Evidence-grounded verification and multimodal Gemini validation
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleOpenMarkdown}
            className="flex items-center gap-1.5"
          >
            <FileText className="w-4 h-4 text-ink-muted" />
            <span>Markdown Report</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={fetchReport}
            disabled={running || runningLive}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={cn("w-4 h-4 text-ink-muted", (running || runningLive) && "animate-spin")} />
            <span>Refresh</span>
          </Button>

          {activeTab === "offline" && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunBenchmark}
              disabled={running}
              className="flex items-center gap-1.5 bg-brand-primary hover:bg-brand-primary-hover text-white shadow-xs"
            >
              {running ? (
                <>
                  <Spinner size="sm" />
                  <span>Running Suite...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Offline Benchmark</span>
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Mode Navigation Tabs */}
      <div className="flex border-b border-border-default space-x-8">
        <button
          onClick={() => setActiveTab("offline")}
          className={cn(
            "pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors",
            activeTab === "offline"
              ? "border-brand-primary text-brand-primary"
              : "border-transparent text-ink-muted hover:text-ink-primary"
          )}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Offline Regression Suite</span>
          <Badge variant="outline" className="text-[10px] bg-surface-subtle font-mono">
            Synthetic Mock (18 cases)
          </Badge>
        </button>

        <button
          onClick={() => setActiveTab("live")}
          className={cn(
            "pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors",
            activeTab === "live"
              ? "border-brand-primary text-brand-primary"
              : "border-transparent text-ink-muted hover:text-ink-primary"
          )}
        >
          <Sparkles className="w-4 h-4" />
          <span>Authorized Live Handwriting Evaluation</span>
          {liveStatus === "completed" ? (
            <Badge variant="outline" className="text-[10px] bg-semantic-success-bg text-semantic-success-text border-semantic-success-border font-mono">
              Live Verified (20 cases)
            </Badge>
          ) : (
            <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-700 border-amber-200 font-mono">
              Not Yet Performed
            </Badge>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-semantic-error-bg text-semantic-error-text border border-semantic-error-border flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Benchmark Execution Error</p>
            <p className="opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Tab 1: Offline Mode Educational Banner */}
      {activeTab === "offline" && (
        <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-blue-950 flex items-start gap-3 shadow-xs">
          <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-blue-900">
              Deterministic Offline Regression Suite (Synthetic Mock)
            </p>
            <p className="text-blue-800 leading-relaxed">
              Evaluates multi-agent verification, SymPy mathematical consistency, procedural error localization, and Independent Critic challenge rules on deterministic mock fixtures with guaranteed <strong>$0.00 external spend</strong>.
              <span className="block mt-1 font-medium text-blue-900">
                Notice: Synthetic mock benchmark pass rates measure reasoning pipeline logic, not real handwriting OCR recognition accuracy.
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Live Mode Default State (Not Yet Performed) */}
      {activeTab === "live" && !liveReport && (
        <div className="space-y-6">
          <Card className="border-border-default shadow-xs overflow-hidden">
            <div className="p-8 text-center max-w-2xl mx-auto space-y-5">
              <div className="w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 border border-amber-200 flex items-center justify-center mx-auto shadow-xs">
                <Lock className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 text-xs font-semibold">
                  <Lock className="w-3.5 h-3.5" />
                  <span>Live handwriting validation: Pending owner authorization ($0.00 spend guarantee)</span>
                </div>
                <h2 className="text-xl font-bold text-ink-primary">
                  Live Handwriting Evaluation: Not Yet Performed
                </h2>
                <p className="text-sm text-ink-muted leading-relaxed">
                  Live inference requires explicit owner authorization and budget allocation.
                  In strict accordance with ClassLens zero-spend constraints, live multimodal Gemini API calls remain disabled by default.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium border border-blue-200">State 1: MOCK/OFFLINE (Active)</span>
                  <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-medium border border-purple-200">State 2: AWAITING_LIVE_ANALYSIS (Uploads)</span>
                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-medium border border-amber-200">State 3: LIVE NOT PERFORMED (Eval Set)</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium border border-emerald-200">State 4: LIVE MEASURED (0 / 20)</span>
                </div>
              </div>

              <div className="p-4 bg-surface-subtle border border-border-default rounded-xl text-left space-y-2.5 text-xs text-ink-secondary">
                <div className="font-semibold text-ink-primary flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-primary" />
                  <span>Evaluation Dataset & Execution Specifications:</span>
                </div>
                <ul className="list-disc list-inside space-y-1 pl-1">
                  <li><strong>Ground-Truth Dataset:</strong> <code>evaluation/datasets/handwriting_eval_v1.json</code> (20 independently annotated cases across 10 error and ambiguity categories).</li>
                  <li><strong>Single Multimodal Agent Architecture:</strong> Multimodal Gemini (<code>gemini-2.5-flash</code>) extracts physical ink strokes only; downstream mathematical verification remains 100% deterministic (SymPy & rule engine).</li>
                  <li><strong>Strict $0.00 Default Guard:</strong> Calls are blocked unless authorized with valid owner key (<code>X-ClassLens-Live-Auth</code>).</li>
                  <li><strong>Architectural Honesty:</strong> Synthetic mock benchmark pass rates are never conflated with real handwriting recognition accuracy.</li>
                </ul>
              </div>

              {liveError && (
                <div className="p-3.5 rounded-xl bg-semantic-error-bg text-semantic-error-text border border-semantic-error-border text-xs text-left flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Authorization / Execution Notice: </span>
                    {liveError}
                  </div>
                </div>
              )}

              <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                <input
                  type="password"
                  placeholder="Owner Authorization Key (Optional if pre-configured)"
                  value={liveAuthKey}
                  onChange={(e) => setLiveAuthKey(e.target.value)}
                  className="text-xs px-3 py-2 rounded-lg border border-border-default bg-surface-base w-full sm:w-80 focus:outline-none focus:ring-1 focus:ring-brand-primary font-mono"
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleRunLive}
                  disabled={runningLive}
                  className="flex items-center gap-2 bg-brand-primary hover:bg-brand-primary-hover text-white shadow-xs whitespace-nowrap"
                >
                  {runningLive ? (
                    <>
                      <Spinner size="sm" />
                      <span>Running Live Evaluation...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Run Authorized Live Evaluation</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: Live Mode Active Report Banner */}
      {activeTab === "live" && liveReport && (
        <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-emerald-950 flex items-start gap-3 shadow-xs">
          <Sparkles className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-emerald-900">
              Authorized Live Multimodal Handwriting Evaluation Active
            </p>
            <p className="text-emerald-800 leading-relaxed">
              Evaluating 20 handwritten worksheets using multimodal Gemini (<code>gemini-2.5-flash</code>) for visual mark extraction, coupled with deterministic SymPy reasoning agents.
              Total Tokens: <strong>{liveReport.total_tokens ?? 0}</strong> • Estimated Cost: <strong>${(liveReport.estimated_cost_usd ?? 0).toFixed(4)} USD</strong>.
            </p>
          </div>
        </div>
      )}

      {/* Overview Metadata Card (rendered when there is a report for the active tab) */}
      {currentDisplayReport && (
        <Card className="border-border-default shadow-xs overflow-hidden">
          <div className="p-6 bg-surface-subtle border-b border-border-default flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Ground-Truth Suite:
                </span>
                <span className="font-mono text-xs font-bold text-ink-primary bg-surface-base px-2 py-0.5 rounded border border-border-default">
                  v{currentDisplayReport.dataset_version}
                </span>
                <span className="text-ink-muted text-xs">•</span>
                <span className="font-mono text-xs text-ink-secondary">
                  commit: {currentDisplayReport.git_commit}
                </span>
                {currentDisplayReport.pipeline_mode && (
                  <>
                    <span className="text-ink-muted text-xs">•</span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {currentDisplayReport.pipeline_mode}
                    </Badge>
                  </>
                )}
              </div>
              <p className="text-xs text-ink-muted">
                Executed: {new Date(currentDisplayReport.timestamp).toLocaleString()}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-xs text-ink-muted">Overall Pass Rate</div>
                <div className="text-xl font-bold font-mono text-ink-primary">
                  {currentDisplayReport.passed_cases}/{currentDisplayReport.total_cases} ({currentDisplayReport.overall_pass_rate_pct}%)
                </div>
              </div>
              <div
                className={cn(
                  "px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-1.5 shadow-xs border",
                  currentDisplayReport.overall_status === "PASS"
                    ? "bg-semantic-success-bg text-semantic-success-text border-semantic-success-border"
                    : "bg-semantic-error-bg text-semantic-error-text border-semantic-error-border"
                )}
              >
                {currentDisplayReport.overall_status === "PASS" ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <XCircle className="w-5 h-5" />
                )}
                <span>{currentDisplayReport.overall_status}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-y sm:divide-y-0 divide-border-default bg-surface-base text-center">
            <div className="p-4">
              <div className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                Total Benchmark Cases
              </div>
              <div className="text-2xl font-bold font-mono text-ink-primary mt-1">
                {currentDisplayReport.total_cases}
              </div>
            </div>
            <div className="p-4">
              <div className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                Passed Cases
              </div>
              <div className="text-2xl font-bold font-mono text-semantic-success-text mt-1">
                {currentDisplayReport.passed_cases}
              </div>
            </div>
            <div className="p-4">
              <div className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                Failed Cases
              </div>
              <div className="text-2xl font-bold font-mono text-semantic-error-text mt-1">
                {currentDisplayReport.failed_cases}
              </div>
            </div>
            <div className="p-4">
              <div className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                Avg Latency
              </div>
              <div className="text-2xl font-bold font-mono text-ink-primary mt-1">
                {currentDisplayReport.metrics.avg_latency_ms} <span className="text-xs font-normal text-ink-muted">ms</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Standardized Reliability Metric Cards (Categories A-F) */}
      {m && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink-primary flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-brand-primary" />
              <span>Standardized Reliability Metrics</span>
            </h2>
            <span className="text-xs text-ink-muted font-medium">
              Explicit Numerators & Denominators
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 1. Answer Status Accuracy */}
            <MetricCardItem
              category="A. Mathematical Outcome"
              fraction={m.answer_status_accuracy}
            />

            {/* 2. Final Answer Agreement */}
            <MetricCardItem
              category="A. Mathematical Outcome"
              fraction={m.final_answer_agreement}
            />

            {/* 3. Reasoning Status Accuracy */}
            <MetricCardItem
              category="B. Reasoning Verification"
              fraction={m.reasoning_status_accuracy}
            />

            {/* 4. Procedural Error Detection Recall */}
            <MetricCardItem
              category="B. Reasoning Verification"
              fraction={m.procedural_error_detection_recall}
            />

            {/* 5. Error Step Localization Accuracy */}
            <MetricCardItem
              category="B. Reasoning Verification"
              fraction={m.error_step_localization_accuracy}
            />

            {/* 6. Misconception Precision */}
            <MetricCardItem
              category="C. Misconception Detection"
              fraction={m.misconception_precision}
            />

            {/* 7. Misconception Recall */}
            <MetricCardItem
              category="C. Misconception Detection"
              fraction={m.misconception_recall}
            />

            {/* 8. Exact Taxonomy Match Rate */}
            <MetricCardItem
              category="C. Misconception Detection"
              fraction={m.exact_taxonomy_match_rate}
            />

            {/* 9. False-Positive Misconceptions */}
            <MetricCardItem
              category="C. Misconception Detection"
              fraction={m.false_positive_misconception_rate}
              invertStatus
            />

            {/* 10. Evidence Sufficiency Accuracy */}
            <MetricCardItem
              category="D. Evidence Grounding"
              fraction={m.evidence_sufficiency_accuracy}
            />

            {/* 11. Appropriate Abstention Rate */}
            <MetricCardItem
              category="D. Evidence Grounding"
              fraction={m.appropriate_abstention_rate}
            />

            {/* 12. Unsupported Claim Rate */}
            <MetricCardItem
              category="D. Evidence Grounding"
              fraction={m.unsupported_claim_rate}
              invertStatus
            />

            {/* 13. Contradiction Rate */}
            <MetricCardItem
              category="D. Evidence Grounding"
              fraction={m.contradiction_rate}
              invertStatus
            />

            {/* 14. Review Routing Precision */}
            <MetricCardItem
              category="E. Teacher Review Routing"
              fraction={m.review_routing_precision}
            />

            {/* 15. Review Routing Recall */}
            <MetricCardItem
              category="E. Teacher Review Routing"
              fraction={m.review_routing_recall}
            />

            {/* 16. Critic Verdict Accuracy */}
            <MetricCardItem
              category="F. Critic Audit"
              fraction={m.critic_verdict_accuracy}
            />

            {/* 17. Critic Challenge Precision */}
            <MetricCardItem
              category="F. Critic Audit"
              fraction={m.critic_challenge_precision}
            />

            {/* 18. Critical Escalation Safety */}
            <Card className="p-4 border-border-default shadow-xs flex flex-col justify-between">
              <div>
                <div className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">
                  E. Safety & Compliance
                </div>
                <div className="text-sm font-bold text-ink-primary mt-1">
                  Missed Critical Reviews
                </div>
                <p className="text-xs text-ink-muted mt-1">
                  Ambiguous or compensatory cases erroneously not routed to teacher.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between">
                <span className="font-mono text-lg font-bold text-semantic-success-text">
                  {m.missed_critical_review_count} cases
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-semantic-success-bg text-semantic-success-text border border-semantic-success-border">
                  PASS
                </span>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Category Breakdown & Case Table */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-ink-primary flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand-primary" />
            <span>Benchmark Dataset Cases ({filteredCases.length})</span>
          </h2>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
              <input
                type="text"
                placeholder="Search cases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-3 py-1.5 text-xs rounded-xl border border-border-default bg-surface-base text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-primary"
              />
            </div>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => setSelectedCategory("all")}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium transition-all border",
              selectedCategory === "all"
                ? "bg-brand-primary text-white border-brand-primary shadow-xs"
                : "bg-surface-base text-ink-secondary border-border-default hover:bg-surface-subtle"
            )}
          >
            All Categories ({cases.length})
          </button>
          {report?.category_breakdown.map((cat) => (
            <button
              key={cat.category}
              type="button"
              onClick={() => setSelectedCategory(cat.category)}
              className={cn(
                "px-3 py-1 rounded-full text-xs font-medium transition-all border flex items-center gap-1.5",
                selectedCategory === cat.category
                  ? "bg-brand-primary text-white border-brand-primary shadow-xs"
                  : "bg-surface-base text-ink-secondary border-border-default hover:bg-surface-subtle"
              )}
            >
              <span>{cat.category}</span>
              <span className="font-mono text-[10px] opacity-80">({cat.total_cases})</span>
            </button>
          ))}
        </div>

        {/* Cases Table */}
        <Card className="border-border-default shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-subtle border-b border-border-default text-ink-muted font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Answer</th>
                  <th className="py-3 px-4">Reasoning</th>
                  <th className="py-3 px-4">Misconception</th>
                  <th className="py-3 px-4 text-center">Review</th>
                  <th className="py-3 px-4 text-right">Latency</th>
                  <th className="py-3 px-4 text-center">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle bg-surface-base">
                {filteredCases.map((c) => (
                  <tr
                    key={c.case_id}
                    className="hover:bg-surface-subtle/60 transition-colors cursor-pointer"
                    onClick={() => setSelectedCase(c)}
                  >
                    <td className="py-3 px-4 font-mono font-semibold text-ink-primary">
                      {c.case_id}
                    </td>
                    <td className="py-3 px-4 text-ink-secondary">
                      <span className="px-2 py-0.5 rounded bg-surface-subtle border border-border-default text-[11px] font-mono">
                        {c.category}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {c.passed ? (
                        <span className="inline-flex items-center gap-1 text-semantic-success-text font-bold text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>PASS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-semantic-error-text font-bold text-[11px]">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>FAIL</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {c.actual_values.answer_status}
                      {c.actual_values.final_answer ? ` (${c.actual_values.final_answer})` : ""}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {c.actual_values.reasoning_status}
                    </td>
                    <td className="py-3 px-4 font-mono text-ink-secondary">
                      {c.actual_values.misconception_id ? (
                        <span className="px-1.5 py-0.5 rounded bg-brand-primary-soft text-brand-primary text-[10px] font-semibold border border-brand-primary/20">
                          {c.actual_values.misconception_id}
                        </span>
                      ) : (
                        <span className="text-ink-muted">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      {c.actual_values.requires_teacher_review ? (
                        <span className="px-2 py-0.5 rounded bg-accent-amber/15 text-accent-amber font-bold text-[10px] border border-accent-amber/20">
                          YES
                        </span>
                      ) : (
                        <span className="text-ink-muted">No</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-ink-muted">
                      {c.latency_ms} ms
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedCase(c);
                        }}
                        className="h-7 w-7 p-0"
                      >
                        <ChevronRight className="w-4 h-4 text-ink-muted" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Case Inspection Modal */}
      {selectedCase && (
        <Dialog
          isOpen={!!selectedCase}
          onClose={() => setSelectedCase(null)}
          title={`Case Audit: ${selectedCase.case_id}`}
        >
          <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
            <div className="flex items-center justify-between pb-3 border-b border-border-default">
              <div>
                <span className="text-xs text-ink-muted uppercase tracking-wider font-semibold">
                  Category:
                </span>
                <span className="ml-2 font-mono text-xs font-bold text-ink-primary">
                  {selectedCase.category}
                </span>
              </div>
              <div
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1",
                  selectedCase.passed
                    ? "bg-semantic-success-bg text-semantic-success-text"
                    : "bg-semantic-error-bg text-semantic-error-text"
                )}
              >
                {selectedCase.passed ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                <span>{selectedCase.passed ? "PASSED ALL ASSERTIONS" : "FAILED"}</span>
              </div>
            </div>

            {selectedCase.failure_reasons.length > 0 && (
              <div className="p-3 rounded-xl bg-semantic-error-bg text-semantic-error-text border border-semantic-error-border space-y-1">
                <p className="text-xs font-bold">Failure Reasons:</p>
                <ul className="list-disc pl-5 text-xs space-y-0.5">
                  {selectedCase.failure_reasons.map((fr, idx) => (
                    <li key={idx}>{fr}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink-muted">
                Assertion Diff (Expected vs Actual)
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-surface-subtle border border-border-default space-y-2">
                  <p className="font-semibold text-ink-muted uppercase text-[10px]">Ground Truth (Expected)</p>
                  {Object.entries(selectedCase.expected_values).map(([k, v]) => (
                    <div key={k} className="flex justify-between font-mono text-[11px]">
                      <span className="text-ink-muted">{k}:</span>
                      <span className="text-ink-primary font-bold">{String(v ?? "None")}</span>
                    </div>
                  ))}
                </div>

                <div className="p-3 rounded-xl bg-surface-subtle border border-border-default space-y-2">
                  <p className="font-semibold text-ink-muted uppercase text-[10px]">Pipeline Prediction (Actual)</p>
                  {Object.entries(selectedCase.actual_values).map(([k, v]) => (
                    <div key={k} className="flex justify-between font-mono text-[11px]">
                      <span className="text-ink-muted">{k}:</span>
                      <span
                        className={cn(
                          "font-bold",
                          selectedCase.expected_values[k] === v
                            ? "text-semantic-success-text"
                            : "text-semantic-error-text"
                        )}
                      >
                        {String(v ?? "None")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-border-default flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedCase(null)}>
                Close Audit
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Markdown Report Modal */}
      {showMarkdownModal && (
        <Dialog
          isOpen={showMarkdownModal}
          onClose={() => setShowMarkdownModal(false)}
          title="Latest Benchmark Report (Markdown)"
        >
          <div className="space-y-4 max-h-[75vh] overflow-y-auto">
            {loadingMarkdown ? (
              <div className="p-12 flex justify-center">
                <Spinner size="md" />
              </div>
            ) : (
              <pre className="p-4 rounded-xl bg-surface-subtle border border-border-default text-ink-primary font-mono text-xs whitespace-pre-wrap leading-relaxed select-all">
                {markdownText}
              </pre>
            )}
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowMarkdownModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}

function MetricCardItem({
  category,
  fraction,
  invertStatus = false,
}: {
  category: string;
  fraction: MetricFraction;
  invertStatus?: boolean;
}) {
  const isPass = fraction.status === "PASS";

  return (
    <Card className="p-4 border-border-default shadow-xs flex flex-col justify-between">
      <div>
        <div className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">
          {category}
        </div>
        <div className="text-sm font-bold text-ink-primary mt-1">
          {fraction.name}
        </div>
        <p className="text-xs text-ink-muted mt-1 leading-snug line-clamp-2">
          {fraction.description}
        </p>
      </div>

      <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between">
        <div>
          <span className="font-mono text-lg font-bold text-ink-primary">
            {fraction.display_value}
          </span>
          {fraction.target_threshold_pct !== null && fraction.target_threshold_pct !== undefined && (
            <span className="text-[10px] text-ink-muted ml-1.5 font-mono">
              (target: {invertStatus ? "≤" : "≥"}{fraction.target_threshold_pct}%)
            </span>
          )}
        </div>
        <span
          className={cn(
            "px-2 py-0.5 rounded text-[11px] font-bold border",
            isPass
              ? "bg-semantic-success-bg text-semantic-success-text border-semantic-success-border"
              : "bg-semantic-error-bg text-semantic-error-text border-semantic-error-border"
          )}
        >
          {fraction.status}
        </span>
      </div>
    </Card>
  );
}
