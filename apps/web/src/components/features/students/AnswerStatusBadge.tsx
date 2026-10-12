import * as React from "react";
import { Check, X, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { getAnswerStatusConfig } from "@/lib/terminology";

export interface AnswerStatusBadgeProps {
  status: string | null | undefined;
  taskStatus?: string | null;
  className?: string;
  size?: "sm" | "md";
}

export function AnswerStatusBadge({
  status,
  taskStatus,
  className,
  size = "md",
}: AnswerStatusBadgeProps) {
  const config = getAnswerStatusConfig(status, taskStatus);

  if (config.tone === "success") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1.5 font-semibold rounded-full bg-accent-mint text-emerald-900 border border-emerald-300/70 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
          className
        )}
      >
        <Check className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-emerald-700" : "w-3.5 h-3.5 text-emerald-700")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  if (config.tone === "error") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1.5 font-semibold rounded-full bg-accent-coral/15 text-accent-coral border border-accent-coral/30 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
          className
        )}
      >
        <X className={cn("shrink-0", size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  return (
    <span
      title={config.description}
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded-full bg-surface-muted text-ink-secondary border border-border-default whitespace-nowrap",
        size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
        className
      )}
    >
      <HelpCircle className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-ink-muted" : "w-3.5 h-3.5 text-ink-muted")} aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  );
}
