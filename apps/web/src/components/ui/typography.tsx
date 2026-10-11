import * as React from "react";
import { cn } from "@/lib/utils";

export type TypographyVariant =
  | "display"
  | "h1"
  | "h2"
  | "h3"
  | "h4"
  | "body-lg"
  | "body"
  | "body-sm"
  | "label"
  | "caption"
  | "mono";

export interface TypographyProps extends React.HTMLAttributes<HTMLElement> {
  variant?: TypographyVariant;
  as?: React.ElementType;
}

const variantMapping: Record<TypographyVariant, { defaultTag: React.ElementType; className: string }> = {
  display: {
    defaultTag: "h1",
    className: "font-display text-4xl sm:text-5xl font-bold tracking-tight text-ink-primary leading-tight",
  },
  h1: {
    defaultTag: "h1",
    className: "font-display text-3xl sm:text-4xl font-bold tracking-tight text-ink-primary leading-snug",
  },
  h2: {
    defaultTag: "h2",
    className: "font-display text-2xl sm:text-3xl font-bold text-ink-primary leading-snug",
  },
  h3: {
    defaultTag: "h3",
    className: "font-display text-xl sm:text-2xl font-semibold text-ink-primary leading-normal",
  },
  h4: {
    defaultTag: "h4",
    className: "font-display text-lg font-semibold text-ink-primary leading-normal",
  },
  "body-lg": {
    defaultTag: "p",
    className: "font-sans text-lg text-ink-primary leading-relaxed",
  },
  body: {
    defaultTag: "p",
    className: "font-sans text-base text-ink-primary leading-normal",
  },
  "body-sm": {
    defaultTag: "p",
    className: "font-sans text-sm text-ink-secondary leading-normal",
  },
  label: {
    defaultTag: "span",
    className: "font-sans text-xs font-semibold uppercase tracking-wider text-ink-secondary",
  },
  caption: {
    defaultTag: "span",
    className: "font-sans text-xs text-ink-muted leading-tight",
  },
  mono: {
    defaultTag: "code",
    className: "font-mono text-sm text-ink-primary bg-surface-muted px-1.5 py-0.5 rounded-xs",
  },
};

export function Typography({
  variant = "body",
  as,
  className,
  children,
  ...props
}: TypographyProps) {
  const config = variantMapping[variant];
  const Component = as || config.defaultTag;

  return (
    <Component className={cn(config.className, className)} {...props}>
      {children}
    </Component>
  );
}
