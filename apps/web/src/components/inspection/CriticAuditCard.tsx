"use client";

import React from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  HelpCircle,
  FileSearch,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface CriticAuditData {
  approved: boolean;
  confidence?: number;
  evidence_grounded?: boolean;
  contradiction_detected?: boolean;
  reinterpretation_needed: boolean;
  discrepancy_notes?: string[];
  requires_teacher_review: boolean;
  teacher_review_reason?: string;
  audit_verdict?: "audit_passed" | "review_required" | "audit_rejected";
}

export interface CriticAuditCardProps {
  criticAudit?: CriticAuditData | null;
  className?: string;
}

export function CriticAuditCard({ criticAudit, className }: CriticAuditCardProps) {
  if (!criticAudit) return null;

  const verdict = criticAudit.audit_verdict || (criticAudit.approved ? "audit_passed" : "review_required");
  const isPassed = verdict === "audit_passed";
  const isReviewRequired = verdict === "review_required";
  const isRejected = verdict === "audit_rejected";

  const confidenceScore = criticAudit.confidence ?? 0.85;
  const qualitativeConfidence =
    confidenceScore >= 0.85
      ? "High (Clear Evidence)"
      : confidenceScore >= 0.70
      ? "Moderate (Partially Supported)"
      : "Low (Review Required)";

  return (
    <div
      className={cn(
        "p-4 rounded-xl border transition-all duration-150 space-y-3",
        isPassed
          ? "bg-surface-base border-emerald-200/80"
          : isReviewRequired
          ? "bg-amber-50/30 border-amber-300"
          : "bg-red-50/30 border-red-300",
        className
      )}
    >
      {/* Header with Grounding Audit Verdict */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-7 h-7 rounded-lg flex items-center justify-center shrink-0",
              isPassed
                ? "bg-emerald-100 text-emerald-800"
                : isReviewRequired
                ? "bg-amber-100 text-amber-900"
                : "bg-red-100 text-red-800"
            )}
          >
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-ink-primary block">
              Independent Critic Grounding Audit
            </span>
            <span className="text-[10px] text-ink-muted block">
              Adversarial verification against physical ink marks
            </span>
          </div>
        </div>

        {/* Verdict Badge */}
        <span
          className={cn(
            "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold font-mono",
            isPassed
              ? "bg-emerald-50 text-emerald-800 border border-emerald-300"
              : isReviewRequired
              ? "bg-amber-50 text-amber-900 border border-amber-300"
              : "bg-red-50 text-red-800 border border-red-300"
          )}
        >
          {isPassed ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Audit Passed
            </>
          ) : isReviewRequired ? (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
              Review Required
            </>
          ) : (
            <>
              <XCircle className="w-3.5 h-3.5 text-red-600" />
              Audit Rejected
            </>
          )}
        </span>
      </div>

      {/* Grid of Audit Attributes */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
        {/* Evidence Grounding */}
        <div className="p-2 rounded-lg bg-surface-subtle border border-border-default space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-ink-muted block">
            Evidence Grounded
          </span>
          <span
            className={cn(
              "font-semibold flex items-center gap-1",
              criticAudit.evidence_grounded !== false
                ? "text-emerald-700"
                : "text-amber-800"
            )}
          >
            {criticAudit.evidence_grounded !== false ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Verified in Ink
              </>
            ) : (
              <>
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Ambiguous Marks
              </>
            )}
          </span>
        </div>

        {/* Contradiction Check */}
        <div className="p-2 rounded-lg bg-surface-subtle border border-border-default space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-ink-muted block">
            Contradictions
          </span>
          <span
            className={cn(
              "font-semibold flex items-center gap-1",
              criticAudit.contradiction_detected
                ? "text-red-700 font-bold"
                : "text-emerald-700"
            )}
          >
            {criticAudit.contradiction_detected ? (
              <>
                <XCircle className="w-3.5 h-3.5 text-red-600" />
                Detected
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                None Detected
              </>
            )}
          </span>
        </div>

        {/* Confidence Tier (Heuristic Indicator) */}
        <div className="p-2 rounded-lg bg-surface-subtle border border-border-default space-y-0.5 col-span-2 sm:col-span-1">
          <span className="text-[10px] uppercase font-bold text-ink-muted block">
            Confidence Indicator
          </span>
          <span className="font-semibold text-ink-primary block truncate">
            {qualitativeConfidence}
          </span>
          <span className="text-[9px] text-ink-muted block font-mono">
            Score: {Math.round(confidenceScore * 100)}% (heuristic indicator)
          </span>
        </div>
      </div>

      {/* Discrepancy Notes or Review Escalation Reason */}
      {(criticAudit.requires_teacher_review || (criticAudit.discrepancy_notes && criticAudit.discrepancy_notes.length > 0)) && (
        <div className="p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 text-xs text-amber-950 space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-[11px] text-amber-900">
            <FileSearch className="w-3.5 h-3.5 text-amber-700" />
            Teacher Escalation Notice:
          </div>
          <p className="text-[11px] leading-relaxed text-amber-900">
            {criticAudit.teacher_review_reason ||
              "Visual ambiguities or incomplete marks require teacher review before instructional action."}
          </p>
          {criticAudit.discrepancy_notes && criticAudit.discrepancy_notes.length > 0 && (
            <ul className="list-disc pl-4 text-[10px] text-amber-900/90 space-y-0.5 pt-0.5">
              {criticAudit.discrepancy_notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
