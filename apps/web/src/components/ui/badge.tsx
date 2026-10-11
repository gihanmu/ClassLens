"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant = "neutral" | "primary" | "accent" | "warm" | "mint" | "outline";
export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
}

const badgeVariantStyles: Record<BadgeVariant, string> = {
  neutral:
    "bg-surface-subtle text-ink-secondary border-border-default",
  primary:
    "bg-brand-primary-soft text-brand-primary border-brand-primary/20",
  accent:
    "bg-brand-coral/10 text-brand-coral border-brand-coral/20",
  warm:
    "bg-brand-yellow-soft text-[#855D00] border-brand-yellow/50",
  mint:
    "bg-brand-mint text-[#066141] border-[#A3E7C8]",
  outline:
    "bg-transparent text-ink-primary border-border-strong",
};

const badgeSizeStyles: Record<BadgeSize, string> = {
  sm: "text-[11px] font-semibold px-2 py-0.5 rounded-full gap-1 leading-tight",
  md: "text-xs font-semibold px-2.5 py-1 rounded-full gap-1.5 leading-tight",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      className,
      variant = "neutral",
      size = "md",
      icon,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center font-sans border select-none",
          badgeVariantStyles[variant],
          badgeSizeStyles[size],
          className
        )}
        {...props}
      >
        {icon && <span className="inline-flex shrink-0" aria-hidden="true">{icon}</span>}
        <span>{children}</span>
      </span>
    );
  }
);

Badge.displayName = "Badge";
