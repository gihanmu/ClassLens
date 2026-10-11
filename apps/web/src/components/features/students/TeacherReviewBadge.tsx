import * as React from "react";
import { AlertTriangle, CheckCircle2, Edit3, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { getTeacherReviewStatusConfig } from "@/lib/terminology";

export interface TeacherReviewBadgeProps {
  reviewStatus?: string | null;
  needsReview?: boolean;
  className?: string;
  size?: "sm" | "md";
}

export function TeacherReviewBadge({
  reviewStatus,
  needsReview = false,
  className,
  size = "sm",
}: TeacherReviewBadgeProps) {
  const config = getTeacherReviewStatusConfig(reviewStatus, needsReview);

  if (config.code === "overridden") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1 font-semibold rounded-full bg-accent-coral/15 text-accent-coral border border-accent-coral/30 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
          className
        )}
      >
        <Edit3 className={cn("shrink-0", size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  if (config.code === "reviewed") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1 font-semibold rounded-full bg-accent-mint text-emerald-900 border border-emerald-300 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
          className
        )}
      >
        <CheckCircle2 className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-emerald-700" : "w-3.5 h-3.5 text-emerald-700")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  if (config.code === "needs_review") {
    return (
      <span
        title={config.description}
        className={cn(
          "inline-flex items-center gap-1 font-semibold rounded-full bg-accent-yellow/30 text-amber-950 border border-amber-300 shadow-2xs whitespace-nowrap",
          size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
          className
        )}
      >
        <AlertTriangle className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-amber-800" : "w-3.5 h-3.5 text-amber-800")} aria-hidden="true" />
        <span>{config.label}</span>
      </span>
    );
  }

  // Not reviewed
  return (
    <span
      title={config.description}
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded-full bg-surface-muted text-ink-muted border border-border-default whitespace-nowrap",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        className
      )}
    >
      <Clock className={cn("shrink-0", size === "sm" ? "w-3 h-3 text-ink-muted" : "w-3.5 h-3.5 text-ink-muted")} aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  );
}
