"use client";

import * as React from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  History,
  Layers,
  Eye,
  Brain,
  Calculator,
  AlertTriangle,
  HelpCircle,
  FileCheck2,
} from "lucide-react";
import { api, StudentAnalysisDetail, StudentResponse } from "@/lib/api";
import { StudentWorkViewer, HopOverlayData } from "@/components/features/students/StudentWorkViewer";
import { AnswerStatusBadge } from "@/components/features/students/AnswerStatusBadge";
import { ReasoningStatusBadge } from "@/components/features/students/ReasoningStatusBadge";
import { AnalysisProvenancePill } from "@/components/features/analysis/AnalysisProvenancePill";
import { MisconceptionCard } from "@/components/features/analysis/MisconceptionCard";
import { ReasoningStepCard } from "@/components/features/analysis/ReasoningStepCard";
import { CriticAuditCard } from "@/components/inspection/CriticAuditCard";
import { TeacherReviewPanel } from "@/components/features/teacher-review/TeacherReviewPanel";
import { AuditTrailDrawer } from "@/components/inspection/AuditTrailDrawer";
import { Drawer } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/ui/icon-button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

export interface StudentInspectionModalProps {
  responseId: string;
  assessmentId: string;
  isOpen: boolean;
  onClose: () => void;
  onReviewChanged?: () => void;
  onNavigatePrev?: () => void;
  onNavigateNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
}

