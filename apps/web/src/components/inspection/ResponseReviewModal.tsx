"use client";

import React, { useEffect, useState } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { api, StudentAnalysisDetail } from "@/lib/api";
import { ImageViewerCanvas } from "./ImageViewerCanvas";
import { DiagnosticSummaryCard } from "./DiagnosticSummaryCard";
import { ErrorLocalizationCard } from "./ErrorLocalizationCard";
import { StepBreakdownList } from "./StepBreakdownList";
import { TeacherReviewForm } from "./TeacherReviewForm";
import { AuditTrailDrawer } from "./AuditTrailDrawer";

interface ResponseReviewModalProps {
  responseId: string;
  isOpen: boolean;
  onClose: () => void;
  onReviewChanged?: () => void;
  onNavigatePrev?: () => void;
  onNavigateNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
}

export function ResponseReviewModal({
  responseId,
  isOpen,
  onClose,
  onReviewChanged,
  onNavigatePrev,
  onNavigateNext,
  hasPrev = false,
  hasNext = false,
}: ResponseReviewModalProps) {
  const [detail, setDetail] = useState<StudentAnalysisDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeMobileTab, setActiveMobileTab] = useState<"image" | "diagnosis">(() => {
    if (typeof window !== "undefined") {
      const pane = new URLSearchParams(window.location.search).get("pane");
      if (pane === "diagnosis") return "diagnosis";
    }
    return "image";
  });

  useEffect(() => {
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
  const modalRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
        return;
      }

      if (e.key === "Tab" && isOpen && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            last.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === last) {
            first.focus();
            e.preventDefault();
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-modal-title"
      className="fixed inset-0 z-50 overflow-hidden bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 lg:p-6"
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        className="bg-slate-100 rounded-2xl w-full max-w-[1240px] max-h-[92dvh] h-[92dvh] sm:max-h-[90dvh] sm:h-[90dvh] flex flex-col shadow-2xl border border-slate-300 overflow-hidden focus-visible:outline-none"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-white border-b border-slate-200 shrink-0 gap-2">
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
            <h2 id="review-modal-title" className="text-sm sm:text-base md:text-lg font-bold text-slate-900 truncate">
              {detail?.pseudonym_label || `Student Response (${responseId})`}
            </h2>
            <span className="text-[10px] sm:text-xs font-mono text-slate-500 bg-slate-100 px-1.5 sm:px-2 py-0.5 rounded border border-slate-200 shrink-0 hidden sm:inline">
              ID: {responseId}
            </span>
            {detail?.is_mock && (
              <span className="text-[10px] sm:text-xs px-2 sm:px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-semibold items-center space-x-1.5 shrink-0 hidden md:inline-flex">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                <span>Offline Demo — Simulated AI Analysis</span>
              </span>
            )}
          </div>

          {/* Navigation & Close */}
          <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
            <button
              type="button"
              onClick={onNavigatePrev}
              disabled={!hasPrev}
              aria-label="Previous student response"
              className="p-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 disabled:opacity-30 focus-visible:ring-2 focus-visible:ring-indigo-500 text-slate-700"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onNavigateNext}
              disabled={!hasNext}
              aria-label="Next student response"
              className="p-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 disabled:opacity-30 focus-visible:ring-2 focus-visible:ring-indigo-500 text-slate-700"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <div className="h-5 w-px bg-slate-200 mx-0.5 sm:mx-1" />
            <button
              type="button"
              onClick={onClose}
              aria-label="Close review dialog"
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-800 focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Mobile Tab Switcher */}
        <div className="lg:hidden flex border-b border-slate-200 bg-white">
          <button
            type="button"
            onClick={() => setActiveMobileTab("image")}
            className={`flex-1 py-2 text-xs font-bold text-center border-b-2 ${
              activeMobileTab === "image"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-slate-500"
            }`}
          >
            Handwritten Image Canvas
          </button>
          <button
            type="button"
            onClick={() => setActiveMobileTab("diagnosis")}
            className={`flex-1 py-2 text-xs font-bold text-center border-b-2 ${
              activeMobileTab === "diagnosis"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-slate-500"
            }`}
          >
            Diagnostic Reasoning &amp; Review
          </button>
        </div>

        {/* Modal Body: Dual Pane Layout */}
        <div className="flex-1 overflow-hidden p-4 grid grid-cols-1 lg:grid-cols-12 gap-4">
          {loading ? (
            <div className="col-span-12 flex items-center justify-center text-slate-400">
              Loading diagnostic analysis...
            </div>
          ) : (
            <>
              {/* Left Pane: Interactive Image Viewer (7 of 12 columns) */}
              <div
                className={`lg:col-span-7 h-full ${
                  activeMobileTab === "image" ? "block" : "hidden lg:block"
                }`}
              >
                <ImageViewerCanvas
                  responseId={responseId}
                  observations={detail?.visual_evidence?.observations || []}
                />
              </div>

              {/* Right Pane: Diagnostic Breakdown & Teacher Override (5 of 12 columns) */}
              <div
                className={`lg:col-span-5 h-full overflow-y-auto space-y-4 pr-1 ${
                  activeMobileTab === "diagnosis" ? "block" : "hidden lg:block"
                }`}
              >
                {/* 1. Summary Card */}
                <DiagnosticSummaryCard
                  answerStatus={detail?.answer_status || "undetermined"}
                  reasoningStatus={detail?.reasoning_status || "undetermined"}
                  qualityStatus={detail?.quality_status || "clear"}
                  isCompensatoryError={detail?.is_compensatory_error}
                  needsTeacherReview={detail?.needs_teacher_review}
                  teacherReviewReason={detail?.teacher_review_reason}
                />

                {/* 2. Error Localization Card */}
                <ErrorLocalizationCard
                  firstError={detail?.diagnosis?.first_supported_error}
                  taxonomyId={detail?.diagnosis?.misconception_taxonomy_id}
                  taxonomyTitle={detail?.diagnosis?.taxonomy_title}
                />

                {/* 3. Step Breakdown List */}
                <StepBreakdownList steps={detail?.diagnosis?.verified_steps || []} />

                {/* 4. Teacher Override Form */}
                <TeacherReviewForm
                  responseId={responseId}
                  initialReviewStatus={detail?.teacher_review_status || "unreviewed"}
                  initialOverrideTaxonomy={detail?.teacher_override_taxonomy_id}
                  initialNotes={detail?.teacher_notes}
                  onReviewSubmitted={() => {
                    if (onReviewChanged) onReviewChanged();
                  }}
                />

                {/* 5. Audit Trail Log */}
                <AuditTrailDrawer responseId={responseId} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
