import * as React from "react";
import { cn } from "@/lib/utils";
import { Typography } from "@/components/ui/typography";

export type MetricAccent = "brand" | "coral" | "mint" | "yellow" | "neutral";

export interface MetricCardProps {
  title: string;
  value: string | number;
  denominator?: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  accent?: MetricAccent;
  className?: string;
}

const accentStyles: Record<
  MetricAccent,
  { iconBg: string; iconColor: string; borderAccent?: string }
> = {
  brand: {
    iconBg: "bg-brand-light",
    iconColor: "text-brand-primary",
    borderAccent: "hover:border-brand-primary/40",
  },
  coral: {
    iconBg: "bg-accent-coral/10",
    iconColor: "text-accent-coral",
    borderAccent: "hover:border-accent-coral/40",
  },
  mint: {
    iconBg: "bg-accent-mint",
    iconColor: "text-semantic-success",
    borderAccent: "hover:border-semantic-success/40",
  },
  yellow: {
    iconBg: "bg-accent-yellow/20",
    iconColor: "text-semantic-warning",
    borderAccent: "hover:border-semantic-warning/40",
  },
  neutral: {
    iconBg: "bg-surface-muted",
    iconColor: "text-ink-secondary",
    borderAccent: "hover:border-border-hover",
  },
};

export function MetricCard({
  title,
  value,
  denominator,
  subtext,
  icon,
  accent = "brand",
  className,
}: MetricCardProps) {
  const style = accentStyles[accent];

  return (
    <div
      className={cn(
        "flex flex-col p-5 rounded-xl bg-surface-base border border-border-default shadow-xs transition-all duration-200",
        style.borderAccent,
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-3 min-h-[32px]">
        <Typography variant="body-sm" className="font-medium text-ink-secondary line-clamp-2 leading-tight text-xs sm:text-sm">
          {title}
        </Typography>
        {icon && (
          <div
            className={cn(
              "w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-transform",
              style.iconBg,
              style.iconColor
            )}
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1 mt-auto">
        <span className="font-display text-3xl font-bold tracking-tight text-ink-primary">
          {value}
        </span>
        {denominator !== undefined && (
          <span className="font-sans text-sm text-ink-muted font-medium">
            /{denominator}
          </span>
        )}
      </div>

      {subtext && (
        <Typography variant="caption" className="mt-1 text-ink-muted">
          {subtext}
        </Typography>
      )}
    </div>
  );
}
