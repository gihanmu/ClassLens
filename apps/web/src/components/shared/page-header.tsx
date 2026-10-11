import * as React from "react";
import { cn } from "@/lib/utils";
import { Typography } from "@/components/ui/typography";

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  breadcrumbs?: { label: string; href?: string; onClick?: () => void }[];
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  badge,
  actions,
  breadcrumbs,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-3 pb-6 border-b border-border-default", className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-ink-muted">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span className="text-ink-muted/60">/</span>}
              {crumb.onClick || crumb.href ? (
                <button
                  type="button"
                  onClick={crumb.onClick}
                  className="hover:text-ink-primary hover:underline transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary rounded"
                >
                  {crumb.label}
                </button>
              ) : (
                <span className="text-ink-primary font-medium">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <Typography variant="h1" className="text-2xl sm:text-3xl font-bold tracking-tight">
              {title}
            </Typography>
            {badge}
          </div>
          {subtitle && (
            <Typography variant="body-sm" className="text-ink-secondary">
              {subtitle}
            </Typography>
          )}
        </div>

        {actions && <div className="flex items-center gap-2.5 flex-wrap shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
