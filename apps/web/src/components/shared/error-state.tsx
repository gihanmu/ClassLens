import * as React from "react";
import { cn } from "@/lib/utils";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "We encountered an issue processing this request. Your data is safe.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl bg-semantic-error-light/40 border border-semantic-error/20",
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-semantic-error-light text-semantic-error flex items-center justify-center mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <Typography variant="h3" className="mb-2 text-semantic-error">
        {title}
      </Typography>
      <Typography variant="body-sm" className="max-w-md mb-6 text-ink-secondary">
        {message}
      </Typography>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
