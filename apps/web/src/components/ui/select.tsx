"use client";

import React, { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  isError?: boolean;
  options?: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      id,
      label,
      helperText,
      className,
      isError = false,
      disabled = false,
      options,
      placeholder,
      children,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const selectId = id || generatedId;
    const helperId = helperText ? `${selectId}-helper` : undefined;

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-xs font-semibold text-ink-secondary"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          <select
            id={selectId}
            ref={ref}
            disabled={disabled}
            aria-invalid={isError ? "true" : undefined}
            aria-describedby={helperId}
            className={cn(
              "h-[44px] w-full appearance-none rounded-md border bg-surface-base pl-3.5 pr-10 text-[14px] text-ink-primary transition-colors duration-150 ease-out cursor-pointer",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1",
              isError
                ? "border-semantic-error focus-visible:ring-semantic-error/30"
                : "border-border-default hover:border-border-hover focus-visible:border-brand-primary focus-visible:ring-brand-primary/20",
              disabled && "bg-surface-subtle text-ink-muted cursor-not-allowed opacity-60",
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-3.5 h-4 w-4 text-ink-muted"
            aria-hidden="true"
          />
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

Select.displayName = "Select";
