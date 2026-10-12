"use client";

import * as React from "react";
import { AppShell } from "@/components/shared/app-shell";
import { AiEvaluationView } from "@/components/features/evaluation/AiEvaluationView";

export default function AiEvaluationPage() {
  return (
    <AppShell currentTab="evaluation">
      <div className="max-w-7xl mx-auto py-2">
        <AiEvaluationView />
      </div>
    </AppShell>
  );
}
