"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Clock,
  Sparkles,
  HelpCircle,
} from "lucide-react";

export type SemanticStatus =
  | "success"
  | "error"
  | "warning"
  | "info"
  | "neutral"
  | "pending"
  | "mock";

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: SemanticStatus;
  label?: string;
  showIcon?: boolean;
  size?: "sm" | "md";
}

const statusConfig: Record<
  SemanticStatus,
  {
    styles: string;
    icon: React.ComponentType<{ className?: string }>;
    defaultLabel: string;
  }
> = {
  success: {
    styles: "bg-semantic-success-soft text-semantic-success border-semantic-success-border",
    icon: CheckCircle2,
    defaultLabel: "Correct",
  },
  error: {
    styles: "bg-semantic-error-soft text-semantic-error border-semantic-error-border",
    icon: XCircle,
    defaultLabel: "Error",
  },
  warning: {
    styles: "bg-semantic-warning-soft text-semantic-warning border-semantic-warning-border",
    icon: AlertTriangle,
    defaultLabel: "Needs Review",
  },
  info: {
    styles: "bg-semantic-info-soft text-semantic-info border-semantic-info-border",
    icon: Info,
    defaultLabel: "Information",
  },
  neutral: {
    styles: "bg-semantic-neutral-soft text-semantic-neutral border-semantic-neutral-border",
    icon: HelpCircle,
    defaultLabel: "Unreviewed",
  },
  pending: {
    styles: "bg-brand-yellow-soft text-[#855D00] border-brand-yellow/60",
    icon: Clock,
    defaultLabel: "In Progress",
  },
  mock: {
    styles: "bg-brand-purple-soft text-brand-primary border-brand-primary/30",
    icon: Sparkles,
    defaultLabel: "Simulated AI",
  },
};

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  (
    {
      className,
      status,
      label,
      showIcon = true,
      size = "md",
      children,
      ...props
    },
    ref
  ) => {
    const config = statusConfig[status];
    const IconComponent = config.icon;
    const displayText = children || label || config.defaultLabel;

    return (
      <span
        ref={ref}
        role="status"
        className={cn(
          "inline-flex items-center font-sans font-semibold border select-none rounded-full",
          size === "sm"
            ? "text-[11px] px-2 py-0.5 gap-1 leading-tight"
            : "text-xs px-2.5 py-0.5 gap-1.5 leading-tight",
          config.styles,
          className
        )}
        {...props}
      >
        {showIcon && (
          <IconComponent
            className={cn(size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5", "shrink-0")}
            aria-hidden="true"
          />
        )}
        <span>{displayText}</span>
      </span>
    );
  }
);

StatusBadge.displayName = "StatusBadge";
