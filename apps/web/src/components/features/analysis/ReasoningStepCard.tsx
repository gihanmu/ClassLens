import * as React from "react";
import { CheckCircle2, XCircle, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { VerifiedStep } from "@/lib/api";

export interface ReasoningStepCardProps {
  step: VerifiedStep;
  className?: string;
}

export function ReasoningStepCard({ step, className }: ReasoningStepCardProps) {
  const isCorrect = step.is_correct;

  return (
    <div
      className={cn(
        "flex flex-col p-3.5 rounded-lg border transition-all duration-150",
        isCorrect
          ? "bg-surface-base border-border-default hover:border-emerald-300"
          : "bg-red-50/20 border-red-200/80 hover:border-red-300",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold font-mono bg-surface-muted text-ink-primary">
            {step.step_number}
          </span>
          <span className="text-xs font-semibold text-ink-primary">
            {step.operation}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium",
              isCorrect
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-red-50 text-red-800 border border-red-200"
            )}
          >
            {isCorrect ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-emerald-600" aria-hidden="true" />
                SymPy Valid
              </>
            ) : (
              <>
                <XCircle className="w-3 h-3 text-red-600" aria-hidden="true" />
                Error
              </>
            )}
          </span>
        </div>
      </div>

      {/* Details Row */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-surface-subtle p-2 rounded border border-border-subtle mt-1">
        <div>
          <span className="text-[10px] uppercase text-ink-muted block font-sans">
            Expected:
          </span>
          <span className="font-semibold text-ink-primary">
            {step.expected_result}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-ink-muted block font-sans">
            Observed:
          </span>
          <span
            className={cn(
              "font-semibold",
              isCorrect ? "text-ink-primary" : "text-accent-coral font-bold"
            )}
          >
            {step.observed_result !== undefined ? step.observed_result : "None/Omitted"}
          </span>
        </div>
      </div>

      {step.evidence_citation && (
        <p className="text-[11px] text-ink-muted mt-2 italic font-sans">
          Evidence: {step.evidence_citation}
        </p>
      )}
    </div>
  );
}
