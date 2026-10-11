"""Geometric and vector displacement calculations on a 1D number line."""

from __future__ import annotations

from typing import List, Tuple
from services.worker.math_verifier.contracts import NumberLineHop


class NumberLineDisplacementCalculator:
    """Calculates vector displacements, direction consistency, and path continuity on a 1D number line."""

    @staticmethod
    def compute_displacements(hops: List[NumberLineHop]) -> List[float]:
        """Extracts ordered signed displacements [Δx_0, Δx_1, ...] from hops.

        Args:
            hops: List of NumberLineHop items.

        Returns:
            List of signed displacements.
        """
        return [hop.displacement for hop in hops]

    @staticmethod
    def check_direction_consistency(hop: NumberLineHop) -> bool:
        """Verifies whether the drawn arrow head matches the signed coordinate displacement.

        Args:
            hop: NumberLineHop to check.

        Returns:
            True if direction matches sign (or is 'none' on zero delta), False if contradictory.
        """
        delta = hop.displacement
        if delta > 0 and hop.direction == "left":
            return False
        if delta < 0 and hop.direction == "right":
            return False
        return True

    @staticmethod
    def check_path_continuity(
        hops: List[NumberLineHop], tolerance: float = 1e-4
    ) -> Tuple[bool, List[int]]:
        """Checks if each consecutive hop starts where the previous hop ended.

        Args:
            hops: Sequence of number line hops.
            tolerance: Float comparison tolerance.

        Returns:
            (is_continuous, list_of_discontinuous_step_indices)
        """
        if len(hops) <= 1:
            return True, []

        discontinuities = []
        for i in range(1, len(hops)):
            prev_end = hops[i - 1].end
            curr_start = hops[i].start
            if abs(curr_start - prev_end) > tolerance:
                discontinuities.append(i + 1)  # 1-indexed step number

        return len(discontinuities) == 0, discontinuities
