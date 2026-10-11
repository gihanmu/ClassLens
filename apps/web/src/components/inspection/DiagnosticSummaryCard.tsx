"use client";

import React from "react";
import { CheckCircle2, XCircle, AlertTriangle, AlertCircle, HelpCircle } from "lucide-react";

interface DiagnosticSummaryCardProps {
  answerStatus: string;
  reasoningStatus: string;
  qualityStatus: string;
  isCompensatoryError?: boolean;
  needsTeacherReview?: boolean;
  teacherReviewReason?: string;
}

export function DiagnosticSummaryCard({
  answerStatus,
  reasoningStatus,
  qualityStatus,
  isCompensatoryError = false,
  needsTeacherReview = false,
  teacherReviewReason,
}: DiagnosticSummaryCardProps) {
  const isCorrect = answerStatus === "correct";
  const isReasoningValid = reasoningStatus === "supported_correct";
  const isIncomplete = reasoningStatus === "incomplete";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase">
          Diagnostic Evaluation
        </h3>
        <div className="flex items-center space-x-2">
          {/* Quality Indicator */}
          <span
            className={`inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full border ${
              qualityStatus === "clear"
                ? "bg-slate-50 text-slate-700 border-slate-200"
                : "bg-amber-50 text-amber-800 border-amber-200"
            }`}
          >
            Image: {qualityStatus.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* Final Answer Evaluation Card */}
        <div
          className={`p-3 rounded-lg border flex items-start space-x-3 ${
            isCorrect
              ? "bg-emerald-50/60 border-emerald-200 text-emerald-950"
              : "bg-rose-50/60 border-rose-200 text-rose-950"
          }`}
        >
          {isCorrect ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
          ) : (
            <XCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
          )}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              Final Answer
            </span>
            <span className="text-sm font-bold flex items-center space-x-1">
              <span>{isCorrect ? "Correct (2)" : "Incorrect"}</span>
            </span>
            <span className="text-xs text-slate-600 block mt-0.5">
              {isCorrect ? "Matches target value 2" : "Does not match target 2"}
            </span>
          </div>
        </div>

        {/* Visible Reasoning Evaluation Card */}
        <div
          className={`p-3 rounded-lg border flex items-start space-x-3 ${
            isReasoningValid
              ? "bg-emerald-50/60 border-emerald-200 text-emerald-950"
              : isIncomplete
              ? "bg-amber-50/60 border-amber-200 text-amber-950"
              : "bg-rose-50/60 border-rose-200 text-rose-950"
          }`}
        >
          {isReasoningValid ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
          ) : isIncomplete ? (
            <HelpCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
          ) : (
            <XCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
          )}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              Visible Reasoning
            </span>
            <span className="text-sm font-bold block">
              {isReasoningValid
                ? "Valid Traversal"
                : isIncomplete
                ? "Incomplete Work"
                : "Procedural Error"}
            </span>
            <span className="text-xs text-slate-600 block mt-0.5">
              {isReasoningValid
                ? "All number line steps verified"
                : isIncomplete
                ? "Answer given without steps"
                : "Flawed jump or miscount"}
            </span>
          </div>
        </div>
      </div>

      {/* Compensatory Error Callout */}
      {isCompensatoryError && (
        <div
          role="alert"
          className="p-3 bg-amber-50 border border-amber-300 rounded-lg flex items-start space-x-2 text-amber-900 text-xs"
        >
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong className="font-semibold block">Compensatory Error Detected:</strong>
            Student arrived at correct final answer 2 despite an intermediate arithmetic error.
            Requires targeted teacher check.
          </div>
        </div>
      )}

      {/* Teacher Escalation Callout */}
      {needsTeacherReview && (
        <div
          role="alert"
          className="p-3 bg-indigo-50 border border-indigo-300 rounded-lg flex items-start space-x-2 text-indigo-950 text-xs"
        >
          <AlertCircle className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong className="font-semibold block">Teacher Review Flagged:</strong>
            {teacherReviewReason || "Perceptual confidence below threshold or critic discrepancy flagged."}
          </div>
        </div>
      )}
    </div>
  );
}
