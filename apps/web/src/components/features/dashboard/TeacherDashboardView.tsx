import * as React from "react";
import { cn } from "@/lib/utils";
import {
  DashboardSummary,
  AssessmentSummaryItem,
  AttentionItem,
  LearningInsightsSnapshot,
  ActivityItem,
} from "@/lib/api";
import { MetricCard } from "@/components/shared/metric-card";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { getMisconceptionPlainLanguage } from "@/lib/terminology";
import {
  Users,
  Layers,
  FolderOpen,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Eye,
  Lightbulb,
  FileText,
  Calendar,
  Check,
  ChevronRight,
  HelpCircle,
  UploadCloud,
} from "lucide-react";

export interface TeacherDashboardViewProps {
  summary: DashboardSummary | null;
  loading: boolean;
  onOpenAssessmentsModal: () => void;
  onNavigateToStudentWork: (assessmentId?: string) => void;
  onInspectSubmission: (responseId: string) => void;
  onNavigateToInsights: (assessmentId?: string) => void;
  onRunBatchAnalysis: (assessmentId: string) => void;
  isAnalyzing?: boolean;
}

export function TeacherDashboardView({
  summary,
  loading,
  onOpenAssessmentsModal,
  onNavigateToStudentWork,
  onInspectSubmission,
  onNavigateToInsights,
  onRunBatchAnalysis,
  isAnalyzing = false,
}: TeacherDashboardViewProps) {
  // Compute contextual time greeting
  const greeting = React.useMemo(() => {
    try {
      const hour = new Date().getHours();
      if (hour < 12) return "Good morning";
      if (hour < 17) return "Good afternoon";
      return "Good evening";
    } catch {
      return "Welcome back";
    }
  }, []);

  if (loading || !summary) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-2xl bg-surface-muted/60" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-surface-muted/60" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 rounded-2xl bg-surface-muted/60" />
          <div className="h-64 rounded-2xl bg-surface-muted/60" />
        </div>
      </div>
    );
  }

  const {
    active_classes_count,
    total_students_count,
    total_assessments_count,
    awaiting_analysis_count,
    needing_review_count,
    assessments,
    attention_items,
    learning_insights_snapshot,
    recent_activity,
  } = summary;

  return (
    <div className="space-y-8">
      {/* =========================================================================
          SECTION A: Welcome & Contextual Header
          ========================================================================= */}
      <section
        aria-label="Welcome Overview"
        className="relative overflow-hidden rounded-2xl border border-border-default bg-surface-base shadow-xs p-6 sm:p-8"
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light text-brand-primary text-xs font-semibold">
              <Calendar className="w-3.5 h-3.5" />
              <span>Cedar Secondary • Term 1 Diagnostic Hub</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-ink-primary">
              {greeting}! Here&apos;s what&apos;s happening in your classroom.
            </h1>
            <p className="text-sm text-ink-secondary leading-relaxed">
              Review diagnostic checkpoints, examine handwritten student number lines verified by SymPy,
              and take evidence-grounded action across your cohort.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Button
              variant="outline"
              size="md"
              onClick={onOpenAssessmentsModal}
              icon={<FolderOpen className="w-4 h-4 text-ink-secondary" />}
            >
              View Assessments
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => onNavigateToStudentWork()}
              icon={<Users className="w-4 h-4 text-white" />}
            >
              Review Student Work
            </Button>
          </div>
        </div>

        {/* Decorative background gradient */}
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-brand-primary/5 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* =========================================================================
          COMPETITION MVP DEMO PATHWAYS BANNER
          ========================================================================= */}
      <section
        aria-label="Competition Demo Experience"
        className="rounded-2xl border border-brand-primary/20 bg-gradient-to-r from-brand-light/40 via-surface-base to-emerald-500/10 p-5 shadow-xs"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-primary text-white uppercase tracking-wider">
                AI Builder Cup 2026
              </span>
              <span className="text-xs font-semibold text-brand-primary">Competition MVP Guided Workflow</span>
            </div>
            <h3 className="text-base font-bold text-ink-primary">
              Experience ClassLens End-to-End: Two Demonstration Pathways
            </h3>
            <p className="text-xs text-ink-secondary max-w-3xl leading-relaxed">
              Explore the 13-student curated Singapore Sec 1 cohort with SymPy mathematical verification, or create a custom checkpoint and upload your own student worksheets with cryptographic privacy checks and truthful offline intake.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToStudentWork("asm_1065658")}
              className="text-xs font-semibold border-brand-primary/30 text-brand-primary hover:bg-brand-light/30"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1 text-brand-primary" />
              Explore Synthetic Demo (13)
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenAssessmentsModal}
              className="text-xs font-semibold shadow-xs"
            >
              <UploadCloud className="w-3.5 h-3.5 mr-1" />
              Create &amp; Upload Worksheets
            </Button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION B: Teacher-Level Summary Metrics (5 Cards)
          ========================================================================= */}
      <section aria-label="Teacher Summary Metrics" className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-ink-muted">
            Classroom Overview
          </h2>
          <span className="text-xs text-ink-muted">Real-time status</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          <MetricCard
            title="Active Classes"
            value={active_classes_count}
            subtext="Sec 1 Mathematics"
            accent="brand"
            icon={<Users className="w-5 h-5" />}
          />
          <MetricCard
            title="Total Students"
            value={total_students_count}
            subtext="Across cohorts"
            accent="brand"
            icon={<Layers className="w-5 h-5" />}
          />
          <MetricCard
            title="Assessments"
            value={total_assessments_count}
            subtext="Active checkpoints"
            accent="mint"
            icon={<FolderOpen className="w-5 h-5" />}
          />
          <MetricCard
            title="Awaiting Analysis"
            value={awaiting_analysis_count}
            subtext={
              awaiting_analysis_count > 0
                ? "Unprocessed worksheets"
                : "All submissions evaluated"
            }
            accent={awaiting_analysis_count > 0 ? "yellow" : "mint"}
            icon={<Clock className="w-5 h-5" />}
          />
          <MetricCard
            title="Needing Teacher Review"
            value={needing_review_count}
            subtext={
              needing_review_count > 0
                ? `${needing_review_count} across ${total_assessments_count} checkpoints`
                : "No pending decisions"
            }
            accent={needing_review_count > 0 ? "coral" : "neutral"}
            icon={<ShieldCheck className="w-5 h-5" />}
          />
        </div>
      </section>

      {/* =========================================================================
          SECTION C & D: Main Two-Column Hub Layout
          Left: Recent Assessments | Right: Teacher Attention Required
          ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (7 cols): Recent Assessments */}
        <section aria-label="Recent Assessments" className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink-primary">Recent Assessments</h2>
              <p className="text-xs text-ink-muted">
                Diagnostic checkpoints in your curriculum
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={onOpenAssessmentsModal} className="text-xs">
              All Assessments <ChevronRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>

          <div className="space-y-3.5">
            {assessments.map((asm) => {
              const isFullyAnalyzed = asm.progress_percentage === 100;
              const hasPending = asm.awaiting_analysis_count > 0;

              return (
                <div
                  key={asm.id}
                  className="group rounded-xl border border-border-default bg-surface-base p-5 shadow-xs hover:border-brand-primary/40 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-light text-brand-primary uppercase">
                          {asm.topic}
                        </span>
                        <span className="text-xs text-ink-muted">
                          {asm.class_name}
                        </span>
                        {asm.needs_review_count > 0 && (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-900 border border-amber-300">
                            {asm.needs_review_count} Need Review
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-bold text-ink-primary truncate">
                        {asm.title}
                      </h3>

                      <p className="text-xs text-ink-secondary">
                        {asm.total_submissions} total submissions •{" "}
                        {isFullyAnalyzed ? (
                          <span className="text-emerald-700 font-medium">
                            {asm.correct_answers_pct !== undefined ? `${asm.correct_answers_pct}% correct answers • ` : ""}
                            {asm.verified_reasoning_pct !== undefined ? `${asm.verified_reasoning_pct}% reasoning verified` : "All analyzed"}
                          </span>
                        ) : (
                          <span className="text-amber-700 font-medium">
                            {asm.awaiting_analysis_count} awaiting evaluation
                          </span>
                        )}
                      </p>
                    </div>

                    <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2 shrink-0">
                      {hasPending && (
                        <Button
                          variant="coral"
                          size="sm"
                          onClick={() => onRunBatchAnalysis(asm.id)}
                          isLoading={isAnalyzing}
                          className="text-xs font-semibold h-[36px]"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          Analyze
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onNavigateToStudentWork(asm.id)}
                        className="text-xs font-semibold h-[36px]"
                      >
                        Open Work <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="w-full h-2 rounded-full bg-surface-muted overflow-hidden">
                        <div
                          className={cn(
                            "h-full transition-all duration-500 rounded-full",
                            isFullyAnalyzed ? "bg-emerald-500" : "bg-brand-primary"
                          )}
                          style={{ width: `${asm.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-xs font-mono font-medium text-ink-secondary shrink-0">
                      {asm.progress_percentage}% ({asm.analyzed_count}/{asm.total_submissions})
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Right Column (5 cols): Teacher Attention Required */}
        <section aria-label="Teacher Attention Required" className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-ink-primary">Attention Required</h2>
              {attention_items.length > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  {attention_items.length}
                </span>
              )}
            </div>
            <span className="text-xs text-ink-muted">Action items</span>
          </div>

          <div className="space-y-3">
            {attention_items.length === 0 ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-6 text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <h3 className="text-sm font-bold text-ink-primary">All Caught Up!</h3>
                <p className="text-xs text-ink-secondary">
                  No submissions currently require manual teacher review or intervention.
                </p>
              </div>
            ) : (
              attention_items.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "rounded-xl border p-4 shadow-xs transition-all duration-200 bg-white",
                    item.severity === "high"
                      ? "border-amber-300 bg-amber-50/30"
                      : "border-border-default hover:border-brand-primary/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {item.type === "awaiting_analysis" ? (
                          <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        )}
                        <h4 className="text-xs font-bold text-ink-primary truncate">
                          {item.title}
                        </h4>
                      </div>
                      <p className="text-xs text-ink-secondary leading-relaxed">
                        {item.description}
                      </p>
                      <span className="inline-block text-[10px] text-ink-muted">
                        {item.assessment_title}
                      </span>
                    </div>

                    <div className="shrink-0">
                      {item.type === "awaiting_analysis" ? (
                        <Button
                          variant="coral"
                          size="sm"
                          onClick={() => onRunBatchAnalysis(item.assessment_id)}
                          isLoading={isAnalyzing}
                          className="text-xs h-[32px] px-2.5 font-semibold"
                        >
                          <Sparkles className="w-3 h-3" />
                          Run
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (item.response_id) {
                              onInspectSubmission(item.response_id);
                            } else {
                              onNavigateToStudentWork(item.assessment_id);
                            }
                          }}
                          className="text-xs h-[32px] px-2.5 font-semibold"
                        >
                          <Eye className="w-3 h-3 text-brand-primary" />
                          Review
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      {/* =========================================================================
          SECTION E & F: Insights Snapshot & Recent Activity
          ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start pt-4 border-t border-border-default">
        {/* Left: Learning Insights Snapshot (7 cols) */}
        <section aria-label="Learning Insights Snapshot" className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink-primary">Learning Insights Snapshot</h2>
              <p className="text-xs text-ink-muted">
                {learning_insights_snapshot.scope_label || "Cohort diagnostic trends & mathematical misconceptions"}
              </p>
            </div>
            {learning_insights_snapshot.has_analyzed_data && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigateToInsights()}
                className="text-xs text-brand-primary font-semibold"
              >
                Full Cohort Insights <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            )}
          </div>

          {!learning_insights_snapshot.has_analyzed_data ? (
            <div className="rounded-2xl border border-border-default bg-surface-base p-8 text-center space-y-3">
              <Lightbulb className="w-10 h-10 text-ink-muted/40 mx-auto" />
              <h3 className="text-sm font-bold text-ink-primary">
                Learning insights will appear once student work has been analyzed.
              </h3>
              <p className="text-xs text-ink-secondary max-w-md mx-auto">
                Run batch multi-agent analysis on your student submissions to surface evidence-supported misconceptions,
                verified reasoning percentages, and automated reteaching recommendations.
              </p>
              <div className="pt-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onNavigateToStudentWork()}
                  icon={<Users className="w-3.5 h-3.5" />}
                >
                  Go to Student Work
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-border-default bg-surface-base p-5 space-y-5 shadow-xs">
              {/* Quick stats row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-surface-subtle/80 border border-border-subtle">
                  <span className="text-xs font-semibold text-ink-secondary">
                    Verified Sound Reasoning
                  </span>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="text-2xl font-bold font-display text-emerald-700">
                      {learning_insights_snapshot.verified_reasoning_pct}%
                    </span>
                    <span className="text-[11px] text-ink-muted">
                      ({learning_insights_snapshot.verified_reasoning_count ?? 9}/{learning_insights_snapshot.analyzed_count} class-wide)
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-surface-subtle/80 border border-border-subtle">
                  <span className="text-xs font-semibold text-ink-secondary">
                    Correct Final Answers
                  </span>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="text-2xl font-bold font-display text-ink-primary">
                      {learning_insights_snapshot.correct_answers_pct}%
                    </span>
                    <span className="text-[11px] text-ink-muted">
                      ({learning_insights_snapshot.correct_answers_count ?? 10}/{learning_insights_snapshot.analyzed_count} class-wide)
                    </span>
                  </div>
                </div>
              </div>

              {/* Top detected misconceptions */}
              {learning_insights_snapshot.top_misconceptions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-ink-muted">
                    Dominant Supported Misconceptions
                  </h4>
                  <div className="space-y-2">
                    {learning_insights_snapshot.top_misconceptions.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-lg bg-red-50/50 border border-red-200/60 text-xs"
                      >
                        <div className="space-y-0.5">
                          <span className="font-semibold text-red-950">
                            {getMisconceptionPlainLanguage(item.taxonomy_id)}
                          </span>
                          <span className="block text-[10px] font-mono text-red-800/80">
                            {item.taxonomy_id}
                          </span>
                        </div>
                        <span className="font-bold text-red-900 bg-red-100 px-2.5 py-1 rounded-full">
                          {item.count} students ({item.percentage}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Action */}
              {learning_insights_snapshot.recommended_reteaching && (
                <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5">
                  <Lightbulb className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Recommended Reteaching Priority: </span>
                    <span>{learning_insights_snapshot.recommended_reteaching}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Right: Recent Activity Feed (5 cols) */}
        <section aria-label="Recent Activity" className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink-primary">Recent Activity</h2>
              <p className="text-xs text-ink-muted">
                Audit trail & system execution events
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-border-default bg-surface-base p-5 shadow-xs">
            {recent_activity.length === 0 ? (
              <div className="p-6 text-center text-ink-muted space-y-1">
                <FileText className="w-6 h-6 mx-auto opacity-40 mb-2" />
                <p className="text-xs font-semibold">No recent activity recorded.</p>
                <p className="text-[11px]">Teacher reviews and batch runs will log events here.</p>
              </div>
            ) : (
              <div className="space-y-3.5">
                {recent_activity.map((act) => (
                  <div
                    key={act.id}
                    className="flex items-start gap-3 pb-3 border-b border-border-subtle last:border-b-0 last:pb-0"
                  >
                    <div
                      className={cn(
                        "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5",
                        act.event_type === "teacher_review"
                          ? "bg-brand-light text-brand-primary"
                          : "bg-emerald-100 text-emerald-800"
                      )}
                    >
                      {act.event_type === "teacher_review" ? (
                        <ShieldCheck className="w-3.5 h-3.5" />
                      ) : (
                        <Check className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <div className="space-y-0.5 flex-1 min-w-0">
                      <p className="text-xs font-bold text-ink-primary truncate">
                        {act.title}
                      </p>
                      <p className="text-[11px] text-ink-secondary truncate">
                        {act.description}
                      </p>
                      <span className="text-[10px] text-ink-muted font-mono">
                        {new Date(act.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
