import * as React from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { Typography } from "@/components/ui/typography";

export interface LoadingStateProps {
  message?: string;
  submessage?: string;
  className?: string;
}

export function LoadingState({
  message = "Analyzing student work...",
  submessage = "Applying multi-agent visual evidence checks and SymPy verification",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center rounded-xl bg-surface-subtle border border-border-default",
        className
      )}
    >
      <Spinner size="lg" className="mb-4" />
      <Typography variant="h3" className="mb-1 text-ink-primary">
        {message}
      </Typography>
      <Typography variant="body-sm" className="text-ink-muted max-w-sm">
        {submessage}
      </Typography>
    </div>
  );
}
