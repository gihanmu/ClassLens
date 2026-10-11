import * as React from "react";
import { ShieldCheck, Info, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export interface OfflineDemoBannerProps {
  className?: string;
  onViewDetails?: () => void;
}

export function OfflineDemoBanner({ className, onViewDetails }: OfflineDemoBannerProps) {
  return (
    <aside
      aria-label="Offline Demonstration Mode Notice"
      className={cn(
        "bg-surface-subtle border-b border-border-default px-4 py-2 text-xs text-ink-secondary flex flex-wrap items-center justify-between gap-2",
        className
      )}
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-1 font-semibold text-brand-primary bg-brand-light px-2 py-0.5 rounded-full text-[11px]">
          <Sparkles className="w-3 h-3 text-brand-primary" aria-hidden="true" />
          Offline Demo Mode
        </span>
        <span className="text-ink-secondary">
          Simulated multi-agent analysis with deterministic SymPy mathematical verification.
        </span>
      </div>
      <div className="flex items-center gap-3 text-[11px] text-ink-muted">
        <span className="inline-flex items-center gap-1 font-medium text-semantic-success">
          <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
          Teacher Override Authority Active
        </span>
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className="text-brand-primary hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary rounded"
          >
            System Info
          </button>
        )}
      </div>
    </aside>
  );
}
