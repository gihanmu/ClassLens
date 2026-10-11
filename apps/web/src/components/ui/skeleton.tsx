import * as React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shape?: "rectangle" | "circle" | "pill";
}

export function Skeleton({
  className,
  shape = "rectangle",
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-surface-muted",
        shape === "circle" && "rounded-full",
        shape === "pill" && "rounded-full",
        shape === "rectangle" && "rounded-md",
        className
      )}
      aria-hidden="true"
      {...props}
    />
  );
}
