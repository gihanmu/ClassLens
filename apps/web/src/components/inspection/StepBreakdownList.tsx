"use client";

import React from "react";
import { CheckCircle2, AlertOctagon } from "lucide-react";

interface VerifiedStep {
  step_number: number;
  operation: string;
  expected_result: number;
  observed_result?: number;
  is_correct: boolean;
  evidence_citation: string;
}

interface StepBreakdownListProps {
  steps: VerifiedStep[];
}

export function StepBreakdownList({ steps }: StepBreakdownListProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase mb-2">
          Step-by-Step Reasoning
        </h3>
        <p className="text-sm text-slate-500 italic">
          No sequential steps recorded or student wrote final answer directly.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase">
          Step-by-Step Reasoning
        </h3>
        <span className="text-xs text-slate-500 font-mono">
          {steps.filter((s) => s.is_correct).length} of {steps.length} Steps Valid
        </span>
      </div>

      <div className="space-y-2">
        {steps.map((step) => {
          return (
            <div
              key={step.step_number}
              className={`p-3 rounded-lg border transition-all ${
                step.is_correct
                  ? "bg-slate-50/80 border-slate-200"
                  : "bg-rose-50/80 border-rose-200 shadow-sm"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="h-5 w-5 rounded-full bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center">
                    {step.step_number}
                  </span>
                  <span className="font-medium text-sm text-slate-900">
                    {step.operation}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5">
                  {step.is_correct ? (
                    <span className="inline-flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
                      <span>Valid</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                      <AlertOctagon className="h-3.5 w-3.5 text-rose-600" aria-hidden="true" />
                      <span>Flaw Localized</span>
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-2 text-xs flex items-center space-x-4 text-slate-600">
                <span>
                  Expected: <strong className="font-mono">{step.expected_result}</strong>
                </span>
                <span>
                  Observed:{" "}
                  <strong className="font-mono text-slate-900">
                    {step.observed_result !== undefined ? step.observed_result : "None"}
                  </strong>
                </span>
              </div>

              <p className="mt-1.5 text-xs text-slate-500 italic border-t border-slate-100 pt-1">
                {step.evidence_citation}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
