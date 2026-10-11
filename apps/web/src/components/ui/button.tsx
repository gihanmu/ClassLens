"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "destructive"
  | "coral";

export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  icon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-primary text-white border-transparent hover:bg-brand-primary-hover active:bg-brand-primary-active shadow-xs",
  secondary:
    "bg-brand-primary-soft text-brand-primary border-transparent hover:bg-[#E0DCFF] active:bg-[#D4CEFF]",
  outline:
    "bg-surface-base text-ink-primary border-border-default hover:bg-surface-subtle hover:border-border-strong active:bg-surface-muted shadow-xs",
  ghost:
    "bg-transparent text-ink-primary border-transparent hover:bg-surface-subtle active:bg-surface-muted",
  destructive:
    "bg-semantic-error text-white border-transparent hover:bg-[#9E1B29] active:bg-[#851622] shadow-xs",
  coral:
    "bg-brand-coral text-white border-transparent hover:bg-brand-coral-hover active:bg-[#BF3E20] shadow-xs",
};

// All sizes enforce minimum 44px interaction height per WCAG 2.2 AA target size criteria
const sizeStyles: Record<ButtonSize, string> = {
  sm: "min-h-[44px] h-[44px] px-3.5 text-xs font-semibold gap-2",
  md: "min-h-[44px] h-[44px] px-4 text-sm font-semibold gap-2",
  lg: "min-h-[48px] h-[48px] px-6 text-base font-bold gap-2.5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      icon,
      type = "button",
      ...props
    },
    ref
  ) => {
    const effectiveLeftIcon = icon || leftIcon;

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        aria-busy={isLoading ? "true" : undefined}
        className={cn(
          "inline-flex flex-row items-center justify-center rounded-lg border font-sans select-none whitespace-nowrap transition-all duration-150 ease-out",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2",
          "active:scale-[0.98]",
          "disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:transform-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 shrink-0 animate-spin" aria-hidden="true" />
            <span className="truncate">{children}</span>
          </>
        ) : (
          <>
            {effectiveLeftIcon && (
              <span className="inline-flex shrink-0 items-center justify-center" aria-hidden="true">
                {effectiveLeftIcon}
              </span>
            )}
            <span className="inline-flex items-center truncate gap-2">{children}</span>
            {rightIcon && (
              <span className="inline-flex shrink-0 items-center justify-center" aria-hidden="true">
                {rightIcon}
              </span>
            )}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
