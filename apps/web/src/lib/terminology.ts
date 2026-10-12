/**
 * Standard plain-language terminology and status semantics for ClassLens.
 * Replaces technical codes with accessible, teacher-friendly explanations
 * while preserving original taxonomy codes for secondary technical details.
 */

export interface StatusConfig {
  label: string;
  code: string;
  description: string;
  tone: "success" | "error" | "warning" | "neutral" | "brand";
}

/**
 * Maps raw taxonomy IDs to plain-language, teacher-first explanations.
 */
export const MISCONCEPTION_LABELS: Record<string, string> = {
  "MISC-ARITH-OFF-BY-ONE": "Counting tick marks instead of intervals",
  "REASONING_INCOMPLETE": "Not enough working shown",
  "MISC-LINE-INTERVAL-MISLABEL": "Number-line labels may be incorrect",
  "START_POINT_ZERO_MISUNDERSTANDING": "Started at first number instead of 0",
  "DIRECTION_SIGN_CONFUSION": "Jumped in the wrong direction",
  "INCORRECT_INTERVAL_MAGNITUDE": "Incorrect hop length",
  "COMPENSATORY_ARITHMETIC_ERROR": "Correct answer despite calculation slip",
  "UNASSESSABLE_HANDWRITING": "Handwriting is unclear or faint",
  "ACCURATE_EXECUTION": "All number-line hops accurate",
  "PROCEDURAL_CALCULATION_SLIP": "Calculation slip during hop sequence",
};

