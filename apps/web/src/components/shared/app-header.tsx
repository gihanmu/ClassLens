import * as React from "react";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/shared/brand-logo";
import { Button } from "@/components/ui/button";
import { Menu, Sparkles, BookOpen, ChevronDown } from "lucide-react";

export interface AppHeaderProps {
  onToggleSidebar?: () => void;
  assessmentTitle?: string;
  onSelectAssessment?: () => void;
  onRunAnalysis?: () => void;
  isAnalyzing?: boolean;
  className?: string;
}

export function AppHeader({
  onToggleSidebar,
  assessmentTitle = "Checkpoint 1 — Integers & Number Lines",
  onSelectAssessment,
  onRunAnalysis,
  isAnalyzing = false,
  className,
}: AppHeaderProps) {
  return (
    <header
      className={cn(
        "h-16 border-b border-border-default bg-surface-base px-4 sm:px-6 flex items-center justify-between gap-4 sticky top-0 z-20 shadow-xs",
        className
      )}
    >
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-lg text-ink-secondary hover:text-ink-primary hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="md:hidden">
          <BrandLogo size="sm" />
        </div>

        {/* Assessment Switcher Dropdown Trigger */}
        <div className="hidden sm:flex items-center gap-2">
          <button
            type="button"
            onClick={onSelectAssessment}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border-default bg-surface-subtle hover:bg-surface-muted text-xs font-medium text-ink-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
            aria-label="Switch active assessment"
          >
            <BookOpen className="w-3.5 h-3.5 text-brand-primary" aria-hidden="true" />
            <span className="font-semibold">{assessmentTitle}</span>
            <ChevronDown className="w-3.5 h-3.5 text-ink-muted" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {onRunAnalysis && (
          <Button
            variant="coral"
            size="sm"
            onClick={onRunAnalysis}
            isLoading={isAnalyzing}
            className="shadow-xs font-semibold"
          >
            <Sparkles className="w-4 h-4 mr-1.5" aria-hidden="true" />
            {isAnalyzing ? "Analyzing..." : "Run Analysis"}
          </Button>
        )}
      </div>
    </header>
  );
}
