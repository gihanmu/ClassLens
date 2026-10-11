import * as React from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

export interface FilterOption {
  id: string;
  label: string;
  count?: number;
}

export interface FilterBarProps {
  options: FilterOption[];
  selectedId: string;
  onSelect: (id: string) => void;
  searchValue?: string;
  onSearchChange?: (val: string) => void;
  searchPlaceholder?: string;
  className?: string;
}

export function FilterBar({
  options,
  selectedId,
  onSelect,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search student ID or error...",
  className,
}: FilterBarProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3", className)}>
      {/* Filter Pills */}
      <div
        role="tablist"
        aria-label="Filter responses"
        className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none"
      >
        {options.map((opt) => {
          const isSelected = opt.id === selectedId;
          return (
            <button
              key={opt.id}
              role="tab"
              aria-selected={isSelected}
              onClick={() => onSelect(opt.id)}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary",
                isSelected
                  ? "bg-ink-primary text-white shadow-xs font-semibold"
                  : "bg-surface-subtle text-ink-secondary hover:bg-surface-muted hover:text-ink-primary border border-border-default"
              )}
            >
              <span>{opt.label}</span>
              {opt.count !== undefined && (
                <span
                  className={cn(
                    "px-1.5 py-0.2 rounded-full text-[10px] font-mono",
                    isSelected ? "bg-white/20 text-white" : "bg-ink-primary/10 text-ink-secondary"
                  )}
                >
                  {opt.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Search Input */}
      {onSearchChange && (
        <div className="relative w-full sm:w-64 shrink-0">
          <Search className="w-4 h-4 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="search"
            value={searchValue || ""}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-border-default bg-surface-base text-ink-primary placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
          />
        </div>
      )}
    </div>
  );
}
