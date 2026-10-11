"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { IconButton } from "./icon-button";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  side?: "left" | "right";
  width?: "sm" | "md" | "lg";
}

const widthStyles = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
};

export function Drawer({
  isOpen,
  onClose,
  title,
  children,
  className,
  side = "right",
  width = "md",
}: DrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => {
        document.body.style.overflow = "";
        window.removeEventListener("keydown", handleKeyDown);
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={typeof title === "string" ? title : "Drawer"}
      className={cn(
        "fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex",
        side === "left" ? "justify-start" : "justify-end"
      )}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={drawerRef}
        className={cn(
          "w-full h-full bg-surface-base border-border-default shadow-2xl flex flex-col focus:outline-none transition-transform duration-250 ease-out",
          side === "left" ? "border-r animate-in slide-in-from-left" : "border-l animate-in slide-in-from-right",
          widthStyles[width],
          className
        )}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-default">
          {typeof title === "string" ? (
            <h3 className="text-base font-semibold text-ink-primary">{title}</h3>
          ) : (
            title
          )}
          <IconButton
            icon={<X className="h-4 w-4" />}
            aria-label="Close drawer"
            variant="neutral"
            size="sm"
            onClick={onClose}
          />
        </div>
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  );
}
