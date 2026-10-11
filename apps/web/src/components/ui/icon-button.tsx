"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type IconButtonVariant = "neutral" | "primary" | "destructive" | "inverse";
export type IconButtonSize = "sm" | "md" | "lg";

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  "aria-label": string; // Mandatory for accessibility
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  icon?: React.ReactNode;
}

const variantStyles: Record<IconButtonVariant, string> = {
  neutral:
    "bg-surface-base text-ink-secondary border-border-default hover:bg-surface-subtle hover:text-ink-primary hover:border-border-strong active:bg-surface-muted shadow-xs",
  primary:
    "bg-brand-primary text-white border-transparent hover:bg-brand-primary-hover active:bg-brand-primary-active shadow-xs",
  destructive:
    "bg-semantic-error-soft text-semantic-error border-semantic-error-border hover:bg-[#FDE2E4] active:bg-[#FBC4C7]",
  inverse:
    "bg-white/10 text-white border-white/20 hover:bg-white/20 active:bg-white/30",
};

// All sizes enforce minimum 44px interaction dimension per WCAG 2.2 AA target size criteria
const sizeStyles: Record<IconButtonSize, string> = {
  sm: "h-[44px] w-[44px] min-h-[44px] min-w-[44px] text-sm",
  md: "h-[44px] w-[44px] min-h-[44px] min-w-[44px] text-base",
  lg: "h-[48px] w-[48px] min-h-[48px] min-w-[48px] text-lg",
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      children,
      className,
      variant = "neutral",
      size = "md",
      icon,
      type = "button",
      disabled = false,
      "aria-label": ariaLabel,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        aria-label={ariaLabel}
        className={cn(
          "inline-flex items-center justify-center rounded-lg border transition-all duration-150 ease-out select-none shrink-0",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2",
          "active:scale-[0.98]",
          "disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:transform-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {icon || children}
      </button>
    );
  }
);

IconButton.displayName = "IconButton";
