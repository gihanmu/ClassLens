"use client";

import React, { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  isError?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      id,
      label,
      helperText,
      className,
      type = "text",
      isError = false,
      leftIcon,
      rightIcon,
      disabled = false,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const helperId = helperText ? `${inputId}-helper` : undefined;

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-ink-secondary"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <span
              className="absolute left-3.5 flex items-center text-ink-muted pointer-events-none"
              aria-hidden="true"
            >
              {leftIcon}
            </span>
          )}
          <input
            id={inputId}
            ref={ref}
            type={type}
            disabled={disabled}
            aria-invalid={isError ? "true" : undefined}
            aria-describedby={helperId}
            className={cn(
              "h-[44px] w-full rounded-md border bg-surface-base px-3.5 text-[15px] text-ink-primary placeholder:text-ink-muted transition-colors duration-150 ease-out",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1",
              isError
                ? "border-semantic-error text-semantic-error focus-visible:ring-semantic-error/30"
                : "border-border-default hover:border-border-hover focus-visible:border-brand-primary focus-visible:ring-brand-primary/20",
              disabled && "bg-surface-subtle text-ink-muted cursor-not-allowed opacity-60",
              leftIcon && "pl-10",
              rightIcon && "pr-10",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <span
              className="absolute right-3.5 flex items-center text-ink-muted pointer-events-none"
              aria-hidden="true"
            >
              {rightIcon}
            </span>
          )}
        </div>
        {helperText && (
          <p
            id={helperId}
            className={cn(
              "text-[11px]",
              isError ? "text-semantic-error font-medium" : "text-ink-muted"
            )}
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
