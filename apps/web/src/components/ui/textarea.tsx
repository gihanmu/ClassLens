"use client";

import React, { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  isError?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      id,
      label,
      helperText,
      className,
      isError = false,
      disabled = false,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const textareaId = id || generatedId;
    const helperId = helperText ? `${textareaId}-helper` : undefined;

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-xs font-semibold text-ink-secondary"
          >
            {label}
          </label>
        )}
        <textarea
          id={textareaId}
          ref={ref}
          disabled={disabled}
          aria-invalid={isError ? "true" : undefined}
          aria-describedby={helperId}
          className={cn(
            "w-full rounded-md border bg-surface-base p-3 text-[14px] text-ink-primary placeholder:text-ink-muted transition-colors duration-150 ease-out",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1",
            isError
              ? "border-semantic-error focus-visible:ring-semantic-error/30"
              : "border-border-default hover:border-border-hover focus-visible:border-brand-primary focus-visible:ring-brand-primary/20",
            disabled && "bg-surface-subtle text-ink-muted cursor-not-allowed opacity-60",
            className
          )}
          {...props}
        />
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

Textarea.displayName = "Textarea";
