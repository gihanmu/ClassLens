import * as React from "react";
import { cn } from "@/lib/utils";
import { AppSidebar, NavItemKey } from "@/components/shared/app-sidebar";
import { AppHeader } from "@/components/shared/app-header";
import { OfflineDemoBanner } from "@/components/shared/offline-demo-banner";
import { Drawer } from "@/components/ui/drawer";

import { UserProfile } from "@/lib/api";

export interface AppShellProps {
  children: React.ReactNode;
  currentTab?: NavItemKey;
  onSelectTab?: (key: NavItemKey) => void;
  assessmentTitle?: string;
  onSelectAssessment?: () => void;
  onRunAnalysis?: () => void;
  isAnalyzing?: boolean;
  className?: string;
  user?: UserProfile | null;
  onLogout?: () => void;
}

export function AppShell({
  children,
  currentTab = "dashboard",
  onSelectTab,
  assessmentTitle,
  onSelectAssessment,
  onRunAnalysis,
  isAnalyzing,
  className,
  user,
  onLogout,
}: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-surface-canvas flex flex-col font-sans text-ink-primary selection:bg-brand-light selection:text-brand-primary">
      {/* Accessibility Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-primary focus:text-white focus:rounded-md focus:shadow-md"
      >
        Skip to main content
      </a>

      {/* Sticky Top Offline Demo Mode Banner */}
      <OfflineDemoBanner />

      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Persistent Sidebar */}
        <div className="hidden md:block">
          <AppSidebar
            currentTab={currentTab}
            onSelectTab={onSelectTab}
            className="h-full"
            user={user}
            onLogout={onLogout}
          />
        </div>

        {/* Mobile Navigation Drawer */}
        <Drawer
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          title="ClassLens Navigation"
          side="left"
          className="p-0 max-w-xs"
        >
          <AppSidebar
            currentTab={currentTab}
            onSelectTab={onSelectTab}
            onCloseMobile={() => setMobileMenuOpen(false)}
            className="w-full h-full border-r-0"
            user={user}
            onLogout={onLogout}
          />
        </Drawer>

        {/* Content Container */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <AppHeader
            onToggleSidebar={() => setMobileMenuOpen(true)}
            assessmentTitle={assessmentTitle}
            onSelectAssessment={onSelectAssessment}
            onRunAnalysis={onRunAnalysis}
            isAnalyzing={isAnalyzing}
          />

          <main id="main-content" tabIndex={-1} className={cn("flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto", className)}>
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
