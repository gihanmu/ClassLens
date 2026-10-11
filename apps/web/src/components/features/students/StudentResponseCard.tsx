import * as React from "react";
import { cn } from "@/lib/utils";
import { StudentResponse } from "@/lib/api";
import { AnswerStatusBadge } from "./AnswerStatusBadge";
import { ReasoningStatusBadge } from "./ReasoningStatusBadge";
import { TeacherReviewBadge } from "./TeacherReviewBadge";
import { Button } from "@/components/ui/button";
import { Eye, FileText } from "lucide-react";
import { getMisconceptionPlainLanguage } from "@/lib/terminology";

export interface StudentResponseCardProps {
  response: StudentResponse;
  assessmentId: string;
  onInspect: (response: StudentResponse) => void;
  className?: string;
}

export function StudentResponseCard({
  response,
  assessmentId,
  onInspect,
  className,
}: StudentResponseCardProps) {
  const imageUrl = `/api/v1/responses/${response.id}/image`;
  const isReviewed =
    response.teacher_review_status === "reviewed" ||
    response.teacher_review_status === "completed" ||
    response.teacher_review_status === "overridden";
  const needsReview = response.needs_teacher_review && !isReviewed;

  // Plain-language diagnostic summary
  const summaryText = React.useMemo(() => {
    if (response.teacher_notes) {
      return response.teacher_notes;
    }
    if (response.misconception_taxonomy_id) {
      return getMisconceptionPlainLanguage(response.misconception_taxonomy_id);
    }
    if (response.answer_status === "correct" && response.reasoning_status?.includes("correct")) {
      return "All number-line hops accurate";
    }
    if (response.reasoning_status?.includes("incomplete")) {
      return "Not enough working shown";
    }
    if (response.answer_status === "undetermined") {
      return "Worksheet handwriting faint or unreadable";
    }
    return "Analysis complete • Ready for teacher inspection";
  }, [response]);

  const studentDisplayName =
    response.pseudonym_label ||
    (response.pseudonymous_student_id
      ? `Student-${response.pseudonymous_student_id.slice(-4).toUpperCase()}`
      : "Student");

  return (
    <article
      aria-label={`Submission card for ${studentDisplayName}`}
      className={cn(
        "group flex flex-col rounded-xl bg-surface-base border border-border-default shadow-xs hover:shadow-md hover:border-brand-primary/40 transition-all duration-200 overflow-hidden min-w-0 h-full",
        needsReview && "border-amber-300 bg-amber-50/15",
        response.teacher_review_status === "overridden" && "border-brand-primary/30",
        className
      )}
    >
      {/* 1. Card Header: Student name and review status (Zero overlay on preview) */}
      <header className="px-4 py-2.5 flex items-center justify-between gap-2 border-b border-border-default bg-surface-subtle/60 shrink-0 min-w-0">
        <div className="flex items-center gap-1.5 min-w-0">
          <h3 className="text-xs font-mono font-bold text-ink-primary truncate">
            {studentDisplayName}
          </h3>
          <span
            className="text-[10px] text-ink-muted hidden sm:inline"
            title={`Internal ID: ${response.id}`}
          >
            • #{response.id.slice(-4)}
          </span>
        </div>

        <TeacherReviewBadge
          reviewStatus={response.teacher_review_status}
          needsReview={response.needs_teacher_review}
        />
      </header>

      {/* 2. Worksheet Preview: Fixed aspect ratio, unobstructed, never distorted */}
      <div className="relative w-full aspect-[16/10] bg-slate-100/70 border-b border-border-default flex items-center justify-center overflow-hidden shrink-0">
        <img
          src={imageUrl}
          alt={`Handwritten worksheet for ${studentDisplayName}`}
          className="object-contain w-full h-full p-2 transition-transform duration-200 group-hover:scale-[1.02]"
          loading="lazy"
          onError={(e) => {
            const target = e.currentTarget;
            target.onerror = null;
            target.style.display = "none";
            const fallback = target.nextElementSibling as HTMLElement;
            if (fallback) fallback.style.display = "flex";
          }}
        />
        {/* Fallback container if image load errors */}
        <div
          style={{ display: "none" }}
          className="w-full h-full flex flex-col items-center justify-center p-4 text-center text-ink-muted bg-surface-muted"
        >
          <FileText className="w-8 h-8 text-ink-muted/50 mb-1" />
          <span className="text-[11px] font-medium">Worksheet Preview</span>
        </div>
      </div>

      {/* 3. Status Section & 4. Diagnostic Summary */}
      <div className="p-3.5 flex-1 flex flex-col justify-between gap-3 min-w-0">
        <div className="space-y-2 min-w-0">
          {/* Status Badges Row */}
          <div className="flex flex-wrap items-center gap-1.5 min-w-0">
            <AnswerStatusBadge status={response.answer_status} size="sm" />
            <ReasoningStatusBadge status={response.reasoning_status} size="sm" />
          </div>

          {/* Plain-Language Diagnostic Summary */}
          <p
            className="text-xs text-ink-secondary leading-relaxed line-clamp-2 min-h-[36px]"
            title={summaryText}
          >
            {summaryText}
          </p>
        </div>

        {/* 5. Footer: One clear Inspect action with guaranteed horizontal icon alignment */}
        <div className="pt-2 border-t border-border-subtle mt-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onInspect(response)}
            icon={<Eye className="w-4 h-4 text-brand-primary" />}
            className="w-full font-semibold border-border-default group-hover:border-brand-primary group-hover:text-brand-primary group-hover:bg-brand-light/20 transition-colors"
          >
            Inspect Work
          </Button>
        </div>
      </div>
    </article>
  );
}
