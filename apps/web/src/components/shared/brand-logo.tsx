import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

export interface BrandLogoProps {
  size?: "sm" | "md" | "lg";
  showSubtitle?: boolean;
  className?: string;
}

const sizeConfig = {
  sm: { img: 28, text: "text-lg", sub: "text-[10px]" },
  md: { img: 36, text: "text-xl", sub: "text-xs" },
  lg: { img: 44, text: "text-2xl", sub: "text-sm" },
};

export function BrandLogo({
  size = "md",
  showSubtitle = false,
  className,
}: BrandLogoProps) {
  const cfg = sizeConfig[size];

  return (
    <div className={cn("inline-flex items-center gap-2.5 select-none", className)}>
      <div className="relative flex items-center justify-center rounded-lg overflow-hidden bg-brand-light p-1 shadow-xs border border-brand-primary/10">
        <Image
          src="/logos/logo.png"
          alt="ClassLens Logo"
          width={cfg.img}
          height={cfg.img}
          className="object-contain"
          priority
        />
      </div>
      <div className="flex flex-col leading-none">
        <span
          className={cn(
            "font-display font-bold tracking-tight text-ink-primary flex items-center gap-1",
            cfg.text
          )}
        >
          Class<span className="text-brand-primary">Lens</span>
        </span>
        {showSubtitle && (
          <span className={cn("font-sans font-medium text-ink-muted uppercase tracking-wider mt-0.5", cfg.sub)}>
            Math Diagnostics
          </span>
        )}
      </div>
    </div>
  );
}
