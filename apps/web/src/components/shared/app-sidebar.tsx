import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/shared/brand-logo";
import {
  Users,
  BarChart3,
  Lightbulb,
  FileText,
  Palette,
  LogOut,
  FolderOpen,
  Sparkles,
  FlaskConical,
  LayoutDashboard,
} from "lucide-react";

export type NavItemKey = "dashboard" | "responses" | "insights" | "recommendations" | "resources" | "assessments" | "design-system" | "gemini-test";

export interface NavItem {
  key: NavItemKey;
  label: string;
  icon: React.ElementType;
  badge?: string;
  href?: string;
}

export interface AppSidebarProps {
  currentTab?: NavItemKey;
  onSelectTab?: (key: NavItemKey) => void;
  className?: string;
  onCloseMobile?: () => void;
}

export function AppSidebar({
  currentTab = "dashboard",
  onSelectTab,
  className,
  onCloseMobile,
}: AppSidebarProps) {
  const pathname = usePathname();

  const navItems: NavItem[] = [
    { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { key: "responses", label: "Student Work", icon: Users },
    { key: "insights", label: "Cohort Insights", icon: BarChart3 },
    { key: "recommendations", label: "Teaching Actions", icon: Sparkles },
    { key: "resources", label: "Exit Tickets", icon: FileText },
    { key: "assessments", label: "Assessments", icon: FolderOpen },
  ];

  const isDesignSystemRoute = pathname === "/design-system";
  const isGeminiTestRoute = pathname === "/dev/gemini-test";

  return (
    <aside
      className={cn(
        "w-64 bg-surface-base border-r border-border-default flex flex-col justify-between shrink-0 h-full",
        className
      )}
    >
      {/* Top Branding */}
      <div className="p-6 border-b border-border-default">
        <BrandLogo size="md" showSubtitle />
      </div>

      {/* Main Navigation Links */}
      <nav aria-label="Main navigation" className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
          Diagnostic Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = !isDesignSystemRoute && !isGeminiTestRoute && currentTab === item.key;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => {
                if (onSelectTab) onSelectTab(item.key);
                if (onCloseMobile) onCloseMobile();
              }}
              className={cn(
                "w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary",
                isActive
                  ? "bg-brand-primary text-white shadow-xs font-semibold"
                  : "text-ink-secondary hover:bg-surface-subtle hover:text-ink-primary"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn("w-4 h-4", isActive ? "text-white" : "text-ink-muted")}
                  aria-hidden="true"
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-[11px] font-mono",
                    isActive ? "bg-white/20 text-white font-semibold" : "bg-surface-muted text-ink-secondary"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        <div className="pt-6 px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
          Design & Testing
        </div>
        <Link
          href="/design-system"
          onClick={onCloseMobile}
          className={cn(
            "w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary",
            isDesignSystemRoute
              ? "bg-brand-primary text-white shadow-xs font-semibold"
              : "text-ink-secondary hover:bg-surface-subtle hover:text-ink-primary"
          )}
        >
          <div className="flex items-center gap-3">
            <Palette
              className={cn("w-4 h-4", isDesignSystemRoute ? "text-white" : "text-ink-muted")}
              aria-hidden="true"
            />
            <span>Design System</span>
          </div>
          <span
            className={cn(
              "px-1.5 py-0.5 rounded text-[10px] font-mono",
              isDesignSystemRoute ? "bg-white/20 text-white" : "bg-brand-light text-brand-primary font-semibold"
            )}
          >
            Live
          </span>
        </Link>

        <Link
          href="/dev/gemini-test"
          onClick={onCloseMobile}
          className={cn(
            "w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary mt-1",
            isGeminiTestRoute
              ? "bg-brand-primary text-white shadow-xs font-semibold"
              : "text-ink-secondary hover:bg-surface-subtle hover:text-ink-primary"
          )}
        >
          <div className="flex items-center gap-3">
            <FlaskConical
              className={cn("w-4 h-4", isGeminiTestRoute ? "text-white" : "text-ink-muted")}
              aria-hidden="true"
            />
            <span>Gemini Test Lab</span>
          </div>
          <span
            className={cn(
              "px-1.5 py-0.5 rounded text-[10px] font-mono",
              isGeminiTestRoute ? "bg-white/20 text-white" : "bg-semantic-warning-bg text-semantic-warning-text font-semibold"
            )}
          >
            Gate 4A
          </span>
        </Link>
      </nav>

      {/* Teacher Profile Footer */}
      <div className="p-4 border-t border-border-default bg-surface-subtle/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-accent-coral/15 text-accent-coral font-bold flex items-center justify-center shrink-0 border border-accent-coral/20">
            ER
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-ink-primary truncate">Ms. Evelyn Reed</p>
            <p className="text-[11px] text-ink-muted truncate">6th Grade Math • Period 2</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
