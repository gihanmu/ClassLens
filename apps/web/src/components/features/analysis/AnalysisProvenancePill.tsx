import * as React from "react";
import { Sparkles, UserCheck, Shield, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProvenanceType =
  | "offline_simulated"
  | "ai_proposed"
  | "teacher_confirmed"
  | "teacher_overridden";

export interface AnalysisProvenancePillProps {
  provenance: ProvenanceType | string;
  className?: string;
}

export function AnalysisProvenancePill({
  provenance,
  className,
}: AnalysisProvenancePillProps) {
  const norm = (provenance || "").toLowerCase();

  if (norm.includes("overridden")) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-accent-coral/15 text-accent-coral border border-accent-coral/30",
          className
        )}
      >
        <UserCheck className="w-3 h-3" aria-hidden="true" />
        <span>Teacher Overridden</span>
      </span>
    );
  }

  if (norm.includes("confirmed") || norm.includes("reviewed")) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-accent-mint text-emerald-800 border border-emerald-300",
          className
        )}
      >
        <Shield className="w-3 h-3" aria-hidden="true" />
        <span>Teacher Confirmed</span>
      </span>
    );
  }

  if (norm.includes("ai_proposed") || norm.includes("live")) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-brand-light text-brand-primary border border-brand-primary/20",
          className
        )}
      >
        <BrainCircuit className="w-3 h-3" aria-hidden="true" />
        <span>AI Hypothesis</span>
      </span>
    );
  }

  // default / offline_simulated
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-surface-subtle text-ink-secondary border border-border-default",
        className
      )}
    >
      <Sparkles className="w-3 h-3 text-brand-primary" aria-hidden="true" />
      <span>Simulated Engine (SymPy)</span>
    </span>
  );
}
