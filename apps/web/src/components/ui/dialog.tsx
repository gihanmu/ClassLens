"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { IconButton } from "./icon-button";

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  footer?: React.ReactNode;
  noPadding?: boolean;
}

const sizeStyles: Record<string, string> = {
  sm: "max-w-md",       // ~448px (confirmations, small prompts)
  md: "max-w-xl",       // ~576px (switchers, selectors)
  lg: "max-w-[760px]",  // ~760px (forms: create assessment, worksheet upload)
  xl: "max-w-5xl",      // ~1024px (dual pane, case audits)
  full: "max-w-7xl",    // ~1280px (full inspection views)
};

export function Dialog({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
  contentClassName,
  size = "lg",
  footer,
  noPadding = false,
}: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.body.style.overflow = "hidden";

      // Focus first focusable element or dialog
      const timer = setTimeout(() => {
        if (dialogRef.current) {
          const firstInput = dialogRef.current.querySelector<HTMLElement>(
            'input:not([disabled]), textarea:not([disabled]), button:not([disabled]):not([aria-label="Close dialog"])'
          );
          if (firstInput) {
            firstInput.focus();
          } else {
            dialogRef.current.focus();
          }
        }
      }, 50);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          onClose();
          return;
        }

        // Accessible Tab focus trapping
        if (e.key === "Tab" && dialogRef.current) {
          const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          if (focusable.length === 0) return;

          const first = focusable[0];
          const last = focusable[focusable.length - 1];

          if (e.shiftKey) {
            if (document.activeElement === first) {
              last.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === last) {
              first.focus();
              e.preventDefault();
            }
          }
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => {
        clearTimeout(timer);
        document.body.style.overflow = "";
        window.removeEventListener("keydown", handleKeyDown);
        if (previousActiveElement.current) {
          previousActiveElement.current.focus();
        }
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "dialog-title" : undefined}
      aria-describedby={description ? "dialog-desc" : undefined}
      className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 lg:p-6"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className={cn(
          "relative w-full max-h-[90dvh] sm:max-h-[88dvh] rounded-2xl bg-surface-card border border-border-default shadow-modal overflow-hidden flex flex-col focus-visible:outline-none",
          sizeStyles[size],
          className
        )}
      >
        {(title || description) && (
          <div className="flex items-start justify-between px-5 py-4 sm:px-6 sm:py-5 border-b border-border-default/80 bg-surface-card shrink-0 gap-3">
            <div className="flex flex-col min-w-0 pr-2">
              {title && (
                <h2 id="dialog-title" className="text-base sm:text-lg font-bold text-ink-primary leading-snug">
                  {title}
                </h2>
              )}
              {description && (
                <p id="dialog-desc" className="text-xs text-ink-muted mt-1 leading-normal">
                  {description}
                </p>
              )}
            </div>
            <IconButton
              variant="neutral"
              size="sm"
              aria-label="Close dialog"
              onClick={onClose}
              icon={<X className="h-4 w-4" />}
              className="shrink-0 -mr-1"
            />
          </div>
        )}

        {noPadding ? (
          <div className={cn("flex-1 min-h-0 flex flex-col overflow-hidden", contentClassName)}>
            {children}
          </div>
        ) : (
          <div
            className={cn(
              "flex-1 min-h-0 overflow-y-auto p-4 sm:p-6",
              contentClassName
            )}
          >
            {children}
          </div>
        )}

        {footer && (
          <div className="px-5 py-3.5 sm:px-6 sm:py-4 border-t border-border-default/80 bg-surface-subtle/40 shrink-0 flex items-center justify-end gap-2.5">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export function DialogBody({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex-1 min-h-0 overflow-y-auto p-4 sm:p-6", className)}>
      {children}
    </div>
  );
}

export function DialogFooter({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "px-5 py-3.5 sm:px-6 sm:py-4 border-t border-border-default/80 bg-surface-subtle/40 shrink-0 flex items-center justify-end gap-2.5",
        className
      )}
    >
      {children}
    </div>
  );
}
