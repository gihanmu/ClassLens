"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface RadioOption {
  value: string;
  label: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
}

export interface RadioGroupProps {
  name: string;
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  options: RadioOption[];
  className?: string;
  orientation?: "vertical" | "horizontal";
  disabled?: boolean;
}

export function RadioGroup({
  name,
  value: controlledValue,
  defaultValue,
  onChange,
  options,
  className,
  orientation = "vertical",
  disabled = false,
}: RadioGroupProps) {
  const [internalValue, setInternalValue] = React.useState<string>(
    controlledValue !== undefined ? controlledValue : defaultValue || ""
  );

  const currentValue = controlledValue !== undefined ? controlledValue : internalValue;

  const handleChange = (newVal: string) => {
    if (controlledValue === undefined) {
      setInternalValue(newVal);
    }
    if (onChange) {
      onChange(newVal);
    }
  };

  return (
    <div
      role="radiogroup"
      aria-orientation={orientation}
      className={cn(
        "flex gap-3",
        orientation === "vertical" ? "flex-col" : "flex-row flex-wrap",
        className
      )}
    >
      {options.map((option) => {
        const isChecked = currentValue === option.value;
        const isDisabled = disabled || option.disabled;
        const optionId = `${name}-${option.value}`;

        return (
          <label
            key={option.value}
            htmlFor={optionId}
            className={cn(
              "flex items-start gap-3 p-3.5 rounded-md border text-sm transition-all duration-150 cursor-pointer select-none",
              isChecked
                ? "bg-brand-primary-soft/30 border-brand-primary/50 text-ink-primary shadow-xs"
                : "bg-surface-card border-border-default hover:border-border-strong text-ink-secondary hover:text-ink-primary",
              isDisabled && "opacity-50 cursor-not-allowed pointer-events-none"
            )}
          >
            <div className="relative flex items-center justify-center pt-0.5">
              <input
                type="radio"
                id={optionId}
                name={name}
                value={option.value}
                checked={isChecked}
                disabled={isDisabled}
                onChange={() => handleChange(option.value)}
                className="peer sr-only"
              />
              <div
                className={cn(
                  "h-4 w-4 rounded-full border border-border-strong bg-white transition-colors flex items-center justify-center",
                  isChecked && "border-brand-primary bg-brand-primary",
                  "peer-focus-visible:ring-2 peer-focus-visible:ring-brand-primary peer-focus-visible:ring-offset-2"
                )}
                aria-hidden="true"
              >
                {isChecked && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-ink-primary leading-tight">
                {option.label}
              </span>
              {option.description && (
                <span className="text-xs text-ink-muted mt-1 leading-normal">
                  {option.description}
                </span>
              )}
            </div>
          </label>
        );
      })}
    </div>
  );
}
