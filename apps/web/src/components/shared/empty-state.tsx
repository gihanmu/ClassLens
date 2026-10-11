import * as React from "react";
import { cn } from "@/lib/utils";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-border-default bg-surface-subtle",
        className
      )}
    >
      {icon && (
        <div className="w-12 h-12 rounded-full bg-brand-light text-brand-primary flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <Typography variant="h3" className="mb-2">
        {title}
      </Typography>
      <Typography variant="body-sm" className="max-w-md mb-6 text-ink-muted">
        {description}
      </Typography>
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