export function getMisconceptionPlainLanguage(
  taxonomyId?: string | null,
  fallbackText?: string
): string {
  if (!taxonomyId) {
    return fallbackText || "No misconceptions detected";
  }

  const cleaned = taxonomyId.trim();
  if (MISCONCEPTION_LABELS[cleaned]) {
    return MISCONCEPTION_LABELS[cleaned];
  }

  // Check case-insensitive match
  const upper = cleaned.toUpperCase().replace(/\s+/g, "_");
  if (MISCONCEPTION_LABELS[upper]) {
    return MISCONCEPTION_LABELS[upper];
  }

  // Convert SNAKE_CASE or KEBAB-CASE to title case
  const readable = cleaned
    .replace(/^MISC[-_]/i, "")
    .replace(/[-_]/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return readable || fallbackText || "Procedural issue noted";
}

/**
 * Processing Status Mapping:
 * - Not analyzed (pending)
 * - Queued (queued)
 * - Analyzing (running)
 * - Analyzed (completed)
 * - Analysis failed (failed)
 */
export function getProcessingStatusConfig(status?: string | null): StatusConfig {
  const norm = (status || "").toLowerCase().trim();

  if (norm === "completed" || norm === "analyzed") {
    return {
      label: "Analyzed",
      code: "completed",
      description: "AI evaluation and SymPy mathematical verification complete",
      tone: "success",
    };
  }

  if (norm === "running" || norm === "analyzing" || norm === "processing") {
    return {
      label: "Analyzing",
      code: "running",
      description: "Multi-agent evaluation in progress",
      tone: "brand",
    };
  }

  if (norm === "queued") {
    return {
      label: "Queued",
      code: "queued",
      description: "Queued for processing",
      tone: "neutral",
    };
  }

  if (norm === "failed") {
    return {
      label: "Analysis failed",
      code: "failed",
      description: "Analysis encountered an operational error",
      tone: "error",
    };
  }

  return {
    label: "Not analyzed",
    code: "pending",
    description: "Submission has not been evaluated by AI",
    tone: "neutral",
  };
}

/**
 * Answer Correctness Status Mapping:
 * - Correct
 * - Incorrect
 * - Undetermined
 * - Not assessed
 */
export function getAnswerStatusConfig(
  status?: string | null,
  taskStatus?: string | null
): StatusConfig {
  if (taskStatus && taskStatus.toUpperCase() !== "COMPLETED") {
    return {
      label: "Not analyzed",
      code: "not_assessed",
      description: "Submission has not been evaluated by AI",
      tone: "neutral",
    };
  }

  const norm = (status || "").toLowerCase().trim();

  if (norm === "correct") {
    return {
      label: "Correct",
      code: "correct",
      description: "Final answer matches target value (+2)",
      tone: "success",
    };
  }

  if (norm === "incorrect") {
    return {
      label: "Incorrect",
      code: "incorrect",
      description: "Final answer does not match target value",
      tone: "error",
    };
  }

  if (norm === "not_assessed" || norm === "not assessed" || norm === "pending") {
    return {
      label: "Not assessed",
      code: "not_assessed",
      description: "Final answer has not been evaluated",
      tone: "neutral",
    };
  }

  return {
    label: "Undetermined",
    code: "undetermined",
    description: "Final answer is unwritten, missing, or obscured",
    tone: "neutral",
  };
}

/**
 * Reasoning Status Mapping:
 * - Verified
 * - Contains verified error
 * - Partially verified
 * - Unverifiable
 * - Not assessed
 */
export function getReasoningStatusConfig(
  status?: string | null,
  taskStatus?: string | null
): StatusConfig {
  if (taskStatus && taskStatus.toUpperCase() !== "COMPLETED") {
    return {
      label: "Not analyzed",
      code: "not_assessed",
      description: "Reasoning has not been evaluated by AI",
      tone: "neutral",
    };
  }

  const norm = (status || "").toLowerCase().trim();

  if (norm === "verified" || norm === "correct" || norm === "sound" || norm === "correct reasoning") {
    return {
      label: "Verified",
      code: "verified",
      description: "All mathematical reasoning steps mathematically sound and verified",
      tone: "success",
    };
  }

  if (
    norm.includes("verified error") ||
    norm.includes("contains_error") ||
    norm.includes("error") ||
    norm.includes("procedure")
  ) {
    return {
      label: "Contains verified error",
      code: "contains_verified_error",
      description: "Mathematical verification confirmed a step calculation or coordinate discrepancy",
      tone: "error",
    };
  }

  if (norm.includes("partial")) {
    return {
      label: "Partially verified",
      code: "partially_verified",
      description: "Some steps verified, but subsequent steps are missing or unsupported",
      tone: "warning",
    };
  }

  if (norm === "not_assessed" || norm === "not assessed" || norm === "pending") {
    return {
      label: "Not assessed",
      code: "not_assessed",
      description: "Reasoning has not yet been evaluated",
      tone: "neutral",
    };
  }

  return {
    label: "Unverifiable",
    code: "unverifiable",
    description: "Handwriting or steps cannot be conclusively verified from visible evidence",
    tone: "neutral",
  };
}

/**
 * Teacher Review Status Mapping:
 * - Not reviewed
 * - Needs review
 * - Teacher confirmed
 * - Teacher corrected
 */
export function getTeacherReviewStatusConfig(
  reviewStatus?: string | null,
  needsReview?: boolean
): StatusConfig {
  const norm = (reviewStatus || "").toLowerCase().trim();

  if (norm === "overridden") {
    return {
      label: "Teacher corrected",
      code: "overridden",
      description: "Educator overrode the automated diagnostic classification",
      tone: "brand",
    };
  }

  if (norm === "reviewed" || norm === "confirmed" || norm === "completed") {
    return {
      label: "Teacher confirmed",
      code: "reviewed",
      description: "Educator reviewed and confirmed the automated diagnosis",
      tone: "success",
    };
  }

  if (needsReview) {
    return {
      label: "Needs review",
      code: "needs_review",
      description: "Flagged for teacher inspection due to ambiguity or procedural errors",
      tone: "warning",
    };
  }

  return {
    label: "Not reviewed",
    code: "unreviewed",
    description: "Automated analysis complete; awaiting optional teacher inspection",
    tone: "neutral",
  };
}