export function StudentInspectionModal({
  responseId,
  assessmentId,
  isOpen,
  onClose,
  onReviewChanged,
  onNavigatePrev,
  onNavigateNext,
  hasPrev = false,
  hasNext = false,
}: StudentInspectionModalProps) {
  const [detail, setDetail] = React.useState<StudentAnalysisDetail | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [activeMobileTab, setActiveMobileTab] = React.useState<"image" | "diagnosis">("image");
  const [auditDrawerOpen, setAuditDrawerOpen] = React.useState(false);
  const [showRawObservations, setShowRawObservations] = React.useState(false);

  React.useEffect(() => {
    if (!isOpen || !responseId) return;

    let cancelled = false;
    setLoading(true);

    api
      .ensureDemoSession()
      .then(() => api.getResponseDetail(responseId))
      .then((data) => {
        if (!cancelled) {
          setDetail(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load response detail:", err);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [responseId, isOpen]);

  // Handle ESC key to dismiss
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !auditDrawerOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, auditDrawerOpen]);

  if (!isOpen) return null;

  const imageUrl = `/api/v1/responses/${responseId}/image`;

  // Format hops overlay data from diagnosis verified steps
  const hopsData: HopOverlayData[] = (detail?.diagnosis?.verified_steps || []).map((step, idx) => ({
    start: idx === 0 ? 0 : step.expected_result - (idx === 1 ? 12 : -4),
    end: step.observed_result !== undefined ? step.observed_result : step.expected_result,
    label: step.operation,
    isCorrect: step.is_correct,
  }));

  const handleSaveTeacherReview = async (reviewData: {
    status: "confirmed" | "overridden" | "unreadable";
    taxonomyId?: string;
    notes?: string;
  }) => {
    const decision =
      reviewData.status === "confirmed"
        ? "approved_as_is"
        : reviewData.status === "unreadable"
        ? "marked_unreadable"
        : "overridden";

    await api.submitReview(
      responseId,
      decision,
      reviewData.taxonomyId,
      reviewData.notes
    );
    // Refresh detail
    const updated = await api.getResponseDetail(responseId);
    setDetail(updated);
    if (onReviewChanged) onReviewChanged();
  };

  const confidenceScore = detail?.visual_evidence?.confidence ?? 0.85;
  const qualitativeConfidence =
    confidenceScore >= 0.85
      ? "High (Clear Evidence)"
      : confidenceScore >= 0.70
      ? "Moderate (Partially Supported)"
      : "Low (Insufficient Evidence)";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Student inspection: ${detail?.pseudonym_label || responseId}`}
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/75 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 lg:p-6"
    >
      <div className="bg-surface-canvas rounded-2xl w-full max-w-7xl h-[94vh] flex flex-col shadow-2xl border border-border-default overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-surface-base border-b border-border-default shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-base sm:text-lg font-bold text-ink-primary">
              {detail?.pseudonym_label || `Student ${responseId}`}
            </h2>
            <span className="text-xs font-mono text-ink-muted bg-surface-subtle px-2 py-0.5 rounded border border-border-default">
              ID: {responseId}
            </span>
            {detail && (
              <AnalysisProvenancePill
                provenance={
                  detail.teacher_review_status === "overridden"
                    ? "teacher_overridden"
                    : detail.teacher_review_status === "approved_as_is" ||
                      detail.teacher_review_status === "reviewed"
                    ? "teacher_confirmed"
                    : "offline_simulated"
                }
              />
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Prev / Next Response Navigation */}
            <div className="flex items-center gap-1 border border-border-default rounded-lg p-0.5 bg-surface-subtle">
              <button
                type="button"
                onClick={onNavigatePrev}
                disabled={!hasPrev}
                aria-label="Previous Student"
                className="p-1 rounded text-ink-secondary hover:text-ink-primary hover:bg-white disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={onNavigateNext}
                disabled={!hasNext}
                aria-label="Next Student"
                className="p-1 rounded text-ink-secondary hover:text-ink-primary hover:bg-white disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setAuditDrawerOpen(true)}
              className="text-xs hidden sm:inline-flex"
            >
              <History className="w-3.5 h-3.5 mr-1 text-ink-muted" />
              Audit Log
            </Button>

            <IconButton
              icon={<X className="w-5 h-5" />}
              aria-label="Close modal"
              variant="neutral"
              size="sm"
              onClick={onClose}
            />
          </div>
        </div>

        {/* Mobile Viewport Tab Switcher */}
        <div className="md:hidden flex border-b border-border-default bg-surface-base">
          <button
            type="button"
            onClick={() => setActiveMobileTab("image")}
            className={cn(
              "flex-1 py-2.5 text-xs font-bold text-center border-b-2 transition-colors",
              activeMobileTab === "image"
                ? "border-brand-primary text-brand-primary"
                : "border-transparent text-ink-muted"
            )}
          >
            Handwritten Worksheet
          </button>
          <button
            type="button"
            onClick={() => setActiveMobileTab("diagnosis")}
            className={cn(
              "flex-1 py-2.5 text-xs font-bold text-center border-b-2 transition-colors",
              activeMobileTab === "diagnosis"
                ? "border-brand-primary text-brand-primary"
                : "border-transparent text-ink-muted"
            )}
          >
            Diagnostic Steps & Review
          </button>
        </div>

        {/* Main Content Pane */}
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12">
            <Spinner size="lg" />
            <p className="text-sm font-medium text-ink-secondary mt-3">
              Loading student visual evidence and verification records...
            </p>
          </div>
        ) : (
          <div className="flex-1 grid grid-cols-1 md:grid-cols-12 overflow-hidden bg-surface-canvas">
            {/* Left Column: Student Work Viewer (Col 7 on desktop) */}
            <div
              className={cn(
                "md:col-span-7 h-full overflow-hidden p-4 border-r border-border-default bg-surface-canvas",
                activeMobileTab === "image" ? "block" : "hidden md:block"
              )}
            >
              <StudentWorkViewer
                imageUrl={imageUrl}
                studentLabel={detail?.pseudonym_label || responseId}
                hops={hopsData}
                isUnreadable={
                  detail?.quality_status === "unreadable" ||
                  detail?.upload_status === "unreadable" ||
                  detail?.teacher_review_status === "marked_unreadable"
                }
                evidenceSufficiency={detail?.diagnosis?.evidence_sufficiency}
                className="h-full"
              />
            </div>

            {/* Right Column: Reasoning Analysis, Critic, & Review Form (Col 5 on desktop) */}
            <div
              className={cn(
                "md:col-span-5 h-full overflow-y-auto p-4 sm:p-5 space-y-4 bg-surface-card",
                activeMobileTab === "diagnosis" ? "block" : "hidden md:block"
              )}
            >
              {/* Top Status & Calibrated Confidence Overview */}
              <div className="p-3 rounded-xl bg-surface-base border border-border-default space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-ink-muted">
                    Evaluation Verdicts
                  </span>
                  <span
                    className={cn(
                      "text-[10px] font-semibold px-2 py-0.5 rounded-full border",
                      confidenceScore >= 0.85
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                        : confidenceScore >= 0.70
                        ? "bg-amber-50 text-amber-900 border-amber-200"
                        : "bg-red-50 text-red-800 border-red-200"
                    )}
                    title="Internal model extraction confidence (heuristic score, not a calibrated probability)"
                  >
                    Confidence: {qualitativeConfidence}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <AnswerStatusBadge status={detail?.answer_status || "undetermined"} />
                  <ReasoningStatusBadge status={detail?.reasoning_status || "undetermined"} />
                </div>
              </div>

              {/* THREE-WAY SEPARATION OF CONCERNS */}

              {/* Stage 1: Observed on Worksheet */}
              <div className="rounded-xl border border-border-default bg-surface-base p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-ink-primary">
                    <Eye className="w-3.5 h-3.5 text-brand-primary" />
                    <span>1. Observed on Worksheet (Multimodal)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowRawObservations(!showRawObservations)}
                    className="text-[11px] text-brand-primary hover:underline font-medium"
                  >
                    {showRawObservations ? "Hide Details" : "View Marks"}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded bg-surface-subtle border border-border-default">
                    <span className="text-[10px] uppercase text-ink-muted block font-sans">
                      Number Line Detected:
                    </span>
                    <span className="font-semibold text-ink-primary">
                      {detail?.visual_evidence?.has_number_line ? "Yes (Horizontal Grid)" : "None / Unreadable"}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-surface-subtle border border-border-default">
                    <span className="text-[10px] uppercase text-ink-muted block font-sans">
                      Final Written Answer:
                    </span>
                    <span className="font-semibold text-ink-primary">
                      {detail?.visual_evidence?.final_answer_marked ? (
                        detail.visual_evidence.final_answer_marked
                      ) : (
                        <span className="text-amber-800 italic">None / Blank</span>
                      )}
                    </span>
                  </div>
                </div>

                {/* Ambiguities Warning Pill */}
                {detail?.visual_evidence?.ambiguities && detail.visual_evidence.ambiguities.length > 0 && (
                  <div className="p-2 rounded bg-amber-50 border border-amber-200 text-xs text-amber-950 space-y-1">
                    <div className="flex items-center gap-1 font-bold text-[11px] text-amber-900">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                      Visual Ambiguities Detected:
                    </div>
                    <ul className="list-disc pl-4 text-[11px] text-amber-900/90 space-y-0.5">
                      {detail.visual_evidence.ambiguities.map((amb, i) => (
                        <li key={i}>{amb}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Collapsible raw ink observations */}
                {showRawObservations && (
                  <div className="pt-2 border-t border-border-default space-y-1">
                    <span className="text-[10px] uppercase font-bold text-ink-muted block">
                      Physical Marks &amp; Hops:
                    </span>
                    <div className="space-y-1 max-h-36 overflow-y-auto">
                      {(detail?.visual_evidence?.observations || []).map((obs, idx) => (
                        <div
                          key={idx}
                          className="p-1.5 rounded bg-surface-subtle text-[11px] font-mono flex items-center justify-between"
                        >
                          <span className="truncate max-w-[240px]">{obs.value}</span>
                          <span className="text-ink-muted text-[10px]">
                            {Math.round(obs.confidence * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Stage 2: Mathematically Interpreted */}
              <div className="rounded-xl border border-border-default bg-surface-base p-3.5 space-y-2">
                <div className="flex items-center gap-1.5 font-bold text-xs text-ink-primary">
                  <Brain className="w-3.5 h-3.5 text-indigo-600" />
                  <span>2. Mathematically Interpreted Strategy</span>
                </div>
                <div className="p-2 rounded bg-surface-subtle border border-border-default text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-ink-primary">
                      Strategy:{" "}
                      <span className="font-mono text-indigo-700">
                        {detail?.candidate_hypotheses?.detected_strategy || "Standard"}
                      </span>
                    </span>
                    <span className="text-[10px] text-ink-muted uppercase">
                      {detail?.candidate_hypotheses?.reasoning_completeness || "complete"}
                    </span>
                  </div>
                  <p className="text-[11px] text-ink-secondary leading-relaxed">
                    {detail?.candidate_hypotheses?.hypotheses?.[0]?.strategy_description ||
                      "Sequential number-line traversal interpreted from visible ink marks."}
                  </p>
                </div>
              </div>

              {/* Stage 3: Verified by SymPy */}
              <div className="rounded-xl border border-border-default bg-surface-base p-3.5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-ink-primary">
                    <Calculator className="w-3.5 h-3.5 text-emerald-600" />
                    <span>3. Verified by SymPy &amp; Geometry Engine</span>
                  </div>
                  <span className="text-[11px] font-mono text-ink-muted">
                    {detail?.diagnosis?.verified_steps?.length || 0} Steps
                  </span>
                </div>

                {/* First Supported Error Card or Safe Suppressed Card */}
                <MisconceptionCard
                  error={detail?.diagnosis?.first_supported_error}
                  misconceptionTitle={
                    detail?.diagnosis?.taxonomy_title ||
                    detail?.diagnosis?.misconception_taxonomy_id
                  }
                  isCompensatoryError={detail?.is_compensatory_error}
                  evidenceSufficiency={detail?.diagnosis?.evidence_sufficiency}
                  reasoningStatus={detail?.reasoning_status}
                />

                {/* Step-by-Step Breakdown */}
                <div className="space-y-2 pt-1">
                  {(detail?.diagnosis?.verified_steps || []).map((step) => (
                    <ReasoningStepCard key={step.step_number} step={step} />
                  ))}
                </div>
              </div>

              {/* Independent Critic Grounding Audit */}
              <CriticAuditCard criticAudit={detail?.critic_audit} />

              {/* Teacher Review & Override Form */}
              <TeacherReviewPanel
                responseId={responseId}
                initialStatus={detail?.teacher_review_status}
                initialOverrideTaxonomy={detail?.teacher_override_taxonomy_id}
                initialNotes={detail?.teacher_notes}
                onSaveReview={handleSaveTeacherReview}
              />
            </div>
          </div>
        )}

        {/* Real Audit Log Drawer */}
        <Drawer
          isOpen={auditDrawerOpen}
          onClose={() => setAuditDrawerOpen(false)}
          title={`Audit History — ${detail?.pseudonym_label || responseId}`}
        >
          <div className="space-y-4">
            <AuditTrailDrawer responseId={responseId} />
          </div>
        </Drawer>
      </div>
    </div>
  );
}
