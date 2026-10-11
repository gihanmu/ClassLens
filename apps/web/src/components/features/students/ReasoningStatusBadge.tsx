import * as React from "react";
import { CheckCircle2, AlertTriangle, HelpCircle, FileQuestion } from "lucide-react";
import { cn } from "@/lib/utils";
import { getReasoningStatusConfig } from "@/lib/terminology";

export interface ReasoningStatusBadgeProps {
  status: string | null | undefined;
  className?: string;
  size?: "sm" | "md";
}

export function ReasoningStatusBadge({
  status,
  className,
  size = "md",
}: ReasoningStatusBadgeProps) {
  const config = getReasoningStatusConfig(status);

  if (config.tone === "success") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1.5 font-semibold rounded-full bg-brand-light text-brand-primary border border-brand-primary/20 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
          className
        )}
      >
        <CheckCircle2 className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-brand-primary" : "w-3.5 h-3.5 text-brand-primary")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  if (config.tone === "error") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1.5 font-semibold rounded-full bg-amber-50 text-amber-900 border border-amber-300 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
          className
        )}
      >
        <AlertTriangle className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-amber-700" : "w-3.5 h-3.5 text-amber-700")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  if (config.tone === "warning") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1.5 font-medium rounded-full bg-surface-muted text-ink-secondary border border-border-default whitespace-nowrap",
          size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
          className
        )}
      >
        <FileQuestion className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-amber-700" : "w-3.5 h-3.5 text-amber-700")} aria-hidden="true" />
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
