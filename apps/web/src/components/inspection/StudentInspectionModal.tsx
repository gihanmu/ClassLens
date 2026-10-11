"use client";

import * as React from "react";
import { X, ChevronLeft, ChevronRight, History, Layers, CheckCircle2 } from "lucide-react";
import { api, StudentAnalysisDetail, StudentResponse } from "@/lib/api";
import { StudentWorkViewer, HopOverlayData } from "@/components/features/students/StudentWorkViewer";
import { AnswerStatusBadge } from "@/components/features/students/AnswerStatusBadge";
import { ReasoningStatusBadge } from "@/components/features/students/ReasoningStatusBadge";
import { AnalysisProvenancePill } from "@/components/features/analysis/AnalysisProvenancePill";
import { MisconceptionCard } from "@/components/features/analysis/MisconceptionCard";
import { ReasoningStepCard } from "@/components/features/analysis/ReasoningStepCard";
import { TeacherReviewPanel } from "@/components/features/teacher-review/TeacherReviewPanel";
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
    start: idx === 0 ? 0 : (step.expected_result - (idx === 1 ? 12 : -4)),
    end: step.observed_result !== undefined ? step.observed_result : step.expected_result,
    label: step.operation,
    isCorrect: step.is_correct,
  }));

  const handleSaveTeacherReview = async (reviewData: {
    status: "confirmed" | "overridden";
    taxonomyId?: string;
    notes?: string;
  }) => {
    const decision = reviewData.status === "confirmed" ? "CONFIRM" : "OVERRIDE";
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
                    : detail.teacher_review_status === "reviewed"
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
                className="h-full"
              />
            </div>

            {/* Right Column: Step Breakdown, Misconception, and Review Form (Col 5 on desktop) */}
            <div
              className={cn(
                "md:col-span-5 h-full overflow-y-auto p-4 sm:p-5 space-y-4 bg-surface-card",
                activeMobileTab === "diagnosis" ? "block" : "hidden md:block"
              )}
            >
              {/* Badges Status Overview */}
              <div className="flex flex-wrap items-center gap-2 pb-1">
                <AnswerStatusBadge status={detail?.answer_status || "unknown"} />
                <ReasoningStatusBadge status={detail?.reasoning_status || "unknown"} />
              </div>

              {/* First Supported Error Card */}
              <MisconceptionCard
                error={detail?.diagnosis?.first_supported_error}
                misconceptionTitle={detail?.diagnosis?.taxonomy_title || detail?.diagnosis?.misconception_taxonomy_id}
                isCompensatoryError={detail?.is_compensatory_error}
              />

              {/* Step-by-Step Breakdown */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-ink-secondary">
                    Mathematical Step Breakdown
                  </h4>
                  <span className="text-[11px] font-mono text-ink-muted">
                    {detail?.diagnosis?.verified_steps?.length || 0} Steps Verified
                  </span>
                </div>

                <div className="space-y-2">
                  {(detail?.diagnosis?.verified_steps || []).map((step) => (
                    <ReasoningStepCard key={step.step_number} step={step} />
                  ))}
                </div>
              </div>

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

        {/* Audit Log Drawer */}
        <Drawer
          isOpen={auditDrawerOpen}
          onClose={() => setAuditDrawerOpen(false)}
          title={`Audit History — ${detail?.pseudonym_label || responseId}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-surface-subtle border border-border-default">
              <div className="flex items-center justify-between font-semibold text-ink-primary">
                <span>Multi-Agent Ingestion</span>
                <span className="font-mono text-[11px] text-ink-muted">Complete</span>
              </div>
              <p className="text-ink-secondary mt-1">
                Visual evidence extracted, candidate hypothesis evaluated against SymPy ground truth.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border-default">
              <div className="flex items-center justify-between font-semibold text-ink-primary">
                <span>Critic Agent Review</span>
                <span className="font-mono text-[11px] text-ink-muted">
                  {detail?.critic_audit?.approved ? "Approved" : "Re-evaluated"}
                </span>
              </div>
              <p className="text-ink-secondary mt-1">
                {detail?.critic_audit?.requires_teacher_review
                  ? `Flagged for teacher review: ${detail.critic_audit.teacher_review_reason || "Ambiguous hop marks"}`
                  : "All observations ground in clear visual evidence without discrepancies."}
              </p>
            </div>

            {detail?.teacher_review_status && detail.teacher_review_status !== "unreviewed" && (
              <div className="p-3 rounded-lg bg-accent-mint/30 border border-emerald-300">
                <div className="flex items-center justify-between font-semibold text-emerald-950">
                  <span>Educator Override</span>
                  <span className="font-mono text-[11px] text-emerald-800">Confirmed</span>
                </div>
                <p className="text-emerald-900 mt-1">
                  Status: <strong>{detail.teacher_review_status}</strong>
                  {detail.teacher_notes && <><br />Notes: <em>{detail.teacher_notes}</em></>}
                </p>
              </div>
            )}
          </div>
        </Drawer>
      </div>
    </div>
  );
}
