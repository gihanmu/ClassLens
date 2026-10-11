"use client";

import React, { useEffect, useState } from "react";
import {
  api,
  Assessment,
  StudentResponse,
  CohortInsights,
} from "@/lib/api";
import {
  Users,
  BarChart3,
  Sparkles,
  FileText,
  FolderOpen,
  DownloadCloud,
  Check,
  AlertTriangle,
  Lightbulb,
  ShieldCheck,
  Layers,
  HelpCircle,
  X,
  ChevronDown,
  ChevronUp,
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
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { Spinner } from "@/components/ui/spinner";
import { Dialog } from "@/components/ui/dialog";
import { getMisconceptionPlainLanguage } from "@/lib/terminology";

const STORAGE_KEY_WELCOME = "classlens_welcome_dismissed";

export default function ClassLensApp() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [responses, setResponses] = useState<StudentResponse[]>([]);
  const [insights, setInsights] = useState<CohortInsights | null>(null);
  const [currentTab, setCurrentTab] = useState<NavItemKey>("responses");
  const [filter, setFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedResponseId, setSelectedResponseId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAssessmentModal, setShowAssessmentModal] = useState<boolean>(false);
  const [showHeroBanner, setShowHeroBanner] = useState<boolean>(false);

  const asmId = "asm_1065658";

  const loadData = async () => {
    try {
      setLoading(true);
      await api.ensureDemoSession();
      const asm = await api.getAssessment(asmId);
      setAssessment(asm);

      const resps = await api.listResponses(asmId);
      setResponses(resps);

      if (resps.some((r) => r.task_status === "COMPLETED")) {
        try {
          const ins = await api.getCohortInsights(asmId);
          setInsights(ins);
        } catch (e) {
          console.warn("Cohort insights not ready yet:", e);
        }
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

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

    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const respParam = params.get("response");
      const tabParam = params.get("tab");
      if (respParam) setSelectedResponseId(respParam);
      if (
        tabParam &&
        ["responses", "insights", "recommendations", "resources", "assessments"].includes(tabParam)
      ) {
        setCurrentTab(tabParam as NavItemKey);
      }
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
      await api.importDemoResponses(asmId);
      await loadData();
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
      await api.triggerAnalysis(asmId, `job_run_${Date.now()}`);
      setTimeout(async () => {
        await loadData();
        setIsAnalyzing(false);
      }, 1200);
    } catch (err) {
      console.error("Failed to launch analysis:", err);
      setIsAnalyzing(false);
      alert("Failed to launch batch analysis.");
    }
  };

  // Derived cohort metrics with strict semantic boundaries
  const totalSubmissions = responses.length;
  const completedAnalyses = responses.filter((r) => r.task_status === "COMPLETED").length;
  const correctCount = responses.filter((r) => r.answer_status === "correct").length;
  const reviewedCount = responses.filter(
    (r) => r.teacher_review_status && r.teacher_review_status !== "unreviewed"
  ).length;

  // Strict semantics: only students flagged who are not yet confirmed/overridden
  const needsReviewCount = responses.filter(
    (r) => r.needs_teacher_review && r.teacher_review_status === "unreviewed"
  ).length;

  // Procedural errors in reasoning or final answer incorrect
  const procedureErrorCount = responses.filter(
    (r) => r.reasoning_status?.includes("error") || r.answer_status === "incorrect"
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

    if (filter === "review") {
      return r.needs_teacher_review && r.teacher_review_status === "unreviewed";
    }
    if (filter === "errors") {
      return r.reasoning_status?.includes("error") || r.answer_status === "incorrect";
    }
    if (filter === "correct") {
      return r.answer_status === "correct";
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
    >
      <div className="space-y-6">
        {/* =========================================================================
            SCREEN A: COMPACT DISMISSIBLE INTRODUCTION (First-Visit or On-Demand)
           ========================================================================= */}
        {showHeroBanner && (
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
                    onClick={handleImport}
                    disabled={loading || responses.length > 0}
                  >
                    <DownloadCloud className="w-4 h-4 text-ink-muted" />
                    {responses.length > 0 ? "Dataset Loaded (13)" : "Import 13 Responses"}
                  </Button>
                  <Button
                    variant="coral"
                    size="sm"
                    onClick={handleAnalyze}
                    isLoading={isAnalyzing}
                    disabled={responses.length === 0}
                  >
                    <Sparkles className="w-4 h-4" />
                    {isAnalyzing ? "Analyzing Pipeline..." : "Run Multi-Agent Analysis"}
                  </Button>
                </div>
              }
            />

            {/* 4 Metric Summary Cards */}
            <section aria-label="Assessment Metrics Summary" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Submissions"
                value={totalSubmissions}
                subtext="Curated classroom cohort"
                accent="brand"
                icon={<Layers className="w-5 h-5" />}
              />
              <MetricCard
                title="Analyses Completed"
                value={completedAnalyses}
                denominator={totalSubmissions}
                subtext={
                  totalSubmissions > 0
                    ? `${Math.round((completedAnalyses / totalSubmissions) * 100)}% analyzed`
                    : "Pending"
                }
                accent="mint"
                icon={<Check className="w-5 h-5" />}
              />
              <MetricCard
                title="Correct Final Answers"
                value={correctCount}
                denominator={totalSubmissions}
                subtext={
                  totalSubmissions > 0
                    ? `${Math.round((correctCount / totalSubmissions) * 100)}% accuracy rate`
                    : "Pending"
                }
                accent="coral"
                icon={<Sparkles className="w-5 h-5" />}
              />
              <MetricCard
                title="Teacher Reviews"
                value={reviewedCount}
                denominator={totalSubmissions}
                subtext={`${needsReviewCount} flagged for review`}
                accent="yellow"
                icon={<ShieldCheck className="w-5 h-5" />}
              />
            </section>

            {/* Filter Bar with Documented Semantics */}
            <FilterBar
              options={[
                { id: "all", label: "All Responses", count: totalSubmissions },
                { id: "review", label: "Needs Review", count: needsReviewCount },
                { id: "errors", label: "Procedural Errors", count: procedureErrorCount },
                { id: "correct", label: "Correct Final Answer", count: correctCount },
              ]}
              selectedId={filter}
              onSelect={setFilter}
              searchValue={searchQuery}
              onSearchChange={setSearchQuery}
              searchPlaceholder="Filter student ID, note, or error..."
            />

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
        {currentTab === "recommendations" && (
          <div className="space-y-6">
            <PageHeader
              title="Differentiated Teaching Action Plans"
              subtitle="Actionable, tiered intervention blueprints targeting localized number-line misconceptions."
              badge={
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-yellow/30 text-amber-950 border border-amber-300">
                  Pedagogical Recommendations
                </span>
              }
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {(
                insights?.intelligence?.differentiated_actions || [
                  {
                    action_type: "concrete_manipulative",
                    target_misconception_id: "START_POINT_ZERO_MISUNDERSTANDING",
                    title: "Floor Number Line Walkway",
                    student_count_affected: 2,
                    instructional_steps: [
                      "Lay painter's tape across classroom floor marked from -10 to +10.",
                      "Ask student to physically stand on 0 as the 'home base' origin.",
                      "Demonstrate taking 6 steps backward to land on -6, reinforcing that origin is where motion begins.",
                    ],
                  },
                  {
                    action_type: "worked_example",
                    target_misconception_id: "INCORRECT_INTERVAL_MAGNITUDE",
                    title: "Side-by-Side Hop Comparison",
                    student_count_affected: 3,
                    instructional_steps: [
                      "Present an incorrect +6 jump next to the correct +12 jump on whiteboard.",
                      "Prompt class: 'Why does jumping 12 units land on +6 rather than 0?'",
                      "Guide students to count intervals between tick marks, not the tick marks themselves.",
                    ],
                  },
                  {
                    action_type: "guided_inquiry",
                    target_misconception_id: "COMPENSATORY_ARITHMETIC_ERROR",
                    title: "Reasoning vs. Answer Audit",
                    student_count_affected: 1,
                    instructional_steps: [
                      "Examine why getting the right answer (+2) with wrong hops creates confusion on advanced algebra.",
                      "Have students verify each hop with SymPy rules independently.",
                    ],
                  },
                ]
              ).map((action, idx) => (
                <TeachingRecommendationCard key={idx} action={action} />
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
            SCREEN F: CLASSROOM RESOURCES / EXIT TICKET
           ========================================================================= */}
        {currentTab === "resources" && (
          <ClassroomResourcesView
            exitTicketItems={
              insights?.intelligence?.formative_exit_ticket || [
                {
                  question_number: 1,
                  prompt: "Evaluate -4 + 9 using the number line. Start at 0.",
                  target_misconception: "START_POINT_ZERO_MISUNDERSTANDING",
                  expected_answer: "5",
                  sympy_verified: true,
                },
                {
                  question_number: 2,
                  prompt: "Evaluate -7 + 10 - 2 on the number line.",
                  target_misconception: "INCORRECT_INTERVAL_MAGNITUDE",
                  expected_answer: "1",
                  sympy_verified: true,
                },
                {
                  question_number: 3,
                  prompt: "A student jumps from 0 to -5, then jumps +12. What number do they land on?",
                  target_misconception: "DIRECTION_SIGN_CONFUSION",
                  expected_answer: "7",
                  sympy_verified: true,
                },
              ]
            }
          />
        )}

        {/* =========================================================================
            SCREEN G: ASSESSMENTS MANAGEMENT VIEW
           ========================================================================= */}
        {currentTab === "assessments" && (
          <div className="space-y-6">
            <PageHeader
              title="Assessment Management"
              subtitle="Review and configure mathematics diagnostic checkpoints."
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card variant="highlighted">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-light text-brand-primary">
                      Active Demonstration
                    </span>
                    <span className="text-xs font-mono text-ink-muted">asm_1065658</span>
                  </div>
                  <CardTitle className="text-lg mt-2">
                    {assessment?.title || "Integers on Number Line: Checkpoint 1"}
                  </CardTitle>
                  <CardDescription>
                    Singapore Secondary 1 Math • Question: Evaluate -6 + 12 - 4
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-xs text-ink-secondary">
                  <div className="flex justify-between py-1 border-b border-border-default">
                    <span>Total Submissions:</span>
                    <strong className="text-ink-primary font-mono">{responses.length} Worksheets</strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border-default">
                    <span>Expected Solution:</span>
                    <strong className="text-emerald-700 font-mono">+2 (Exact SymPy Verified)</strong>
                  </div>
                  <div className="flex justify-between py-1">
                    <span>Status:</span>
                    <strong className="text-ink-primary font-mono">100% Mock Ready</strong>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
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
          onReviewChanged={loadData}
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
        title="Active Assessment Checkpoint"
        description="Select or inspect mathematics diagnostic curriculum checkpoints."
      >
        <div className="space-y-3 text-xs">
          <div className="p-3 rounded-lg border border-brand-primary bg-brand-light/30 flex items-center justify-between">
            <div>
              <p className="font-bold text-ink-primary">Checkpoint 1 — Integers &amp; Number Lines</p>
              <p className="text-[11px] text-ink-muted">13 student responses • Sec 1 Math</p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-primary text-white">
              Current
            </span>
          </div>

          <div className="pt-2 flex justify-end">
            <Button variant="secondary" size="sm" onClick={() => setShowAssessmentModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Dialog>
    </AppShell>
  );
}
