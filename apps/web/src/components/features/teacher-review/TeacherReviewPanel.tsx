import * as React from "react";
import { Check, Edit3, ShieldAlert, CheckCircle, Save } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

export interface TeacherReviewPanelProps {
  responseId: string;
  initialStatus?: string;
  initialOverrideTaxonomy?: string;
  initialNotes?: string;
  onSaveReview: (data: {
    status: "confirmed" | "overridden" | "unreadable";
    taxonomyId?: string;
    notes?: string;
  }) => Promise<void>;
  className?: string;
}

const taxonomyOptions = [
  { value: "MISC-LINE-INTERVAL-MISLABEL", label: "Interval Mislabel (+11 jump counted instead of +12 label)" },
  { value: "MISC-ARITH-OFF-BY-ONE", label: "Off-by-One Interval Miscount on Number Line" },
  { value: "START_POINT_ZERO_MISUNDERSTANDING", label: "Start Point Misunderstanding (Didn't start at 0)" },
  { value: "DIRECTION_SIGN_CONFUSION", label: "Direction / Sign Confusion (Jumped opposite way)" },
  { value: "INCORRECT_INTERVAL_MAGNITUDE", label: "Interval Magnitude Error (Incorrect hop displacement)" },
  { value: "COMPENSATORY_ARITHMETIC_ERROR", label: "Compensatory Error (Right final answer, erroneous steps)" },
  { value: "MISC-DIR-INV", label: "Directional Vector Inversion" },
  { value: "MISC-MAG-COUNT", label: "Magnitude Miscount on Number Line" },
  { value: "ACCURATE_EXECUTION", label: "Accurate Execution (No Misconception)" },
];

export function TeacherReviewPanel({
  responseId,
  initialStatus = "pending",
  initialOverrideTaxonomy = "",
  initialNotes = "",
  onSaveReview,
  className,
}: TeacherReviewPanelProps) {
  const [mode, setMode] = React.useState<"confirm" | "override" | "unreadable">(
    initialStatus === "marked_unreadable"
      ? "unreadable"
      : initialOverrideTaxonomy
      ? "override"
      : "confirm"
  );
  const [taxonomy, setTaxonomy] = React.useState(initialOverrideTaxonomy || "MISC-LINE-INTERVAL-MISLABEL");
  const [notes, setNotes] = React.useState(initialNotes);
  const [isSaving, setIsSaving] = React.useState(false);
  const [savedSuccess, setSavedSuccess] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);
    try {
      await onSaveReview({
        status: mode === "confirm" ? "confirmed" : mode === "unreadable" ? "unreadable" : "overridden",
        taxonomyId: mode === "override" ? taxonomy : undefined,
        notes: notes.trim(),
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className={cn(
        "p-5 rounded-xl bg-surface-base border border-border-default shadow-xs flex flex-col gap-4",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-ink-primary">Teacher Review & Override</h4>
          <p className="text-xs text-ink-muted">
            Educator decision authority takes absolute precedence over AI outputs.
          </p>
        </div>
        {savedSuccess && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-accent-mint px-2 py-0.5 rounded-full animate-fade-in">
            <CheckCircle className="w-3.5 h-3.5" />
            Saved & Audited
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Toggle Mode */}
        <div className="grid grid-cols-3 gap-1.5 p-1 bg-surface-subtle rounded-lg border border-border-default">
          <button
            type="button"
            onClick={() => setMode("confirm")}
            className={cn(
              "flex items-center justify-center gap-1 py-1.5 text-xs font-semibold rounded-md transition-all text-center",
              mode === "confirm"
                ? "bg-white text-ink-primary shadow-xs"
                : "text-ink-secondary hover:text-ink-primary"
            )}
          >
            <Check className="w-3.5 h-3.5 text-emerald-600" />
            Confirm AI
          </button>
          <button
            type="button"
            onClick={() => setMode("override")}
            className={cn(
              "flex items-center justify-center gap-1 py-1.5 text-xs font-semibold rounded-md transition-all text-center",
              mode === "override"
                ? "bg-white text-ink-primary shadow-xs"
                : "text-ink-secondary hover:text-ink-primary"
            )}
          >
            <Edit3 className="w-3.5 h-3.5 text-brand-primary" />
            Override
          </button>
          <button
            type="button"
            onClick={() => setMode("unreadable")}
            className={cn(
              "flex items-center justify-center gap-1 py-1.5 text-xs font-semibold rounded-md transition-all text-center",
              mode === "unreadable"
                ? "bg-white text-amber-900 shadow-xs"
                : "text-ink-secondary hover:text-ink-primary"
            )}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            Insufficient
          </button>
        </div>

        {/* Override taxonomy selector */}
        {mode === "override" && (
          <div>
            <label className="block text-xs font-semibold text-ink-secondary mb-1">
              Correct Misconception Classification
            </label>
            <Select
              value={taxonomy}
              onChange={(e) => setTaxonomy(e.target.value)}
              options={taxonomyOptions}
              placeholder="Select custom misconception classification..."
            />
          </div>
        )}

        {/* Teacher Notes */}
        <div>
          <label className="block text-xs font-semibold text-ink-secondary mb-1">
            Teacher Clinical Notes (Audit Log)
          </label>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add specific context, classroom observations, or notes for small-group intervention..."
            rows={3}
            className="text-xs"
          />
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-2 pt-1">
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={isSaving}
            className="font-semibold shadow-xs"
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            Save Teacher Review
          </Button>
        </div>
      </form>
    </div>
  );
}
