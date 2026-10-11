import * as React from "react";
import { cn } from "@/lib/utils";
import { Typography } from "@/components/ui/typography";

export interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  badge,
  actions,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center justify-between gap-2.5", className)}>
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <Typography variant="h3" className="text-lg sm:text-xl font-bold text-ink-primary">
            {title}
          </Typography>
          {badge}
        </div>
        {subtitle && (
          <Typography variant="body-sm" className="text-ink-muted text-xs sm:text-sm mt-0.5">
            {subtitle}
          </Typography>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}
