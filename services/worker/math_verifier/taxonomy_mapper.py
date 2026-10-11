"""Evidence-grounded pedagogical misconception classification."""

from __future__ import annotations

from typing import Optional, Tuple


class TaxonomyMapper:
    """Classifies mathematical deviations and geometric anomalies into standardized taxonomy codes."""

    TAXONOMY_DESCRIPTIONS = {
        "MISC-NUM-DIR-REVERSE": "Directional sign reversal on number line (moved opposite to addend sign)",
        "MISC-ARITH-OFF-BY-ONE": "Counting off-by-one magnitude error on number line",
        "MISC-LINE-INTERVAL-MISLABEL": "Mislabeled number line intervals or irregular coordinate spacing",
        "MISC-ARITH-SLIP": "Arithmetic calculation or hop displacement discrepancy",
        "REASONING_INCOMPLETE": "Incomplete number line reasoning; required working or hops missing",
        "REASONING_DISCONTINUOUS": "Path discontinuity between consecutive number line hops",
        "REASONING_CONTRADICTORY": "Contradiction between drawn arrow direction and coordinate displacement",
    }

    @classmethod
    def classify_step_deviation(
        cls,
        expected_displacement: float,
        observed_displacement: float,
        stated_magnitude: Optional[float] = None,
        has_interval_mislabel: bool = False,
        tolerance: float = 1e-4,
    ) -> Tuple[str, str]:
        """Classifies the deviation of a single hop from expected displacement.

        Args:
            expected_displacement: Mathematically required coordinate displacement.
            observed_displacement: Measured coordinate displacement on number line.
            stated_magnitude: Explicit student written magnitude if present.
            has_interval_mislabel: Explicit flag if number line tick intervals are irregular.
            tolerance: Floating point numerical comparison tolerance.

        Returns:
            Tuple of (taxonomy_id, evidence_notes).
        """
        # If external observation explicitly notes tick mislabeling or stated magnitude mismatch
        if has_interval_mislabel:
            return (
                "MISC-LINE-INTERVAL-MISLABEL",
                "Irregular tick intervals or mislabeled integers detected on student number line.",
            )

        if stated_magnitude is not None:
            # If stated magnitude equals expected magnitude but coordinate displacement was different
            if (
                abs(stated_magnitude - abs(expected_displacement)) <= tolerance
                and abs(abs(observed_displacement) - abs(expected_displacement)) > tolerance
            ):
                return (
                    "MISC-LINE-INTERVAL-MISLABEL",
                    f"Student intended magnitude {stated_magnitude}, but drawn coordinates yield {abs(observed_displacement)} due to mislabeled intervals.",
                )

        # Check for directional sign reversal (hop in opposite direction)
        if abs(observed_displacement + expected_displacement) <= tolerance and abs(expected_displacement) > tolerance:
            return (
                "MISC-NUM-DIR-REVERSE",
                f"Direction reversed: observed {observed_displacement:+} instead of expected {expected_displacement:+}.",
            )

        # Check if vectors point in opposite directions
        if (expected_displacement * observed_displacement) < -tolerance:
            return (
                "MISC-NUM-DIR-REVERSE",
                f"Opposite directional movement: observed {observed_displacement:+} vs expected {expected_displacement:+}.",
            )

        # Check for off-by-one magnitude or displacement count error
        mag_diff = abs(abs(observed_displacement) - abs(expected_displacement))
        if abs(mag_diff - 1.0) <= tolerance:
            return (
                "MISC-ARITH-OFF-BY-ONE",
                f"Off-by-one magnitude count: hopped {abs(observed_displacement):g} units instead of {abs(expected_displacement):g}.",
            )

        disp_diff = abs(observed_displacement - expected_displacement)
        if abs(disp_diff - 1.0) <= tolerance:
            return (
                "MISC-ARITH-OFF-BY-ONE",
                f"Off-by-one arithmetic error: coordinate deviation is {observed_displacement - expected_displacement:+g}.",
            )

        # General arithmetic slip fallback
        return (
            "MISC-ARITH-SLIP",
            f"Arithmetic slip: observed displacement {observed_displacement:+g} deviates from expected {expected_displacement:+g} by {observed_displacement - expected_displacement:+g}.",
        )

    @classmethod
    def classify_empty_reasoning(cls) -> Tuple[str, str]:
        """Returns taxonomy for missing or empty reasoning working."""
        return (
            "REASONING_INCOMPLETE",
            "No number line hops or mathematical working visible on student response.",
        )

    @classmethod
    def classify_discontinuity(cls, gap: float, step: int) -> Tuple[str, str]:
        """Returns taxonomy for a jump/gap between steps."""
        return (
            "REASONING_DISCONTINUOUS",
            f"Path discontinuity at step {step}: hop starts at {gap:+g} units away from previous endpoint.",
        )

    @classmethod
    def classify_contradiction(
        cls, step: int, direction: str, delta: float
    ) -> Tuple[str, str]:
        """Returns taxonomy for arrow direction contradicting coordinate displacement."""
        return (
            "REASONING_CONTRADICTORY",
            f"Step {step} drawn arrow direction '{direction}' contradicts coordinate delta {delta:+g}.",
        )
