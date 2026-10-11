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
 * Answer Correctness Status Mapping:
 * - Correct
 * - Incorrect
 * - Cannot determine
 */
export function getAnswerStatusConfig(status?: string | null): StatusConfig {
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

  return {
    label: "Cannot determine",
    code: "undetermined",
    description: "Final answer is unwritten, missing, or obscured",
    tone: "neutral",
  };
}

/**
 * Reasoning Status Mapping:
 * - Correct reasoning
 * - Reasoning error
 * - Incomplete working
 * - Unclear working
 */
export function getReasoningStatusConfig(status?: string | null): StatusConfig {
  const norm = (status || "").toLowerCase().trim();

  if (norm.includes("correct") || norm === "valid") {
    return {
      label: "Correct reasoning",
      code: "correct",
      description: "All number-line hops follow valid mathematical rules",
      tone: "success",
    };
  }

  if (norm.includes("error") || norm.includes("procedure")) {
    return {
      label: "Reasoning error",
      code: "error",
      description: "Observed number-line hops contain procedural errors",
      tone: "error",
    };
  }

  if (norm.includes("incomplete")) {
    return {
      label: "Incomplete working",
      code: "incomplete",
      description: "Only partial working or final answer provided without full hops",
      tone: "warning",
    };
  }

  return {
    label: "Unclear working",
    code: "unclear",
    description: "Handwriting or number line steps cannot be conclusively evaluated",
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
