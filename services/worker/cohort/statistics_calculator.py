"""Deterministic cohort statistics calculator."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Union

from services.worker.agents.contracts import QualityStatus, StudentResponseAnalysis
from services.worker.cohort.contracts import CohortStatistics, MisconceptionCluster

TAXONOMY_TITLES: Dict[str, str] = {
    "MISC-ARITH-OFF-BY-ONE": "Off-by-One Interval Miscount",
    "MISC-DIR-INV": "Directional Vector Inversion",
    "MISC-MAG-COUNT": "Magnitude Miscount on Number Line",
    "MISC-SIGN-CONFUSION": "Signed Arithmetic Sign Confusion",
    "MISC-LINE-INTERVAL-MISLABEL": "Number-Line Interval Mislabel",
    "START_POINT_ZERO_MISUNDERSTANDING": "Origin Coordinate Confusion (Did not start at 0)",
    "INCORRECT_INTERVAL_MAGNITUDE": "Interval Magnitude Counting Slip (+6 instead of +12)",
    "COMPENSATORY_ARITHMETIC_ERROR": "Compensatory Arithmetic Error (Masked Slip)",
    "DIRECTION_SIGN_CONFUSION": "Signed Vector Direction Confusion",
    "REASONING_INCOMPLETE": "Incomplete Reasoning (Answer Only)",
    "FRAC-DIV-WRONG-GROUP-SIZE": "Fraction Division: Incorrect Divisor Group Size",
    "FRAC-DIV-RECIPROCAL-INVERSION": "Fraction Division: Divisor Reciprocal Confusion",
    "FRAC-DIV-UNIT-FORM-DISCONNECT": "Fraction Division: Unit Form & Diagram Disconnect",
    "REPRESENTATION-MISSING": "Missing Visual Model (Equation Only)",
    "VISUAL-MODEL-INCOMPLETE": "Incomplete Visual Diagram",
    "DEC-EST-MAGNITUDE-SLIP": "Decimal Estimation Magnitude Slip",
    "PLACE-VALUE-COLUMN-MISALIGN": "Place Value Unit Alignment Slip",
    "ARITHMETIC_SLIP": "Arithmetic Calculation Slip",
    "UNSUPPORTED_TASK": "Unsupported Mathematical Task Domain",
}


class CohortStatisticsCalculator:
    """Calculates deterministic statistics across student responses with exact denominators."""

    @classmethod
    def calculate(
        cls,
        responses: List[Union[StudentResponseAnalysis, Dict[str, Any]]],
    ) -> CohortStatistics:
        """Calculates exact cohort distributions, percentages, and clustered misconceptions."""
        total = len(responses)
        if total == 0:
            return CohortStatistics(
                total_responses=0,
                correct_count=0,
                correct_percentage=0.0,
                error_count=0,
                error_percentage=0.0,
                incomplete_count=0,
                incomplete_percentage=0.0,
                unreadable_count=0,
                unreadable_percentage=0.0,
                compensatory_errors_count=0,
                needs_teacher_review_count=0,
                insufficient_evidence_count=0,
                insufficient_evidence_percentage=0.0,
                misconception_clusters=[],
            )

        correct_count = 0
        error_count = 0
        incomplete_count = 0
        unreadable_count = 0
        compensatory_count = 0
        needs_review_count = 0
        insufficient_evidence_count = 0

        cluster_counts: Counter[str] = Counter()
        cluster_confirmed: Counter[str] = Counter()
        cluster_ai: Counter[str] = Counter()
        cluster_students: Dict[str, List[str]] = defaultdict(list)

        for r in responses:
            # Normalize to dict
            data = r.model_dump() if isinstance(r, StudentResponseAnalysis) else dict(r)

            resp_id = data.get("response_id", "unknown")
            quality = data.get("quality_status", "clear")
            if isinstance(quality, QualityStatus):
                quality = quality.value
            elif hasattr(quality, "value"):
                quality = quality.value
            quality = str(quality).lower()

            ans_status = data.get("answer_status", "undetermined")
            if hasattr(ans_status, "value"):
                ans_status = ans_status.value
            ans_status = str(ans_status).lower()

            reasoning_status = data.get("reasoning_status", "undetermined")
            if hasattr(reasoning_status, "value"):
                reasoning_status = reasoning_status.value
            reasoning_status = str(reasoning_status).lower()

            is_compensatory = bool(data.get("is_compensatory_error", False))
            needs_review = bool(data.get("needs_teacher_review", False))

            if is_compensatory:
                compensatory_count += 1
            if needs_review:
                needs_review_count += 1

            # Extract diagnosis object for evidence sufficiency
            diag = data.get("diagnosis", {})
            evidence_sufficiency = diag.get("evidence_sufficiency") if isinstance(diag, dict) else None
            if not evidence_sufficiency:
                evidence_sufficiency = data.get("evidence_sufficiency")

            is_insufficient = (
                evidence_sufficiency == "insufficient"
                or quality in ("corrupt", "unreadable")
                or (ans_status == "undetermined" and reasoning_status in ("incomplete", "undetermined"))
            )
            if is_insufficient:
                insufficient_evidence_count += 1

            # Categorize mutually exclusive student states
            if quality in ("corrupt", "unreadable") or ans_status == "undetermined":
                unreadable_count += 1
            elif reasoning_status == "incomplete":
                incomplete_count += 1
            elif ans_status == "correct" and reasoning_status == "supported_correct":
                correct_count += 1
            elif ans_status == "incorrect" or reasoning_status == "supported_error":
                error_count += 1
            else:
                # Fallback based on answer status
                if ans_status == "correct":
                    correct_count += 1
                else:
                    error_count += 1

            # Extract taxonomy ID
            tax_id = diag.get("misconception_taxonomy_id") if isinstance(diag, dict) else None
            if not tax_id:
                tax_id = data.get("misconception_taxonomy_id")

            # Check teacher override
            teacher_override_tax = data.get("teacher_override_taxonomy_id")
            review_status = data.get("teacher_review_status", "unreviewed")
            if review_status == "overridden" and teacher_override_tax:
                tax_id = teacher_override_tax
            elif review_status in ("marked_unreadable", "insufficient_evidence"):
                tax_id = None

            # Evidence-aware aggregation: only include supported diagnoses or specific taxonomy
            # in misconception clusters. Ambiguous/incomplete cases without taxonomy (e.g. Case 3)
            # must NEVER be counted as identified misconceptions.
            if tax_id and tax_id != "UNVERIFIABLE":
                cluster_counts[tax_id] += 1
                cluster_students[tax_id].append(resp_id)

                if review_status in ("approved_as_is", "overridden"):
                    cluster_confirmed[tax_id] += 1
                else:
                    cluster_ai[tax_id] += 1

        # Build sorted clusters
        clusters: List[MisconceptionCluster] = []
        for tax_id, count in cluster_counts.most_common():
            title = TAXONOMY_TITLES.get(tax_id, f"Misconception {tax_id}")
            pct = round((count / total) * 100.0, 1)
            clusters.append(
                MisconceptionCluster(
                    taxonomy_id=tax_id,
                    title=title,
                    affected_count=count,
                    affected_percentage=pct,
                    teacher_confirmed_count=cluster_confirmed[tax_id],
                    ai_proposed_count=cluster_ai[tax_id],
                    sample_response_ids=cluster_students[tax_id],
                )
            )

        return CohortStatistics(
            total_responses=total,
            correct_count=correct_count,
            correct_percentage=round((correct_count / total) * 100.0, 1),
            error_count=error_count,
            error_percentage=round((error_count / total) * 100.0, 1),
            incomplete_count=incomplete_count,
            incomplete_percentage=round((incomplete_count / total) * 100.0, 1),
            unreadable_count=unreadable_count,
            unreadable_percentage=round((unreadable_count / total) * 100.0, 1),
            compensatory_errors_count=compensatory_count,
            needs_teacher_review_count=needs_review_count,
            insufficient_evidence_count=insufficient_evidence_count,
            insufficient_evidence_percentage=round((insufficient_evidence_count / total) * 100.0, 1),
            misconception_clusters=clusters,
        )
