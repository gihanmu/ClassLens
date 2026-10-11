"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Info, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";

export type AlertVariant = "info" | "success" | "warning" | "error";

export interface AlertProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  variant?: AlertVariant;
  title?: React.ReactNode;
  icon?: React.ReactNode;
}

const alertConfig: Record<
  AlertVariant,
  {
    container: string;
    iconColor: string;
    defaultIcon: React.ComponentType<{ className?: string }>;
  }
> = {
  info: {
    container: "bg-semantic-info-soft border-semantic-info-border text-ink-primary",
    iconColor: "text-semantic-info",
    defaultIcon: Info,
  },
  success: {
    container: "bg-semantic-success-soft border-semantic-success-border text-ink-primary",
    iconColor: "text-semantic-success",
    defaultIcon: CheckCircle2,
  },
  warning: {
    container: "bg-semantic-warning-soft border-semantic-warning-border text-ink-primary",
    iconColor: "text-semantic-warning",
    defaultIcon: AlertTriangle,
  },
  error: {
    container: "bg-semantic-error-soft border-semantic-error-border text-ink-primary",
    iconColor: "text-semantic-error",
    defaultIcon: AlertCircle,
  },
};

export function Alert({
  variant = "info",
  title,
  icon,
  children,
  className,
  ...props
}: AlertProps) {
  const config = alertConfig[variant];
  const IconComponent = config.defaultIcon;

  return (
    <div
      role="alert"
      className={cn(
        "flex gap-3 p-4 rounded-md border text-sm leading-relaxed shadow-2xs",
        config.container,
        className
      )}
      {...props}
    >
      <div className={cn("shrink-0 pt-0.5", config.iconColor)} aria-hidden="true">
        {icon || <IconComponent className="h-5 w-5" />}
      </div>
      <div className="flex flex-col gap-0.5">
        {title && <h4 className="font-bold text-[14px] leading-tight">{title}</h4>}
        <div className="text-[13px] text-ink-secondary">{children}</div>
      </div>
    </div>
  );
}
