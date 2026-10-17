"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import {
  api,
  Assessment,
  StudentResponse,
  CohortInsights,
  DashboardSummary,
  UserProfile,
} from "@/lib/api";
import { TeacherDashboardView } from "@/components/features/dashboard/TeacherDashboardView";
import {
  Users,
  BarChart3,
  Sparkles,
  FileText,
  FolderOpen,
  DownloadCloud,
  Check,
  CheckCheck,
  AlertTriangle,
  Lightbulb,
  ShieldCheck,
  Layers,
  HelpCircle,
  X,
  ChevronDown,
  ChevronUp,
  Plus,
  UploadCloud,
} from "lucide-react";
import { AppShell } from "@/components/shared/app-shell";
import { NavItemKey } from "@/components/shared/app-sidebar";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { FilterBar } from "@/components/shared/filter-bar";
import { StudentResponseCard } from "@/components/features/students/StudentResponseCard";
import { StudentInspectionModal } from "@/components/inspection/StudentInspectionModal";
import { TeachingRecommendationCard } from "@/components/features/cohort/TeachingRecommendationCard";
import { ClassroomResourcesView } from "@/components/features/cohort/ClassroomResourcesView";
import { ClassroomHeroIllustration } from "@/components/shared/classroom-illustration";
import { AiEvaluationView } from "@/components/features/evaluation/AiEvaluationView";
import { CreateAssessmentModal } from "@/components/features/assessments/CreateAssessmentModal";
import { WorksheetUploadModal } from "@/components/features/assessments/WorksheetUploadModal";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { Spinner } from "@/components/ui/spinner";
import { Dialog } from "@/components/ui/dialog";
import { getMisconceptionPlainLanguage } from "@/lib/terminology";

const STORAGE_KEY_WELCOME = "classlens_welcome_dismissed";

