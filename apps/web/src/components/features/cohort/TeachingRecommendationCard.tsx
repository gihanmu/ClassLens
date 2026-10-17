import * as React from "react";
import { Blocks, BookOpen, Compass, Users, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { DifferentiatedAction } from "@/lib/api";

export interface TeachingRecommendationCardProps {
  action: DifferentiatedAction;
  className?: string;
}

const actionIcons = {
  concrete_manipulative: Blocks,
  worked_example: BookOpen,
  guided_inquiry: Compass,
};

const actionBadges = {
  concrete_manipulative: { label: "Hands-On Manipulative", bg: "bg-accent-yellow/20 text-amber-950 border-amber-300" },
  worked_example: { label: "Worked Example", bg: "bg-accent-coral/15 text-accent-coral border-accent-coral/30" },
  guided_inquiry: { label: "Guided Inquiry", bg: "bg-brand-light text-brand-primary border-brand-primary/20" },
};

export function TeachingRecommendationCard({
  action,
  className,
}: TeachingRecommendationCardProps) {
  const Icon = actionIcons[action.action_type] || BookOpen;
  const badgeConfig = actionBadges[action.action_type] || actionBadges.worked_example;

  const isRepresentationFollowUp =
    action.status === "representation_followup" ||
    action.target_misconception_id.includes("REPRESENTATION") ||
    action.target_misconception_id.includes("VISUAL-MODEL");

  const statusLabel = isRepresentationFollowUp
    ? "Visual Model Follow-Up"
    : action.status === "possible_misconception"
    ? "Pending Teacher Review"
    : "Verified Misconception";

  const statusColor = isRepresentationFollowUp
    ? "bg-indigo-50 text-indigo-800 border-indigo-200"
    : action.status === "possible_misconception"
    ? "bg-amber-50 text-amber-800 border-amber-200"
    : "bg-emerald-50 text-emerald-800 border-emerald-200";

  return (
    <div
      className={cn(
        "flex flex-col p-5 rounded-xl bg-surface-base border border-border-default shadow-xs hover:shadow-md transition-all duration-200 justify-between",
        className
      )}
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-surface-subtle flex items-center justify-center text-ink-primary border border-border-default">
              <Icon className="w-5 h-5 text-brand-primary" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className={cn("px-2 py-0.5 rounded text-[10px] font-semibold border", badgeConfig.bg)}>
                  {badgeConfig.label}
                </span>
                <span className={cn("px-2 py-0.5 rounded text-[10px] font-semibold border", statusColor)}>
                  {statusLabel}
                </span>
              </div>
              <h4 className="text-sm font-bold text-ink-primary mt-1">
                {action.title}
              </h4>
            </div>
          </div>

          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-surface-muted text-ink-secondary shrink-0">
            <Users className="w-3.5 h-3.5 text-ink-muted" />
            {action.student_count_affected} {action.student_count_affected === 1 ? "Student" : "Students"}
          </span>
        </div>

        {action.rationale && (
          <p className="text-[11px] text-ink-muted italic mb-3">
            {action.rationale}
          </p>
        )}

        <div className="mt-3 space-y-2">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
            Instructional Sequence
          </div>
          <ol className="space-y-2 text-xs text-ink-secondary">
            {action.instructional_steps.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-brand-light text-brand-primary font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="mt-5 pt-3 border-t border-border-subtle flex flex-col gap-1.5 text-[11px] text-ink-muted">
        <div className="flex items-center justify-between">
          <span>Target: <strong className="text-ink-secondary font-mono">{action.target_misconception_id.replace(/_/g, " ")}</strong></span>
          {action.task_type && (
            <span className="font-mono text-[10px] text-ink-muted capitalize">
              {action.task_type.replace(/_/g, " ")}
            </span>
          )}
        </div>
        {action.supporting_response_ids && action.supporting_response_ids.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap pt-1 text-[10px]">
            <span className="text-ink-muted font-medium">Evidence:</span>
            {action.supporting_response_ids.slice(0, 4).map((id) => (
              <span
                key={id}
                className="px-1.5 py-0.2 rounded bg-surface-subtle border border-border-default font-mono text-[10px] text-ink-secondary"
                title={`Supporting Response: ${id}`}
              >
                {id.replace("resp_", "res_")}
              </span>
            ))}
            {action.supporting_response_ids.length > 4 && (
              <span className="text-ink-muted font-mono">
                +{action.supporting_response_ids.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
