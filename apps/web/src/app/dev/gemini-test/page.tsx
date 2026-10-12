"use client";

import * as React from "react";
import {
  FlaskConical,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Clock,
  Coins,
  Cpu,
  Layers,
  FileText,
  RefreshCw,
  Eye,
  ChevronDown,
  ChevronUp,
  Terminal,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { AppShell } from "@/components/shared/app-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { AnswerStatusBadge } from "@/components/features/students/AnswerStatusBadge";
import { ReasoningStatusBadge } from "@/components/features/students/ReasoningStatusBadge";
import { AnalysisProvenancePill } from "@/components/features/analysis/AnalysisProvenancePill";
import { ReasoningStepCard } from "@/components/features/analysis/ReasoningStepCard";
import { MisconceptionCard } from "@/components/features/analysis/MisconceptionCard";
import { api, DevStatusResponse, SyntheticAnalysisResponse } from "@/lib/api";

export default function GeminiTestLabPage() {
  const [devStatus, setDevStatus] = React.useState<DevStatusResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = React.useState(true);
  const [statusError, setStatusError] = React.useState<string | null>(null);

  const [selectedFixtureId, setSelectedFixtureId] = React.useState<string>("case_01_canonical_correct");
  const [ruleExpr, setRuleExpr] = React.useState<string>("-6 + 12 - 4");
  const [targetValue, setTargetValue] = React.useState<number>(2.0);

  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [analysisResult, setAnalysisResult] = React.useState<SyntheticAnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = React.useState<string | null>(null);

  const [showRawJson, setShowRawJson] = React.useState(false);

  // Load status on mount
  const fetchStatus = React.useCallback(async () => {
    setLoadingStatus(true);
    setStatusError(null);
    try {
      const data = await api.getDevStatus();
      setDevStatus(data);
    } catch (err: any) {
      setStatusError(err.message || "Failed to connect to backend development endpoint.");
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  React.useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Handle analysis
  const handleAnalyze = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await api.analyzeSynthetic(selectedFixtureId, ruleExpr, targetValue);
      setAnalysisResult(res);
      // Refresh status to update remaining calls
      await fetchStatus();
    } catch (err: any) {
      setAnalysisError(err.message || "Analysis request failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedFixture = devStatus?.authorized_fixtures.find((f) => f.id === selectedFixtureId);
  const isBudgetExhausted = devStatus?.is_live_mode && devStatus?.calls_remaining <= 0;

  return (
    <AppShell currentTab="gemini-test" assessmentTitle="Gemini Test Lab (Gate 4A.1)">
      <div className="space-y-6 max-w-6xl mx-auto pb-16">
        {/* Lab Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-default pb-5">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-xl bg-brand-primary-soft text-brand-primary flex items-center justify-center shrink-0 border border-brand-primary/20 shadow-xs">
              <FlaskConical className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-ink-primary tracking-tight">Gemini Test Lab</h1>
                <Badge variant="accent" size="sm">Gate 4A.1</Badge>
                <Badge variant="outline" size="sm">Dev Only</Badge>
              </div>
              <p className="text-sm text-ink-secondary mt-1">
                Local-development interactive test harness for validating multimodal visual extraction and deterministic mathematical verification.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loadingStatus ? "animate-spin" : ""}`} />}
              onClick={fetchStatus}
              disabled={loadingStatus || isAnalyzing}
            >
              Refresh Status
            </Button>
          </div>
        </div>

        {/* Status Error Alert if backend unreachable */}
        {statusError && (
          <Alert variant="error" title="Backend Connection Unavailable">
            <p className="mb-2">{statusError}</p>
            <p className="text-xs text-ink-muted">
              Ensure the FastAPI backend is running locally on port 8000:
              <code className="ml-1 px-1.5 py-0.5 bg-surface-muted rounded font-mono">
                .venv/bin/uvicorn services.api.main:app --port 8000
              </code>
            </p>
          </Alert>
        )}

        {/* Runtime Environment & Budget Telemetry Bar */}
        {devStatus && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Execution Mode Card */}
            <Card className="p-4 bg-surface-base border-border-default">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Execution Mode</span>
                {devStatus.is_live_mode ? (
                  <Badge variant="accent" size="sm">LIVE INFERENCE</Badge>
                ) : (
                  <Badge variant="mint" size="sm">MOCK ENGINE</Badge>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    devStatus.is_live_mode ? "bg-accent-coral animate-pulse" : "bg-emerald-500"
                  }`}
                />
                <span className="text-sm font-bold text-ink-primary">
                  {devStatus.is_live_mode ? "Google Vertex AI" : "Deterministic Offline Mock"}
                </span>
              </div>
              <p className="text-[11px] text-ink-muted mt-1">
                {devStatus.is_live_mode
                  ? "Real Gemini 3.8 Flash multimodal vision"
                  : "Safe offline development mode (zero cloud cost)"}
              </p>
            </Card>

            {/* Configured Model Card */}
            <Card className="p-4 bg-surface-base border-border-default">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Gemini Model</span>
                <Cpu className="w-3.5 h-3.5 text-ink-muted" />
              </div>
              <div className="text-sm font-bold text-ink-primary font-mono truncate">
                {devStatus.model}
              </div>
              <p className="text-[11px] text-ink-muted mt-1 truncate">
                Endpoint: {devStatus.location} (Vertex AI: {devStatus.use_vertexai ? "Enabled" : "Off"})
              </p>
            </Card>

            {/* Cloud Project Card */}
            <Card className="p-4 bg-surface-base border-border-default">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Google Cloud Project</span>
                <Terminal className="w-3.5 h-3.5 text-ink-muted" />
              </div>
              <div className="text-sm font-bold text-ink-primary font-mono truncate">
                {devStatus.project || "None (Mock)"}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">
                Environment: <span className="font-semibold">{devStatus.environment}</span>
              </p>
            </Card>

            {/* Call Budget Ceiling Card */}
            <Card
              className={`p-4 border ${
                isBudgetExhausted
                  ? "bg-red-50/40 border-red-200"
                  : devStatus.is_live_mode
                  ? "bg-amber-50/30 border-amber-200"
                  : "bg-surface-base border-border-default"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">Call Budget</span>
                <Coins className="w-3.5 h-3.5 text-ink-muted" />
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-lg font-bold text-ink-primary font-mono">
                  {devStatus.calls_used} / {devStatus.max_calls}
                </span>
                <span className="text-xs text-ink-secondary">
                  ({devStatus.calls_remaining} remaining)
                </span>
              </div>
              <div className="w-full bg-surface-muted rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    isBudgetExhausted
                      ? "bg-semantic-error"
                      : devStatus.is_live_mode
                      ? "bg-brand-coral"
                      : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.min(100, (devStatus.calls_used / devStatus.max_calls) * 100)}%`,
                  }}
                />
              </div>
            </Card>
          </div>
        )}

        {/* Live Mode Switching Instructions Alert */}
        {devStatus && !devStatus.is_live_mode && (
          <Alert variant="info" title="Currently Operating in Safe Mock Mode">
            <p className="mb-2">
              All analyses below execute using deterministic offline mock fixtures without making live Google Cloud calls.
            </p>
            <div className="text-xs bg-surface-base p-2.5 rounded border border-border-default font-mono space-y-1">
              <span className="text-ink-muted block font-sans font-semibold">To switch backend to Live Gemini Inference:</span>
              <code>CLASSLENS_AI_MODE=live CLASSLENS_LIVE_INFERENCE_ENABLED=true .venv/bin/uvicorn services.api.main:app --port 8000</code>
            </div>
          </Alert>
        )}

        {/* Live Mode Warning Alert */}
        {devStatus?.is_live_mode && (
          <Alert variant="warning" title="Live Gemini Inference Active">
            <p>
              Inference is connecting to Google Vertex AI project <strong>{devStatus.project}</strong> using model <strong>{devStatus.model}</strong>.
              Calls are bounded strictly to the session ceiling of <strong>{devStatus.max_calls}</strong> calls.
            </p>
          </Alert>
        )}

        {/* Budget Exhausted Alert */}
        {isBudgetExhausted && (
          <Alert variant="error" title="Gate 4A Live Call Budget Ceiling Reached">
            <p>
              All {devStatus?.max_calls} authorized live test calls have been consumed for this backend session.
              To reset the call budget, restart the backend server.
            </p>
          </Alert>
        )}

        {/* Step 1: Synthetic Worksheet Selection */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-ink-primary">1. Select Authorized Synthetic Worksheet</h2>
              <p className="text-xs text-ink-secondary">
                Strict provenance guard: Only these three verified synthetic benchmarks can be analyzed.
              </p>
            </div>
            <Badge variant="outline" size="sm">
              3 Fixtures Available
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {devStatus?.authorized_fixtures.map((fixture) => {
              const isSelected = fixture.id === selectedFixtureId;
              return (
                <button
                  key={fixture.id}
                  type="button"
                  onClick={() => {
                    setSelectedFixtureId(fixture.id);
                    setAnalysisResult(null);
                    setAnalysisError(null);
                  }}
                  className={`text-left p-4 rounded-xl border transition-all duration-150 flex flex-col justify-between ${
                    isSelected
                      ? "bg-brand-primary-soft/30 border-brand-primary ring-2 ring-brand-primary/20 shadow-xs"
                      : "bg-surface-card border-border-default hover:border-brand-primary/40 hover:bg-surface-subtle"
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-ink-primary line-clamp-1">{fixture.name}</span>
                      {isSelected ? (
                        <CheckCircle2 className="w-4 h-4 text-brand-primary shrink-0" />
                      ) : (
                        <span className="w-4 h-4 rounded-full border border-border-default shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-ink-secondary leading-relaxed line-clamp-3">
                      {fixture.description}
                    </p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-border-default/60 flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono text-ink-muted truncate">
                      Expected: {fixture.expected_reasoning}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        fixture.category === "canonical_correct"
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : fixture.category === "procedural_error"
                          ? "bg-red-50 text-red-800 border border-red-200"
                          : "bg-amber-50 text-amber-800 border border-amber-200"
                      }`}
                    >
                      {fixture.category}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Step 2: Worksheet Preview & Analysis Execution Panel */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Worksheet Image Preview (Left: 7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-ink-primary flex items-center gap-2">
                <Eye className="w-4 h-4 text-ink-muted" />
                Worksheet Preview
              </h2>
              <span className="text-[11px] font-mono text-ink-muted">
                {selectedFixture?.filename}
              </span>
            </div>

            <Card className="overflow-hidden bg-surface-subtle/50 border-border-default p-2 flex flex-col items-center">
              <div className="relative w-full rounded-lg overflow-hidden bg-white border border-border-default flex items-center justify-center min-h-[280px]">
                {selectedFixture ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={api.getSyntheticFixtureImageUrl(selectedFixture.id)}
                    alt={`Preview of synthetic worksheet: ${selectedFixture.name}`}
                    className="w-full h-auto max-h-[380px] object-contain select-none"
                  />
                ) : (
                  <div className="p-8 text-center text-ink-muted">
                    <FileText className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-xs">No worksheet selected</p>
                  </div>
                )}
              </div>

              <div className="w-full p-2.5 flex items-center justify-between text-xs text-ink-muted border-t border-border-subtle mt-2">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Provenance Guard Verified SHA-256</span>
                </div>
                <span className="font-mono text-[11px]">Authorized Synthetic Benchmark</span>
              </div>
            </Card>
          </div>

          {/* Action Trigger Card (Right: 5 cols) */}
          <div className="lg:col-span-5 space-y-3">
            <h2 className="text-base font-bold text-ink-primary">2. Execute Analysis</h2>

            <Card className="p-5 bg-surface-base border-border-default space-y-4">
              <div className="space-y-3">
                <div>
                  <label htmlFor="rule-expr" className="block text-xs font-semibold text-ink-primary mb-1">
                    Mathematical Rule Expression
                  </label>
                  <input
                    id="rule-expr"
                    type="text"
                    value={ruleExpr}
                    onChange={(e) => setRuleExpr(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border-default bg-surface-subtle text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-primary"
                    placeholder="-6 + 12 - 4"
                  />
                </div>

                <div>
                  <label htmlFor="target-val" className="block text-xs font-semibold text-ink-primary mb-1">
                    Target Verified Value
                  </label>
                  <input
                    id="target-val"
                    type="number"
                    step="any"
                    value={targetValue}
                    onChange={(e) => setTargetValue(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border-default bg-surface-subtle text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-primary"
                    placeholder="2.0"
                  />
                </div>
              </div>

              <div className="pt-2 border-t border-border-default/60 space-y-3">
                <Button
                  variant={devStatus?.is_live_mode ? "coral" : "primary"}
                  size="lg"
                  className="w-full justify-center"
                  onClick={handleAnalyze}
                  isLoading={isAnalyzing}
                  disabled={isBudgetExhausted || isAnalyzing}
                  leftIcon={<Sparkles className="w-4 h-4" />}
                >
                  {isAnalyzing
                    ? "Executing Multi-Agent Pipeline..."
                    : devStatus?.is_live_mode
                    ? "Analyze with Gemini (Live 3.8 Flash)"
                    : "Analyze Worksheet (Mock Engine)"}
                </Button>

                <p className="text-[11px] text-ink-muted text-center leading-relaxed">
                  {devStatus?.is_live_mode
                    ? "Manual button click only. Will consume 1 of remaining live call allowance."
                    : "Deterministic offline execution through existing MultiAgentPipeline."}
                </p>
              </div>

              {analysisError && (
                <Alert variant="error" title="Analysis Error">
                  <p className="text-xs break-words">{analysisError}</p>
                </Alert>
              )}
            </Card>
          </div>
        </section>

        {/* Step 3: Structured Results View (Decoupled Visual vs Math) */}
        {analysisResult && (
          <section className="space-y-5 pt-4 border-t border-border-default">
            {/* Results Header & Telemetry */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-surface-base p-4 rounded-xl border border-border-default shadow-xs">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-primary-soft text-brand-primary flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-ink-primary">Analysis Completed</h3>
                    <AnalysisProvenancePill
                      provenance={analysisResult.is_mock ? "offline_simulated" : "ai_proposed"}
                    />
                    <Badge variant="outline" size="sm" className="font-mono">
                      {analysisResult.model_version}
                    </Badge>
                  </div>
                  <p className="text-xs text-ink-secondary mt-0.5">
                    Analyzed fixture: <span className="font-mono font-medium">{analysisResult.fixture_id}</span>
                  </p>
                </div>
              </div>

              {/* Telemetry Metrics */}
              <div className="flex items-center gap-4 text-xs font-mono text-ink-secondary divide-x divide-border-default self-start sm:self-center">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-ink-muted" />
                  <span>{analysisResult.execution_latency_ms} ms</span>
                </div>
                <div className="pl-4 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-ink-muted" />
                  <span>{analysisResult.tokens_consumed} tokens</span>
                </div>
                {analysisResult.cost_estimate_usd !== null && analysisResult.cost_estimate_usd !== undefined && (
                  <div className="pl-4 flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-ink-muted" />
                    <span>${analysisResult.cost_estimate_usd.toFixed(6)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Core Decoupled Panels: Visual Evidence vs Mathematical Verification */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* LEFT COLUMN: Visual Evidence Observations (Gemini Multimodal Transcription) */}
              <Card className="p-5 bg-surface-base border-border-default space-y-4">
                <div className="flex items-center justify-between border-b border-border-default pb-3">
                  <div>
                    <h3 className="text-base font-bold text-ink-primary flex items-center gap-2">
                      <Eye className="w-4 h-4 text-brand-primary" />
                      Visual Evidence Observations
                    </h3>
                    <p className="text-xs text-ink-secondary mt-0.5">
                      Perceptual physical marks transcribed from image (Gemini Vision)
                    </p>
                  </div>
                  <Badge variant="primary" size="sm">Agent 1</Badge>
                </div>

                {/* Quality & Detection Overview */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle">
                    <span className="text-[10px] uppercase font-semibold text-ink-muted block mb-1">
                      Quality Status
                    </span>
                    <span className="font-bold text-ink-primary capitalize">
                      {analysisResult.analysis.visual_evidence?.quality_status || "Unknown"}
                    </span>
                  </div>
                  <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle">
                    <span className="text-[10px] uppercase font-semibold text-ink-muted block mb-1">
                      Visual Confidence
                    </span>
                    <span className="font-bold text-ink-primary font-mono">
                      {((analysisResult.analysis.visual_evidence?.confidence || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Stated Marks Summary */}
                <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-ink-secondary">Number Line Detected:</span>
                    <span className="font-semibold text-ink-primary">
                      {analysisResult.analysis.visual_evidence?.has_number_line ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-ink-secondary">Final Answer Marked:</span>
                    <span className="font-mono font-bold text-ink-primary">
                      {analysisResult.analysis.visual_evidence?.final_answer_marked ?? "None / Unmarked"}
                    </span>
                  </div>
                </div>

                {/* Physical Marks Transcription List */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-ink-primary uppercase tracking-wider text-ink-muted">
                    Transcribed Physical Marks ({analysisResult.analysis.visual_evidence?.observations?.length || 0})
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {analysisResult.analysis.visual_evidence?.observations?.map((obs: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg border border-border-default bg-surface-card text-xs flex items-start justify-between gap-2"
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-ink-primary capitalize font-mono text-[11px] bg-surface-muted px-1.5 py-0.5 rounded">
                              {obs.kind}
                            </span>
                            <span className="font-mono text-ink-primary font-bold">
                              {obs.value}
                            </span>
                          </div>
                          {(obs.start_pos !== null && obs.start_pos !== undefined) && (
                            <p className="text-[11px] font-mono text-ink-muted">
                              Jump: {obs.start_pos} → {obs.end_pos} ({obs.direction})
                              {obs.stated_magnitude !== null && ` [label: ${obs.stated_magnitude}]`}
                            </p>
                          )}
                        </div>
                        <span className="text-[10px] font-mono text-ink-muted shrink-0">
                          {(obs.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Ambiguities & Review Flags */}
                {analysisResult.analysis.visual_evidence?.ambiguities?.length > 0 && (
                  <div className="p-3 rounded-lg bg-amber-50/50 border border-amber-200 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-amber-900 font-bold">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      <span>Visual Ambiguities Identified</span>
                    </div>
                    <ul className="list-disc list-inside text-amber-800 text-[11px] space-y-0.5 pl-1">
                      {analysisResult.analysis.visual_evidence.ambiguities.map((amb: string, i: number) => (
                        <li key={i}>{amb}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>

              {/* RIGHT COLUMN: Deterministic Mathematical Verification (SymPy & Diagnostics) */}
              <Card className="p-5 bg-surface-base border-border-default space-y-4">
                <div className="flex items-center justify-between border-b border-border-default pb-3">
                  <div>
                    <h3 className="text-base font-bold text-ink-primary flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      Mathematical Verification
                    </h3>
                    <p className="text-xs text-ink-secondary mt-0.5">
                      Deterministic SymPy verification & error classification
                    </p>
                  </div>
                  <Badge variant="mint" size="sm">Agents 2 & 3</Badge>
                </div>

                {/* Diagnostic Badges Summary */}
                <div className="flex items-center gap-3">
                  <AnswerStatusBadge status={analysisResult.analysis.answer_status} />
                  <ReasoningStatusBadge status={analysisResult.analysis.reasoning_status} />
                  {analysisResult.analysis.is_compensatory_error && (
                    <Badge variant="warm" size="sm">Compensatory Error</Badge>
                  )}
                </div>

                {/* Detected Strategy */}
                <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-semibold text-ink-muted">Detected Strategy</span>
                    <span className="text-[10px] font-mono text-ink-muted capitalize">
                      Completeness: {analysisResult.analysis.candidate_hypotheses?.reasoning_completeness}
                    </span>
                  </div>
                  <p className="font-semibold text-ink-primary">
                    {analysisResult.analysis.candidate_hypotheses?.detected_strategy || "Standard sequential number line"}
                  </p>
                </div>

                {/* Verified Steps List */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-ink-primary uppercase tracking-wider text-ink-muted">
                    SymPy Verified Steps ({analysisResult.analysis.diagnosis?.verified_steps?.length || 0})
                  </h4>
                  <div className="space-y-2">
                    {analysisResult.analysis.diagnosis?.verified_steps?.map((step: any, idx: number) => (
                      <ReasoningStepCard key={idx} step={step} />
                    ))}
                  </div>
                </div>

                {/* Misconception / Error Diagnosis */}
                <div className="space-y-2 pt-2">
                  <h4 className="text-xs font-bold text-ink-primary uppercase tracking-wider text-ink-muted">
                    Diagnosed Misconception
                  </h4>
                  <MisconceptionCard
                    error={analysisResult.analysis.diagnosis?.first_supported_error}
                    misconceptionTitle={analysisResult.analysis.diagnosis?.misconception_taxonomy_id}
                    isCompensatoryError={analysisResult.analysis.is_compensatory_error}
                  />
                </div>
              </Card>
            </div>

            {/* FULL-WIDTH BOTTOM PANEL: Independent Critic Audit & Teacher Review */}
            <Card className="p-5 bg-surface-base border-border-default space-y-4">
              <div className="flex items-center justify-between border-b border-border-default pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center shrink-0 border border-purple-200">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-ink-primary">
                      Agent 4: Independent Critic Audit & Teacher Escalation
                    </h3>
                    <p className="text-xs text-ink-secondary">
                      Adversarial grounding validation and human-in-the-loop review recommendations
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {analysisResult.analysis.critic_audit?.approved ? (
                    <Badge variant="mint" size="sm">Audit Passed</Badge>
                  ) : (
                    <Badge variant="accent" size="sm">Discrepancy Flagged</Badge>
                  )}
                </div>
              </div>

              {/* Critic Audit Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle flex items-center justify-between">
                  <span className="text-ink-secondary">Evidence Grounded:</span>
                  <span className="font-bold">
                    {analysisResult.analysis.critic_audit?.evidence_grounded ? (
                      <span className="text-emerald-700">Verified</span>
                    ) : (
                      <span className="text-red-700">Ungrounded</span>
                    )}
                  </span>
                </div>
                <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle flex items-center justify-between">
                  <span className="text-ink-secondary">Contradiction Detected:</span>
                  <span className="font-bold">
                    {analysisResult.analysis.critic_audit?.contradiction_detected ? (
                      <span className="text-red-700">Yes</span>
                    ) : (
                      <span className="text-emerald-700">None</span>
                    )}
                  </span>
                </div>
                <div className="p-3 bg-surface-subtle rounded-lg border border-border-subtle flex items-center justify-between">
                  <span className="text-ink-secondary">Critic Confidence:</span>
                  <span className="font-mono font-bold text-ink-primary">
                    {((analysisResult.analysis.critic_audit?.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Teacher Review Recommendation */}
              {analysisResult.analysis.needs_teacher_review ? (
                <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-300 text-amber-950 space-y-1">
                  <div className="flex items-center gap-2 font-bold text-sm text-amber-900">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Teacher Review Escalation Required</span>
                  </div>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    Reason: {analysisResult.analysis.teacher_review_reason || "Visual ambiguities or ungrounded reasoning detected."}
                  </p>
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200 text-emerald-950 flex items-center gap-2 text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    No teacher escalation required. The analysis is deterministically verified with high visual confidence.
                  </span>
                </div>
              )}

              {/* Raw JSON Debug Inspector */}
              <div className="pt-2 border-t border-border-default/60">
                <button
                  type="button"
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-ink-secondary hover:text-ink-primary transition-colors"
                >
                  {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showRawJson ? "Hide Raw Response Payload" : "Inspect Raw JSON Response Payload"}</span>
                </button>

                {showRawJson && (
                  <div className="mt-3 bg-surface-canvas p-4 rounded-xl border border-border-default overflow-x-auto max-h-96">
                    <pre className="text-[11px] font-mono text-ink-secondary leading-relaxed">
                      {JSON.stringify(analysisResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </Card>
          </section>
        )}
      </div>
    </AppShell>
  );
}
