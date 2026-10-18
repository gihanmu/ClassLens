import * as React from "react";
import { ShieldCheck, Info, Sparkles, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export interface OfflineDemoBannerProps {
  className?: string;
  onViewDetails?: () => void;
}

interface SystemHealth {
  ai_mode?: string;
  is_live_authorized?: boolean;
  gemini_model?: string;
  google_cloud_project?: string;
}

export function OfflineDemoBanner({ className, onViewDetails }: OfflineDemoBannerProps) {
  const [health, setHealth] = React.useState<SystemHealth | null>(null);

  React.useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
        const res = await fetch(`${apiUrl}/health`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setHealth(data);
        }
      } catch {
        // Fallback to default offline mode on network error
      }
    };
    fetchHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  const isLive = Boolean(health?.is_live_authorized);
  const modelName = health?.gemini_model || "gemini-3.8-flash";

  return (
    <aside
      aria-label="Diagnostic Service Status"
      className={cn(
        "border-b px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-2 transition-colors",
        isLive ? "bg-emerald-50/70 border-emerald-200 text-ink-secondary" : "bg-surface-subtle border-border-default text-ink-secondary",
        className
      )}
    >
      <div className="flex items-center gap-2 flex-wrap">
        {isLive ? (
          <>
            <span className="inline-flex items-center gap-1.5 font-semibold text-emerald-800 bg-emerald-100/90 px-2.5 py-0.5 rounded-full text-[11px] border border-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" aria-hidden="true" />
              Live AI Diagnostics
            </span>
            <span className="text-ink-secondary font-medium">
              Multimodal Handwriting Evaluation & Formal Verification Active
            </span>
          </>
        ) : (
          <>
            <span className="inline-flex items-center gap-1.5 font-semibold text-brand-primary bg-brand-light px-2.5 py-0.5 rounded-full text-[11px] border border-brand-primary/20">
              <Sparkles className="w-3 h-3 text-brand-primary" aria-hidden="true" />
              Diagnostic Sandbox
            </span>
            <span className="text-ink-secondary font-medium">
              Deterministic Mathematical Verification (Offline Evaluation Mode)
            </span>
          </>
        )}
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
