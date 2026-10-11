"use client";

import React from "react";
import { AlertCircle, CheckCircle } from "lucide-react";

interface FirstSupportedError {
  step_number: number;
  error_type: string;
  observed_behavior: string;
  expected_behavior: string;
  explanation: string;
}

interface ErrorLocalizationCardProps {
  firstError?: FirstSupportedError;
  taxonomyId?: string;
  taxonomyTitle?: string;
}

export function ErrorLocalizationCard({
  firstError,
  taxonomyId,
  taxonomyTitle,
}: ErrorLocalizationCardProps) {
  if (!firstError && !taxonomyId) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center space-x-2 text-emerald-800">
          <CheckCircle className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          <h3 className="font-semibold text-sm uppercase tracking-wide">
            Root Cause Localization
          </h3>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          No procedural errors detected. Student number line traversal and final calculation are fully consistent.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-rose-200 p-5 shadow-sm space-y-3 bg-rose-50/20">
      <div className="flex items-center justify-between border-b border-rose-100 pb-2">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-rose-600" aria-hidden="true" />
          <h3 className="font-semibold text-rose-950 text-sm uppercase tracking-wide">
            First-Error Localization
          </h3>
        </div>
        {firstError && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200 font-mono">
            Failed at Step {firstError.step_number}
          </span>
        )}
      </div>

      {taxonomyId && (
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Pedagogical Classification:
          </span>
          <span className="inline-flex items-center text-xs font-bold px-2.5 py-1 rounded bg-rose-100 text-rose-900 border border-rose-300">
            {taxonomyId}
          </span>
        </div>
      )}

      {taxonomyTitle && (
        <h4 className="font-bold text-slate-900 text-sm">
          {taxonomyTitle}
        </h4>
      )}

      {firstError && (
        <div className="grid grid-cols-2 gap-3 text-xs mt-2 bg-white p-3 rounded-lg border border-slate-200">
          <div>
            <span className="font-semibold text-slate-500 block uppercase">Observed Hop:</span>
            <span className="font-mono text-rose-800 mt-0.5 block">{firstError.observed_behavior}</span>
          </div>
          <div>
            <span className="font-semibold text-slate-500 block uppercase">Expected Rule:</span>
            <span className="font-mono text-emerald-800 mt-0.5 block">{firstError.expected_behavior}</span>
          </div>
        </div>
      )}

      {firstError?.explanation && (
        <p className="text-xs text-slate-700 leading-relaxed bg-rose-50/50 p-2.5 rounded border border-rose-100">
          <strong>Diagnosis:</strong> {firstError.explanation}
        </p>
      )}
    </div>
  );
}
