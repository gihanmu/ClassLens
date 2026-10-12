import * as React from "react";
import { AlertCircle, Lightbulb, Zap, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { FirstSupportedError } from "@/lib/api";
import { getMisconceptionPlainLanguage } from "@/lib/terminology";

export interface MisconceptionCardProps {
  error?: FirstSupportedError | null;
  misconceptionTitle?: string;
  isCompensatoryError?: boolean;
  evidenceSufficiency?: string;
  reasoningStatus?: string;
  className?: string;
}

export function MisconceptionCard({
  error,
  misconceptionTitle,
  isCompensatoryError,
  evidenceSufficiency,
  reasoningStatus,
  className,
}: MisconceptionCardProps) {
  if (!error && !misconceptionTitle) {
    if (evidenceSufficiency === "insufficient" || reasoningStatus === "incomplete") {
      return (
        <div
          className={cn(
            "p-4 rounded-xl bg-amber-50/50 border border-amber-300 text-amber-950 flex items-start gap-3",
            className
          )}
        >
          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
            <HelpCircle className="w-4 h-4 text-amber-800" />
          </div>
          <div>
            <h4 className="text-sm font-bold">No Misconception Assigned (Insufficient Visual Evidence)</h4>
            <p className="text-xs text-amber-900/90 mt-0.5 leading-relaxed">
              Visual evidence is incomplete or ambiguous. Procedural misconceptions are withheld to prevent ungrounded inferences until an educator reviews the handwritten work.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div
        className={cn(
          "p-4 rounded-xl bg-accent-mint/30 border border-emerald-300/60 text-emerald-900 flex items-start gap-3",
          className
        )}
      >
        <div className="w-8 h-8 rounded-full bg-accent-mint flex items-center justify-center shrink-0">
          <Lightbulb className="w-4 h-4 text-emerald-800" />
        </div>
        <div>
          <h4 className="text-sm font-bold">No Procedural Errors Detected</h4>
          <p className="text-xs text-emerald-800/90 mt-0.5 leading-relaxed">
            The student’s number-line representation and final numerical evaluation follow valid mathematical reasoning.
          </p>
        </div>
      </div>
    );
  }

  const rawCode = error?.error_type || misconceptionTitle;
  const plainTitle = getMisconceptionPlainLanguage(rawCode);

  return (
    <div
      className={cn(
        "p-4 rounded-xl bg-surface-base border border-accent-coral/30 shadow-xs space-y-3",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent-coral/15 text-accent-coral flex items-center justify-center shrink-0">
            <AlertCircle className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-ink-primary">
            First Supported Error • Step {error?.step_number || 1}
          </span>
        </div>

        {isCompensatoryError && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-accent-yellow/30 text-amber-950 border border-amber-300">
            <Zap className="w-3 h-3 text-amber-700" />
            Compensatory Error
          </span>
        )}
      </div>

      {/* Plain-Language Misconception */}
      <div className="bg-surface-subtle p-3 rounded-lg border border-border-default space-y-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-ink-muted">
            Diagnosed Misconception
          </span>
          {rawCode && (
            <span className="text-[10px] font-mono text-ink-muted bg-surface-muted px-1.5 py-0.5 rounded">
              {rawCode}
            </span>
          )}
        </div>
        <div className="text-sm font-bold text-ink-primary">
          {plainTitle}
        </div>
        {error?.explanation && (
          <p className="text-xs text-ink-secondary mt-1.5 leading-relaxed">
            {error.explanation}
          </p>
        )}
      </div>

      {/* Observed vs Expected Comparison */}
      {error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <div className="p-2.5 rounded bg-red-50/50 border border-red-200/60 text-red-950">
            <span className="text-[10px] uppercase font-semibold text-red-700 block mb-0.5">
              Observed Action
            </span>
            <span className="font-mono text-xs font-medium">
              {error.observed_behavior}
            </span>
          </div>

          <div className="p-2.5 rounded bg-emerald-50/50 border border-emerald-200/60 text-emerald-950">
            <span className="text-[10px] uppercase font-semibold text-emerald-700 block mb-0.5">
              Expected Action
            </span>
            <span className="font-mono text-xs font-medium">
              {error.expected_behavior}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