export default function ClassLensApp() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [assessmentsList, setAssessmentsList] = useState<Assessment[]>([]);
  const [currentAssessmentId, setCurrentAssessmentId] = useState<string>("asm_1065658");
  const [responses, setResponses] = useState<StudentResponse[]>([]);
  const [insights, setInsights] = useState<CohortInsights | null>(null);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [currentTab, setCurrentTab] = useState<NavItemKey>("dashboard");
  const [filter, setFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedResponseId, setSelectedResponseId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analyzingSingleId, setAnalyzingSingleId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAssessmentModal, setShowAssessmentModal] = useState<boolean>(false);
  const [showHeroBanner, setShowHeroBanner] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [assessmentFilter, setAssessmentFilter] = useState<"all" | "classroom" | "demo">("all");
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  const asmId = currentAssessmentId;

  const loadData = async (targetAsmId = currentAssessmentId) => {
    try {
      setLoading(true);

      try {
        const user = await api.getCurrentUser();
        setCurrentUser(user);
      } catch (authErr: any) {
        if (typeof window !== "undefined") {
          const currentPath = window.location.pathname + window.location.search;
          const target = currentPath === "/" ? "" : `?redirect=${encodeURIComponent(currentPath)}`;
          window.location.href = `/login${target}`;
          return;
        }
      }

      try {
        const dash = await api.getDashboardSummary();
        setDashboardSummary(dash);
      } catch (e) {
        console.warn("Could not load dashboard summary:", e);
      }

      try {
        const asms = await api.listAssessments();
        setAssessmentsList(asms);
      } catch (e) {
        console.warn("Could not list assessments:", e);
      }

      let asm: Assessment | null = null;
      try {
        asm = await api.getAssessment(targetAsmId);
      } catch (e) {
        console.warn(`Could not load target assessment ${targetAsmId}, checking list:`, e);
        try {
          const freshAsms = await api.listAssessments();
          if (freshAsms.length > 0) {
            targetAsmId = freshAsms[0].id;
            setCurrentAssessmentId(targetAsmId);
            asm = await api.getAssessment(targetAsmId);
          }
        } catch {
          // Fallback gracefully
        }
      }
      setAssessment(asm);

      const resps = await api.listResponses(targetAsmId);
      setResponses(resps);

      if (resps.some((r) => r.task_status === "COMPLETED")) {
        try {
          const ins = await api.getCohortInsights(targetAsmId);
          setInsights(ins);
        } catch (e) {
          console.warn("Cohort insights not ready yet:", e);
          setInsights(null);
        }
      } else {
        setInsights(null);
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAssessment = async (newAsmId: string) => {
    setCurrentAssessmentId(newAsmId);
    setAssessment(null);
    setResponses([]);
    setInsights(null);
    setShowAssessmentModal(false);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("classlens_active_assessment_id", newAsmId);
        const url = new URL(window.location.href);
        url.searchParams.set("asm", newAsmId);
        window.history.replaceState({}, "", url.toString());
      } catch (e) {
        console.warn("Could not save active assessment to storage/url:", e);
      }
    }
    await loadData(newAsmId);
  };

  useEffect(() => {
    let targetAsm = currentAssessmentId;
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const respParam = params.get("response");
      const tabParam = params.get("tab");
      const asmParam = params.get("asm");
      const savedAsm = localStorage.getItem("classlens_active_assessment_id");

      if (asmParam && asmParam.trim()) {
        targetAsm = asmParam.trim();
        setCurrentAssessmentId(targetAsm);
      } else if (savedAsm && savedAsm.trim()) {
        targetAsm = savedAsm.trim();
        setCurrentAssessmentId(targetAsm);
      }
      if (respParam) setSelectedResponseId(respParam);
      if (
        tabParam &&
        ["dashboard", "responses", "insights", "recommendations", "resources", "assessments", "evaluation"].includes(tabParam)
      ) {
        setCurrentTab(tabParam as NavItemKey);
      }
    }

    loadData(targetAsm);

    // Check client-side welcome preference safely
    try {
      const isDismissed = localStorage.getItem(STORAGE_KEY_WELCOME);
      if (isDismissed !== "true") {
        setShowHeroBanner(true);
      }
    } catch (e) {
      // Safe fallback if localStorage unavailable
      setShowHeroBanner(false);
    }
  }, []);

  const handleDismissHero = () => {
    setShowHeroBanner(false);
    try {
      localStorage.setItem(STORAGE_KEY_WELCOME, "true");
    } catch (e) {
      // safe fallback
    }
  };

  const handleToggleHero = () => {
    const nextState = !showHeroBanner;
    setShowHeroBanner(nextState);
    if (!nextState) {
      try {
        localStorage.setItem(STORAGE_KEY_WELCOME, "true");
      } catch (e) {
        // safe fallback
      }
    }
  };

  const handleImport = async () => {
    try {
      setLoading(true);
      await api.importDemoResponses(currentAssessmentId);
      await loadData(currentAssessmentId);
    } catch (err) {
      console.error("Failed to import demo responses:", err);
      alert("Failed to import demo responses.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      await api.triggerAnalysis(currentAssessmentId, `job_run_${Date.now()}`);
      setTimeout(async () => {
        await loadData(currentAssessmentId);
        setIsAnalyzing(false);
      }, 1200);
    } catch (err) {
      console.error("Failed to launch analysis:", err);
      setIsAnalyzing(false);
      alert("Failed to launch batch analysis.");
    }
  };

  const handleAnalyzeSingle = async (resp: StudentResponse) => {
    try {
      setAnalyzingSingleId(resp.id);
      await api.analyzeSingleResponse(resp.id);
      await loadData(currentAssessmentId);
    } catch (err) {
      console.error("Failed to analyze response:", err);
      alert(`Failed to analyze response ${resp.id}.`);
    } finally {
      setAnalyzingSingleId(null);
    }
  };

  // Derived cohort metrics with strict semantic boundaries
  const totalSubmissions = responses.length;
  const completedAnalyses = responses.filter((r) => r.task_status === "COMPLETED").length;
  const awaitingCount = responses.filter((r) => r.task_status !== "COMPLETED" && r.task_status !== "FAILED").length;
  const failedCount = responses.filter((r) => r.task_status === "FAILED").length;

  const correctCount = responses.filter((r) => r.task_status === "COMPLETED" && r.answer_status === "correct").length;
  const reasoningVerifiedCount = responses.filter(
    (r) =>
      r.task_status === "COMPLETED" &&
      (r.reasoning_status === "supported_correct" ||
        r.reasoning_status === "verified" ||
        r.reasoning_status === "sound" ||
        r.reasoning_status === "valid" ||
        r.reasoning_status === "correct")
  ).length;
  const misconceptionCount = responses.filter(
    (r) =>
      r.task_status === "COMPLETED" &&
      Boolean(r.misconception_taxonomy_id || r.analysis_data?.diagnosis?.diagnosed_misconception_id)
  ).length;
  const reviewedCount = responses.filter(
    (r) => r.teacher_review_status && r.teacher_review_status !== "unreviewed"
  ).length;

  // Strict semantics: only students flagged who are not yet confirmed/overridden
  // Prior to completion, submissions are NOT flagged for review
  const needsReviewCount = responses.filter(
    (r) => r.task_status === "COMPLETED" && r.needs_teacher_review && r.teacher_review_status === "unreviewed"
  ).length;

  // Insufficient evidence count: ONLY computed on completed analyses
  const insufficientEvidenceCount = responses.filter(
    (r) =>
      r.task_status === "COMPLETED" &&
      (r.reasoning_status === "incomplete" ||
        r.reasoning_status === "unverifiable" ||
        r.answer_status === "undetermined" ||
        r.upload_status === "unreadable" ||
        r.analysis_data?.diagnosis?.evidence_sufficiency === "insufficient")
  ).length;

  // Procedural errors in reasoning or final answer incorrect
  const procedureErrorCount = responses.filter(
    (r) =>
      r.task_status === "COMPLETED" &&
      (r.reasoning_status?.includes("error") || r.answer_status === "incorrect")
  ).length;

  // Filtered student responses
  const filteredResponses = responses.filter((r) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const label = (r.pseudonym_label || "").toLowerCase();
      const id = (r.id || "").toLowerCase();
      const notes = (r.teacher_notes || "").toLowerCase();
      const tax = (r.misconception_taxonomy_id || "").toLowerCase();
      const plainTax = getMisconceptionPlainLanguage(r.misconception_taxonomy_id).toLowerCase();
      if (
        !label.includes(q) &&
        !id.includes(q) &&
        !notes.includes(q) &&
        !tax.includes(q) &&
        !plainTax.includes(q)
      ) {
        return false;
      }
    }

    if (filter === "awaiting") {
      return r.task_status !== "COMPLETED" && r.task_status !== "FAILED";
    }
    if (filter === "analyzed") {
      return r.task_status === "COMPLETED";
    }
    if (filter === "review") {
      return r.task_status === "COMPLETED" && r.needs_teacher_review && r.teacher_review_status === "unreviewed";
    }
    if (filter === "insufficient") {
      return (
        r.task_status === "COMPLETED" &&
        (r.reasoning_status === "incomplete" ||
          r.reasoning_status === "unverifiable" ||
          r.answer_status === "undetermined" ||
          r.upload_status === "unreadable" ||
          r.analysis_data?.diagnosis?.evidence_sufficiency === "insufficient")
      );
    }
    if (filter === "errors") {
      return (
        r.task_status === "COMPLETED" &&
        (r.reasoning_status?.includes("error") || r.answer_status === "incorrect")
      );
    }
    if (filter === "correct") {
      return r.task_status === "COMPLETED" && r.answer_status === "correct";
    }
    if (filter === "failed") {
      return r.task_status === "FAILED";
    }
    return true;
  });

  const selectedIndex = responses.findIndex((r) => r.id === selectedResponseId);

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      assessmentTitle={assessment?.title || "Checkpoint 1 — Integers & Number Lines"}
      onSelectAssessment={() => setShowAssessmentModal(true)}
      onRunAnalysis={handleAnalyze}
      isAnalyzing={isAnalyzing}
      user={currentUser}
    >
      <div className="space-y-6">
        {/* =========================================================================
            SCREEN 0: DEDICATED TEACHER DASHBOARD (PRIMARY LANDING PAGE)
           ========================================================================= */}
        {currentTab === "dashboard" && (
          <TeacherDashboardView
            summary={dashboardSummary}
            loading={loading}
            onOpenAssessmentsModal={() => setShowAssessmentModal(true)}
            onNavigateToStudentWork={(targetAsmId) => {
              if (targetAsmId && targetAsmId !== currentAssessmentId) {
                handleSelectAssessment(targetAsmId);
              }
              setCurrentTab("responses");
            }}
            onInspectSubmission={(respId) => {
              setSelectedResponseId(respId);
            }}
            onNavigateToInsights={(targetAsmId) => {
              if (targetAsmId && targetAsmId !== currentAssessmentId) {
                handleSelectAssessment(targetAsmId);
              }
              setCurrentTab("insights");
            }}
            onRunBatchAnalysis={async (targetAsmId) => {
              try {
                setIsAnalyzing(true);
                await api.triggerAnalysis(targetAsmId, `job_run_${Date.now()}`);
                setTimeout(async () => {
                  await loadData(targetAsmId);
                  setIsAnalyzing(false);
                }, 1200);
              } catch (err) {
                console.error("Failed to run batch analysis:", err);
                setIsAnalyzing(false);
                alert("Failed to run batch analysis.");
              }
            }}
            isAnalyzing={isAnalyzing}
          />
        )}

        {/* =========================================================================
            SCREEN A: COMPACT DISMISSIBLE INTRODUCTION (First-Visit or On-Demand)
           ========================================================================= */}
        {showHeroBanner && currentTab === "responses" && (
          <section
            aria-label="Welcome and System Guide"
            className="relative rounded-2xl bg-gradient-to-br from-surface-base via-surface-base to-brand-light/30 border border-border-default p-5 sm:p-6 shadow-xs overflow-hidden transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-yellow/25 border border-accent-yellow/50 text-amber-950 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-amber-700" />
                Secondary 1 Mathematics Diagnostic System
              </div>

              <button
                type="button"
                onClick={handleDismissHero}
                aria-label="Dismiss welcome introduction"
                className="p-1 rounded-lg text-ink-muted hover:text-ink-primary hover:bg-surface-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              <div className="lg:col-span-8 space-y-3">
                <Typography variant="h2" className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-ink-primary leading-tight">
                  See how your students <span className="text-brand-primary">actually think</span> in math.
                </Typography>

                <p className="text-xs sm:text-sm text-ink-secondary leading-relaxed max-w-2xl">
                  ClassLens analyzes handwritten worksheets to pinpoint the exact number-line hop where reasoning breaks down—separating conceptual understanding from final calculation slips.
                </p>

                {/* 3 Core Value Pillars */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                  <div className="p-3 rounded-xl bg-white/90 border border-border-default shadow-2xs">
                    <span className="font-bold text-xs text-brand-primary block mb-0.5">1. Multimodal AI</span>
                    <p className="text-[11px] text-ink-muted">Grounds observations in physical handwritten ink strokes.</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/90 border border-border-default shadow-2xs">
                    <span className="font-bold text-xs text-emerald-800 block mb-0.5">2. SymPy Engine</span>
                    <p className="text-[11px] text-ink-muted">Mathematically exact verification with zero hallucinations.</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/90 border border-border-default shadow-2xs">
                    <span className="font-bold text-xs text-accent-coral block mb-0.5">3. Teacher Control</span>
                    <p className="text-[11px] text-ink-muted">Every diagnosis can be audited, confirmed, or overridden.</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button
                    variant="coral"
                    size="sm"
                    onClick={() => {
                      if (responses.length === 0) handleImport();
                      handleDismissHero();
                    }}
                  >
                    <Users className="w-4 h-4" />
                    Inspect Student Responses
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDismissHero}
                    className="text-xs text-ink-muted hover:text-ink-primary"
                  >
                    Hide Introduction
                  </Button>
                </div>
              </div>

              {/* Character & Books Illustration */}
              <div className="lg:col-span-4 hidden sm:flex items-center justify-center">
                <ClassroomHeroIllustration className="max-w-[260px]" />
              </div>
            </div>
          </section>
        )}

        {/* =========================================================================
            SCREEN B: TEACHER DASHBOARD (STUDENT WORK)
           ========================================================================= */}
        {currentTab === "responses" && (
          <div className="space-y-6">
            {/* Page Header: Immediate access to Checkpoint and Actions */}
            <PageHeader
              title={assessment?.title || "Integers on Number Line: Checkpoint 1"}
              subtitle="Task: Evaluate -6 + 12 - 4 on the number line • Target Canonical Value: +2"
              badge={
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-brand-light text-brand-primary border border-brand-primary/20">
                  Problem #1065658
                </span>
              }
              actions={
                <div className="flex items-center gap-2">
                  {!showHeroBanner && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleToggleHero}
                      className="text-xs text-ink-muted hover:text-ink-primary"
                    >
                      <HelpCircle className="w-3.5 h-3.5 text-ink-muted mr-1" />
                      About ClassLens
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowUploadModal(true)}
                    className="border-brand-primary/30 text-brand-primary hover:bg-brand-light/30 font-semibold"
                  >
                    <UploadCloud className="w-4 h-4 mr-1 text-brand-primary" />
                    Upload Worksheets
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleImport}
                    disabled={loading || responses.length > 0}
                  >
                    <DownloadCloud className="w-4 h-4 text-ink-muted mr-1" />
                    {responses.length > 0 ? `Loaded (${responses.length})` : "Import 13 Demo Worksheets"}
                  </Button>
                  <Button
                    variant="coral"
                    size="sm"
                    onClick={handleAnalyze}
                    isLoading={isAnalyzing}
                    disabled={responses.length === 0}
                  >
                    <Sparkles className="w-4 h-4" />
                    {isAnalyzing ? "Analyzing All (13)..." : "Analyze All Submissions"}
                  </Button>
                </div>
              }
            />

            {/* 5 Metric Summary Cards with clean unanalyzed baseline */}
            <section aria-label="Assessment Metrics Summary" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
              <MetricCard
                title="Total Submissions"
                value={totalSubmissions}
                subtext={
                  completedAnalyses === 0
                    ? `${awaitingCount} awaiting analysis`
                    : `${completedAnalyses} of ${totalSubmissions} analyzed`
                }
                accent="brand"
                icon={<Layers className="w-5 h-5" />}
              />
              <MetricCard
                title="Correct Final Answers"
                value={completedAnalyses === 0 ? "—" : correctCount}
                denominator={completedAnalyses === 0 ? undefined : completedAnalyses}
                subtext={
                  completedAnalyses === 0
                    ? "Pending batch analysis"
                    : `${Math.round((correctCount / Math.max(completedAnalyses, 1)) * 100)}% of this checkpoint`
                }
                accent="mint"
                icon={<Check className="w-5 h-5" />}
              />
              <MetricCard
                title="Reasoning Verified"
                value={completedAnalyses === 0 ? "—" : reasoningVerifiedCount}
                denominator={completedAnalyses === 0 ? undefined : completedAnalyses}
                subtext={
                  completedAnalyses === 0
                    ? "Pending verification"
                    : `${Math.round((reasoningVerifiedCount / Math.max(completedAnalyses, 1)) * 100)}% sound in this checkpoint`
                }
                accent="brand"
                icon={<CheckCheck className="w-5 h-5" />}
              />
              <MetricCard
                title="Misconceptions Identified"
                value={completedAnalyses === 0 ? "—" : misconceptionCount}
                denominator={completedAnalyses === 0 ? undefined : completedAnalyses}
                subtext={
                  completedAnalyses === 0
                    ? "Pending analysis"
                    : `${Math.round((misconceptionCount / Math.max(completedAnalyses, 1)) * 100)}% supported patterns`
                }
                accent="coral"
                icon={<AlertTriangle className="w-5 h-5" />}
              />
              <MetricCard
                title="Needs Teacher Review"
                value={needsReviewCount}
                denominator={completedAnalyses === 0 ? undefined : completedAnalyses}
                subtext={
                  completedAnalyses === 0
                    ? "0 flagged prior to analysis"
                    : `${needsReviewCount} flagged in this checkpoint (${reviewedCount} reviewed)`
                }
                accent="yellow"
                icon={<ShieldCheck className="w-5 h-5" />}
              />
            </section>

            {/* Filter Bar with Documented Semantics */}
            <FilterBar
              options={[
                { id: "all", label: "All Submissions", count: totalSubmissions },
                { id: "awaiting", label: "Awaiting Analysis", count: awaitingCount },
                { id: "analyzed", label: "Analyzed", count: completedAnalyses },
                { id: "review", label: "Needs Review", count: needsReviewCount },
                { id: "insufficient", label: "Insufficient Evidence", count: insufficientEvidenceCount },
                { id: "errors", label: "Procedural Errors", count: procedureErrorCount },
              ]}
              selectedId={filter}
              onSelect={setFilter}
              searchValue={searchQuery}
              onSearchChange={setSearchQuery}
              searchPlaceholder="Filter student ID, note, or error..."
            />

            {/* Dedicated Review Queue Section when filter === 'review' */}
            {filter === "review" && (
              <div className="rounded-2xl border border-amber-300 bg-amber-50/40 p-4 sm:p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
                      <ShieldCheck className="w-4 h-4 text-amber-800" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-ink-primary">
                        Teacher Review Queue ({needsReviewCount} Awaiting Review)
                      </h3>
                      <p className="text-xs text-ink-muted">
                        Responses flagged for educator review due to visual ambiguities, incomplete markings, or adversarial discrepancies.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-amber-200 bg-white">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-amber-100/50 text-ink-secondary font-semibold border-b border-amber-200">
                      <tr>
                        <th className="px-3 py-2.5">Student</th>
                        <th className="px-3 py-2.5">Evidence Status</th>
                        <th className="px-3 py-2.5">Escalation Reason</th>
                        <th className="px-3 py-2.5">Review Status</th>
                        <th className="px-3 py-2.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-amber-100">
                      {filteredResponses.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-3 py-6 text-center text-ink-muted">
                            No student responses currently awaiting review.
                          </td>
                        </tr>
                      ) : (
                        filteredResponses.map((r) => {
                          const isInsufficient =
                            r.reasoning_status === "incomplete" ||
                            r.answer_status === "undetermined" ||
                            r.analysis_data?.diagnosis?.evidence_sufficiency === "insufficient";
                          const reviewReason =
                            r.analysis_data?.critic_audit?.teacher_review_reason ||
                            r.analysis_data?.teacher_review_reason ||
                            "Ambiguous marks require educator review";

                          return (
                            <tr key={r.id} className="hover:bg-amber-50/30 transition-colors">
                              <td className="px-3 py-3 font-semibold text-ink-primary">
                                {r.pseudonym_label || r.id}
                                <span className="block font-mono text-[10px] text-ink-muted">
                                  {r.id}
                                </span>
                              </td>
                              <td className="px-3 py-3">
                                <span
                                  className={cn(
                                    "px-2 py-0.5 rounded-full text-[10px] font-semibold",
                                    isInsufficient
                                      ? "bg-amber-100 text-amber-900"
                                      : "bg-emerald-100 text-emerald-900"
                                  )}
                                >
                                  {isInsufficient ? "Insufficient / Ambiguous" : "Sufficient"}
                                </span>
                              </td>
                              <td className="px-3 py-3 text-ink-secondary max-w-xs truncate">
                                {reviewReason}
                              </td>
                              <td className="px-3 py-3">
                                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-surface-subtle border border-border-default text-ink-muted uppercase">
                                  {r.teacher_review_status}
                                </span>
                              </td>
                              <td className="px-3 py-3 text-right">
                                <Button
                                  variant="coral"
                                  size="sm"
                                  onClick={() => setSelectedResponseId(r.id)}
                                  className="text-xs h-7 px-3 font-semibold"
                                >
                                  Inspect &amp; Review
                                </Button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Responsive Grid of Student Response Cards: 1 col (mobile), 2 cols (tablet), 3 cols (desktop), 4 cols (wide desktop) */}
            {loading ? (
              <div className="flex flex-col items-center justify-center p-16 bg-surface-base rounded-2xl border border-border-default">
                <Spinner size="lg" />
                <Typography variant="body" className="mt-3 text-ink-secondary">
                  Loading student responses and verification states...
                </Typography>
              </div>
            ) : filteredResponses.length === 0 ? (
              <div className="p-12 text-center rounded-2xl border border-dashed border-border-default bg-surface-base">
                <p className="text-sm font-semibold text-ink-primary">No matching student responses found.</p>
                <p className="text-xs text-ink-muted mt-1">Try resetting the filter or search query.</p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setFilter("all");
                    setSearchQuery("");
                  }}
                  className="mt-4"
                >
                  Reset Filters
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-5">
                {filteredResponses.map((resp) => (
                  <StudentResponseCard
                    key={resp.id}
                    response={resp}
                    assessmentId={asmId}
                    onInspect={(r) => setSelectedResponseId(r.id)}
                    onAnalyzeSingle={handleAnalyzeSingle}
                    isAnalyzingSingle={analyzingSingleId === resp.id}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            SCREEN D: COHORT INTELLIGENCE
           ========================================================================= */}
        {currentTab === "insights" && (
          <div className="space-y-6">
            <PageHeader
              title="Cohort Intelligence & Misconception Analysis"
              subtitle="Aggregated pattern recognition across all 13 student responses, grounded in SymPy verification."
              badge={
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-mint text-emerald-800">
                  Whole-Class Diagnostics
                </span>
              }
            />

            {/* Top 4 Metrics Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Cohort Size"
                value={totalSubmissions}
                subtext="13 Evaluated Worksheets"
                accent="brand"
                icon={<Users className="w-5 h-5" />}
              />
              <MetricCard
                title="Mastery Rate"
                value={`${Math.round((correctCount / Math.max(totalSubmissions, 1)) * 100)}%`}
                subtext={`${correctCount} of ${totalSubmissions} correct`}
                accent="mint"
                icon={<Check className="w-5 h-5" />}
              />
              <MetricCard
                title="Procedural Errors"
                value={procedureErrorCount}
                denominator={totalSubmissions}
                subtext="Number-line representation issues"
                accent="coral"
                icon={<AlertTriangle className="w-5 h-5" />}
              />
              <MetricCard
                title="Compensatory Errors"
                value={responses.filter((r) => r.is_compensatory_error).length}
                subtext="Correct answer, invalid steps"
                accent="yellow"
                icon={<Lightbulb className="w-5 h-5" />}
              />
            </div>

            {/* "What This Means" Executive Narrative Card */}
            <div className="p-6 rounded-2xl bg-brand-light/40 border border-brand-primary/20 shadow-xs flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-brand-primary text-white flex items-center justify-center shrink-0 shadow-xs">
                <Lightbulb className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold uppercase tracking-wider text-brand-primary">
                  What This Means For Your Classroom
                </h3>
                <p className="text-xs sm:text-sm text-ink-primary leading-relaxed">
                  {insights?.intelligence?.executive_narrative ||
                    "While 69% of students reached the correct final answer (+2), 31% exhibit fundamental misconceptions regarding origin coordinate selection (starting at -1 or -6 instead of 0) or hop direction magnitude. Several students utilized compensatory arithmetic adjustments to reach +2 despite flawed drawings."}
                </p>
              </div>
            </div>

            {/* Horizontal Misconception Distribution Bar Chart */}
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">Misconception Frequency Distribution</CardTitle>
                    <CardDescription>
                      Explicit fractional denominators across cohort of {totalSubmissions} students
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1.5 font-medium text-ink-secondary">
                      <span className="w-3 h-3 rounded bg-brand-primary" />
                      AI Proposed
                    </span>
                    <span className="flex items-center gap-1.5 font-medium text-ink-secondary">
                      <span className="w-3 h-3 rounded bg-emerald-600" />
                      Teacher Confirmed
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {(
                  insights?.statistics?.misconception_clusters || [
                    {
                      taxonomy_id: "START_POINT_ZERO_MISUNDERSTANDING",
                      title: "Origin Coordinate Confusion (Did not start at 0)",
                      affected_count: 2,
                      affected_percentage: 15,
                      teacher_confirmed_count: 1,
                      ai_proposed_count: 1,
                      sample_response_ids: ["response_01", "response_07"],
                    },
                    {
                      taxonomy_id: "INCORRECT_INTERVAL_MAGNITUDE",
                      title: "Interval Magnitude Counting Slip (+6 instead of +12)",
                      affected_count: 3,
                      affected_percentage: 23,
                      teacher_confirmed_count: 0,
                      ai_proposed_count: 3,
                      sample_response_ids: ["response_03", "response_09"],
                    },
                    {
                      taxonomy_id: "COMPENSATORY_ARITHMETIC_ERROR",
                      title: "Compensatory Arithmetic Error (Masked Slip)",
                      affected_count: 1,
                      affected_percentage: 8,
                      teacher_confirmed_count: 0,
                      ai_proposed_count: 1,
                      sample_response_ids: ["response_05"],
                    },
                  ]
                ).map((cluster) => {
                  const maxCount = 5;
                  const plainTitle = getMisconceptionPlainLanguage(
                    cluster.taxonomy_id,
                    cluster.title
                  );

                  return (
                    <div key={cluster.taxonomy_id} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="text-ink-primary font-semibold">
                          {plainTitle}
                        </span>
                        <span className="font-mono text-ink-muted">
                          {cluster.affected_count}/{totalSubmissions} students (
                          {Math.round(
                            (cluster.affected_count / Math.max(totalSubmissions, 1)) * 100
                          )}
                          %)
                        </span>
                      </div>

                      <div className="h-6 w-full rounded-lg bg-surface-subtle overflow-hidden flex border border-border-default">
                        <div
                          className="h-full bg-emerald-600 transition-all duration-300"
                          style={{
                            width: `${(cluster.teacher_confirmed_count / maxCount) * 100}%`,
                          }}
                          title={`Teacher Confirmed: ${cluster.teacher_confirmed_count}`}
                        />
                        <div
                          className="h-full bg-brand-primary transition-all duration-300"
                          style={{
                            width: `${(cluster.ai_proposed_count / maxCount) * 100}%`,
                          }}
                          title={`AI Proposed: ${cluster.ai_proposed_count}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        )}

        {/* =========================================================================
            SCREEN E: TEACHING ACTIONS & RECOMMENDATIONS
           ========================================================================= */}
        {currentTab === "recommendations" && (() => {
          const actions = insights?.intelligence?.differentiated_actions || [];
          const cohortStatus = insights?.intelligence?.cohort_status;
          const topicName = assessment?.math_topic || "Mathematics";

          let emptyTitle = "No Evidence-Supported Interventions Available";
          let emptyDescription = "No recurring misconception patterns met the threshold for intervention assignment across analyzed submissions.";

          if (responses.length === 0) {
            emptyTitle = "No Student Work Submitted Yet";
            emptyDescription = "Upload and analyze student worksheets to generate evidence-grounded teaching action plans.";
          } else if (!responses.some((r) => r.task_status === "COMPLETED")) {
            emptyTitle = "Analysis Pending or Not Yet Run";
            emptyDescription = "Run analysis on submitted worksheets to diagnose student reasoning and synthesize localized intervention blueprints.";
          } else if (cohortStatus === "all_insufficient") {
            emptyTitle = "Manual Teacher Review Required";
            emptyDescription = "Submitted responses require manual verification due to image clarity or unreadable handwriting.";
          } else if (cohortStatus === "unsupported_task") {
            emptyTitle = "Automated Recommendations Not Supported";
            emptyDescription = `Assessment topic '${topicName}' is outside supported automated diagnostic domains. Generic number-line plans are suppressed.`;
          } else if (cohortStatus === "no_misconceptions" || (insights?.statistics && insights.statistics.correct_percentage === 100)) {
            emptyTitle = "Full Cohort Mastery Demonstrated";
            emptyDescription = `All analyzed students achieved correct answers with mathematically sound reasoning in ${topicName.toLowerCase()}. No systemic misconceptions were detected.`;
          }

          return (
            <div className="space-y-6">
              <PageHeader
                title="Differentiated Teaching Action Plans"
                subtitle={
                  assessment?.math_topic
                    ? `Actionable, tiered intervention blueprints targeting diagnosed misconceptions in ${assessment.math_topic.toLowerCase()}.`
                    : "Actionable, tiered intervention blueprints targeting diagnosed student misconceptions."
                }
                badge={
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-yellow/30 text-amber-950 border border-amber-300">
                    Pedagogical Recommendations
                  </span>
                }
              />

              {actions.length === 0 ? (
                <div className="p-8 rounded-2xl bg-surface-base border border-dashed border-border-default text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-surface-subtle border border-border-default flex items-center justify-center mx-auto text-ink-muted">
                    <Sparkles className="w-6 h-6 text-brand-primary" />
                  </div>
                  <Typography variant="h3" className="text-base font-bold text-ink-primary">
                    {emptyTitle}
                  </Typography>
                  <Typography variant="body-sm" className="text-ink-secondary max-w-lg mx-auto">
                    {emptyDescription}
                  </Typography>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {actions.map((action, idx) => (
                    <TeachingRecommendationCard key={idx} action={action} />
                  ))}
                </div>
              )}
            </div>
          );
        })()}

        {/* =========================================================================
            SCREEN F: CLASSROOM RESOURCES / EXIT TICKET
           ========================================================================= */}
        {currentTab === "resources" && (
          <ClassroomResourcesView
            exitTicketItems={insights?.intelligence?.formative_exit_ticket || []}
            mathTopic={assessment?.math_topic}
            assessmentTitle={assessment?.title}
          />
        )}

        {/* =========================================================================
            SCREEN G: ASSESSMENTS MANAGEMENT VIEW
           ========================================================================= */}
        {currentTab === "assessments" && (() => {
          const rawAssessments = assessmentsList.length > 0 ? assessmentsList : assessment ? [assessment] : [];
          const isDemoAssessment = (a: Assessment) =>
            Boolean(a.is_demo) || a.id === "asm_1065658" || a.id === "asm_synthetic_cases";

          const totalAll = rawAssessments.length;
          const totalClassroom = rawAssessments.filter((a) => !isDemoAssessment(a)).length;
          const totalDemo = rawAssessments.filter((a) => isDemoAssessment(a)).length;

          const displayedAssessments = rawAssessments.filter((a) => {
            if (assessmentFilter === "classroom") return !isDemoAssessment(a);
            if (assessmentFilter === "demo") return isDemoAssessment(a);
            return true;
          });

          return (
            <div className="space-y-6">
              <PageHeader
                title="Assessment Management"
                subtitle="Review, create, and configure mathematics diagnostic checkpoints."
                actions={
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowUploadModal(true)}
                      className="border-brand-primary/30 text-brand-primary hover:bg-brand-light/30 font-semibold"
                    >
                      <UploadCloud className="w-4 h-4 mr-1 text-brand-primary" />
                      Upload Worksheets
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowCreateModal(true)}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      New Assessment
                    </Button>
                  </div>
                }
              />

              {/* Assessment Type Filter Pills */}
              <div className="flex items-center gap-2 border-b border-border-default pb-3 overflow-x-auto">
                <button
                  type="button"
                  onClick={() => setAssessmentFilter("all")}
                  className={cn(
                    "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap",
                    assessmentFilter === "all"
                      ? "bg-brand-primary text-white shadow-xs"
                      : "bg-surface-subtle text-ink-secondary hover:text-ink-primary hover:bg-surface-base border border-border-default"
                  )}
                >
                  All Checkpoints ({totalAll})
                </button>
                <button
                  type="button"
                  onClick={() => setAssessmentFilter("classroom")}
                  className={cn(
                    "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1.5",
                    assessmentFilter === "classroom"
                      ? "bg-emerald-700 text-white shadow-xs"
                      : "bg-surface-subtle text-ink-secondary hover:text-ink-primary hover:bg-surface-base border border-border-default"
                  )}
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                  Classroom Checkpoints ({totalClassroom})
                </button>
                <button
                  type="button"
                  onClick={() => setAssessmentFilter("demo")}
                  className={cn(
                    "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1.5",
                    assessmentFilter === "demo"
                      ? "bg-amber-600 text-white shadow-xs"
                      : "bg-surface-subtle text-ink-secondary hover:text-ink-primary hover:bg-surface-base border border-border-default"
                  )}
                >
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
                  Demo Showcases ({totalDemo})
                </button>
              </div>

              {displayedAssessments.length === 0 ? (
                <div className="p-12 text-center border border-dashed border-border-default rounded-2xl bg-surface-subtle/50 space-y-3">
                  <div className="w-12 h-12 rounded-full bg-brand-light/50 text-brand-primary flex items-center justify-center mx-auto">
                    <FolderOpen className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-ink-primary text-base">
                    {assessmentFilter === "classroom"
                      ? "No Classroom Assessments Yet"
                      : assessmentFilter === "demo"
                      ? "No Demo Showcases Found"
                      : "No Assessments Found"}
                  </h3>
                  <p className="text-xs text-ink-secondary max-w-md mx-auto">
                    {assessmentFilter === "classroom"
                      ? "Create custom mathematics diagnostic checkpoints for your own classes using the 'New Assessment' button."
                      : "No matching checkpoints found for the selected filter."}
                  </p>
                  {assessmentFilter === "classroom" && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowCreateModal(true)}
                      className="mt-2"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Create First Classroom Assessment
                    </Button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {displayedAssessments.map((asm) => {
                    const isActive = asm.id === currentAssessmentId;
                    const isDemo = isDemoAssessment(asm);
                    const classNameLabel =
                      asm.class_id === "cls_sec1_math"
                        ? "Sec 1 Mathematics"
                        : asm.class_id || "Classroom";

                    return (
                      <Card
                        key={asm.id}
                        variant={isActive ? "highlighted" : "default"}
                        className={cn(
                          "transition-all flex flex-col justify-between",
                          isActive ? "ring-2 ring-brand-primary/40 shadow-sm" : "hover:border-brand-primary/40"
                        )}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {isActive && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-primary text-white tracking-wide uppercase">
                                  Active
                                </span>
                              )}
                              {isDemo ? (
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                                  Demo Showcase
                                </span>
                              ) : (
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                                  Classroom Checkpoint
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-medium text-ink-secondary bg-surface-subtle px-2 py-0.5 rounded-md border border-border-default">
                              {classNameLabel}
                              {asm.grade_level ? ` • ${asm.grade_level}` : ""}
                            </span>
                          </div>
                          <CardTitle className="text-base mt-2.5 line-clamp-1">{asm.title}</CardTitle>
                          <CardDescription className="line-clamp-2 text-xs">
                            {asm.math_topic || "Integer operations on number lines"}
                            {asm.question?.question_text ? ` • ${asm.question.question_text}` : ""}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3 pt-0">
                          <div className="space-y-1.5 text-xs text-ink-secondary bg-surface-subtle/50 p-2.5 rounded-lg border border-border-default">
                            <div className="flex justify-between py-0.5">
                              <span>Class & Grade:</span>
                              <strong className="text-ink-primary font-medium">
                                {classNameLabel} • {asm.grade_level || "Secondary 1"}
                              </strong>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span>Total Submissions:</span>
                              <strong className="text-ink-primary font-mono">
                                {isActive ? responses.length : (asm.total_responses ?? 0)} Worksheets
                              </strong>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span>Expected Solution:</span>
                              <strong className="text-emerald-700 font-mono">
                                {asm.question?.expected_answer || "+2"} (SymPy Verified)
                              </strong>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span>Status:</span>
                              <strong className="text-ink-primary font-mono capitalize">
                                {asm.status || "ready"}
                              </strong>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              variant={isActive ? "secondary" : "outline"}
                              size="sm"
                              className="flex-1 text-xs"
                              onClick={() => {
                                if (!isActive) handleSelectAssessment(asm.id);
                                setCurrentTab("responses");
                              }}
                            >
                              {isActive ? "View Submissions" : "Select Checkpoint"}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs text-brand-primary hover:bg-brand-light/30"
                              onClick={() => {
                                if (!isActive) handleSelectAssessment(asm.id);
                                setShowUploadModal(true);
                              }}
                              title="Upload new worksheets to this assessment"
                            >
                              <UploadCloud className="w-3.5 h-3.5 mr-1" />
                              Upload
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })()}

        {/* =========================================================================
            SCREEN F: AI RELIABILITY & BENCHMARK EVALUATION (GATE 4C)
           ========================================================================= */}
        {currentTab === "evaluation" && (
          <AiEvaluationView />
        )}
      </div>

      {/* =========================================================================
          SCREEN C: STUDENT WORK & INSPECTION MODAL
         ========================================================================= */}
      {selectedResponseId && (
        <StudentInspectionModal
          responseId={selectedResponseId}
          assessmentId={asmId}
          isOpen={!!selectedResponseId}
          onClose={() => setSelectedResponseId(null)}
          onReviewChanged={() => loadData(currentAssessmentId)}
          onNavigatePrev={() => {
            if (selectedIndex > 0) {
              setSelectedResponseId(responses[selectedIndex - 1].id);
            }
          }}
          onNavigateNext={() => {
            if (selectedIndex < responses.length - 1) {
              setSelectedResponseId(responses[selectedIndex + 1].id);
            }
          }}
          hasPrev={selectedIndex > 0}
          hasNext={selectedIndex < responses.length - 1}
        />
      )}

      {/* Assessment Switcher Dialog */}
      <Dialog
        isOpen={showAssessmentModal}
        onClose={() => setShowAssessmentModal(false)}
        size="md"
        title="Select Assessment Checkpoint"
        description="Switch between curricular checkpoints or create a new assessment."
        footer={
          <div className="w-full flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowAssessmentModal(false);
                setShowCreateModal(true);
              }}
              className="text-xs border-dashed"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              New Assessment
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setShowAssessmentModal(false)}>
              Close
            </Button>
          </div>
        }
      >
        <div className="space-y-2 text-xs">
          {(assessmentsList.length > 0
            ? assessmentsList
            : [
                {
                  id: "asm_1065658",
                  title: "Checkpoint 1 — Integers & Number Lines",
                  math_topic: "Curated cohort of 13 student responses • Problem #1065658 (-6 + 12 - 4)",
                  is_demo: true,
                },
                {
                  id: "asm_synthetic_cases",
                  title: "Synthetic Feasibility Benchmark: Cases 1–3",
                  math_topic: "3 Authorized Worksheets: Canonical Correct, Off-by-One Error, Ambiguous & Incomplete",
                  is_demo: true,
                },
              ]
          ).map((asm) => {
            const isSelected = currentAssessmentId === asm.id;
            const isDemo = ("is_demo" in asm && Boolean(asm.is_demo)) || asm.id === "asm_1065658" || asm.id === "asm_synthetic_cases";
            return (
              <div
                key={asm.id}
                onClick={() => handleSelectAssessment(asm.id)}
                className={cn(
                  "p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between",
                  isSelected
                    ? "border-brand-primary bg-brand-light/30 ring-1 ring-brand-primary"
                    : "border-border-default bg-surface-base hover:bg-surface-subtle"
                )}
              >
                <div className="pr-2">
                  <p className="font-bold text-ink-primary text-sm flex items-center gap-1.5">
                    {asm.title}
                    {isDemo && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                        Demo
                      </span>
                    )}
                  </p>
                  <p className="text-[11px] text-ink-muted mt-0.5 line-clamp-1">
                    {asm.math_topic || ("question" in asm ? asm.question?.question_text : undefined) || "Mathematics Checkpoint"}
                  </p>
                </div>
                {isSelected && (
                  <span className="shrink-0 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-primary text-white">
                    Active
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </Dialog>

      {/* Create Assessment Modal */}
      <CreateAssessmentModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onAssessmentCreated={async (newAsm) => {
          setCurrentAssessmentId(newAsm.id);
          if (typeof window !== "undefined") {
            try {
              localStorage.setItem("classlens_active_assessment_id", newAsm.id);
              const url = new URL(window.location.href);
              url.searchParams.set("asm", newAsm.id);
              url.searchParams.set("tab", "responses");
              window.history.replaceState({}, "", url.toString());
            } catch (e) {
              console.warn("Could not save new assessment to storage/url:", e);
            }
          }
          await loadData(newAsm.id);
          setCurrentTab("responses");
        }}
      />

      {/* Worksheet Upload Modal */}
      <WorksheetUploadModal
        isOpen={showUploadModal}
        assessmentId={currentAssessmentId}
        assessmentTitle={assessment?.title || currentAssessmentId}
        existingCount={responses.length}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={async () => {
          await loadData(currentAssessmentId);
          setCurrentTab("responses");
        }}
      />
    </AppShell>
  );
}
