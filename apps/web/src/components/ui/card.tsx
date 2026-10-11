"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type CardVariant =
  | "default"
  | "interactive"
  | "highlighted"
  | "educational"
  | "warning"
  | "flat";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
}

const cardVariantStyles: Record<CardVariant, string> = {
  default:
    "bg-surface-card border-border-default shadow-sm",
  interactive:
    "bg-surface-card border-border-default shadow-sm hover:shadow-md hover:border-brand-primary/40 transition-all duration-150 cursor-pointer",
  highlighted:
    "bg-brand-purple-soft/40 border-brand-primary/30 shadow-sm",
  educational:
    "bg-surface-warm border-amber-200/80 shadow-sm",
  warning:
    "bg-semantic-warning-soft border-semantic-warning-border shadow-sm",
  flat:
    "bg-surface-subtle border-transparent",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border text-ink-primary overflow-hidden",
          cardVariantStyles[variant],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

export const CardHeader = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-5 pb-3", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, children, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-bold text-lg text-ink-primary tracking-tight leading-tight", className)}
    {...props}
  >
    {children}
  </h3>
));
CardTitle.displayName = "CardTitle";

export const CardDescription = forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-ink-secondary leading-relaxed", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

export const CardContent = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-5 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-5 pt-0 gap-2 border-t border-border-default/60 mt-4", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";
