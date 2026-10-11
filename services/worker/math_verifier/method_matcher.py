"""Pedagogical method identification and solution path matching."""

from __future__ import annotations

import itertools
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from services.worker.math_verifier.contracts import NumberLineHop, QuestionRule


class MatchedMethod(BaseModel):
    """Result of matching student hops against valid mathematical solution paths."""

    method_name: Literal["hop_from_zero", "direct_start", "commutative", "unrecognized"]
    expected_start: Optional[float] = None
    expected_displacements: List[float] = Field(default_factory=list)
    is_exact_match: bool = False
    matching_step_count: int = 0


class MethodMatcher:
    """Matches observed student number line hops against canonical mathematical strategies."""

    @classmethod
    def match(cls, hops: List[NumberLineHop], rule: QuestionRule) -> MatchedMethod:
        """Determines the student's solution method and aligned expected displacements.

        Args:
            hops: List of observed student NumberLineHop objects.
            rule: Question specification with expected addends and rules.

        Returns:
            MatchedMethod with identified method and expected displacement sequence.
        """
        if not hops or not rule.expected_addends:
            return MatchedMethod(
                method_name="unrecognized",
                expected_start=None,
                expected_displacements=[],
                is_exact_match=False,
                matching_step_count=0,
            )

        student_start = hops[0].start
        student_displacements = [hop.displacement for hop in hops]
        num_hops = len(hops)
        tolerance = rule.tolerance
        addends = rule.expected_addends

        # Build all plausible candidate strategies
        candidates: List[Tuple[str, float, List[float]]] = []

        # 1. Hop from zero: starts at 0, applies addends in original order
        candidates.append(("hop_from_zero", 0.0, list(addends)))

        # 2. Direct start at first term: starts at addends[0], applies remaining addends
        if rule.allow_direct_start and len(addends) > 1:
            candidates.append(("direct_start", float(addends[0]), list(addends[1:])))

        # 3. Commutative paths
        if rule.allow_commutative and len(addends) > 1:
            # Type 3a: Direct start at another term addends[k]
            for idx in range(1, len(addends)):
                start_val = float(addends[idx])
                remaining = addends[:idx] + addends[idx + 1:]
                # Test remaining in original order and permutations (up to 4 terms)
                if len(remaining) <= 4:
                    for perm in set(itertools.permutations(remaining)):
                        candidates.append(("commutative", start_val, list(perm)))
                else:
                    candidates.append(("commutative", start_val, remaining))

            # Type 3b: Hop from zero with permuted addends
            if len(addends) <= 5:
                for perm in set(itertools.permutations(addends)):
                    perm_list = list(perm)
                    if perm_list != addends:
                        candidates.append(("commutative", 0.0, perm_list))

        # Check for an exact match first
        for method_name, exp_start, exp_disps in candidates:
            if abs(student_start - exp_start) <= tolerance and len(student_displacements) == len(exp_disps):
                all_steps_match = True
                for obs_d, exp_d in zip(student_displacements, exp_disps):
                    if abs(obs_d - exp_d) > tolerance:
                        all_steps_match = False
                        break
                if all_steps_match:
                    return MatchedMethod(
                        method_name=method_name,  # type: ignore[arg-type]
                        expected_start=exp_start,
                        expected_displacements=exp_disps,
                        is_exact_match=True,
                        matching_step_count=len(exp_disps),
                    )

        # If no exact match, find candidate that best explains student's attempt
        best_candidate: Optional[Tuple[str, float, List[float]]] = None
        best_score = -1.0
        best_match_count = 0

        for method_name, exp_start, exp_disps in candidates:
            start_matches = abs(student_start - exp_start) <= tolerance
            count_matches = num_hops == len(exp_disps)

            matching_steps = 0
            min_len = min(num_hops, len(exp_disps))
            for i in range(min_len):
                if abs(student_displacements[i] - exp_disps[i]) <= tolerance:
                    matching_steps += 1

            # Scoring heuristic:
            # - matching start point: +10 points
            # - matching step count: +5 points
            # - each matching step: +4 points
            score = (10.0 if start_matches else 0.0) + (5.0 if count_matches else 0.0) + (matching_steps * 4.0)

            # Prioritize standard order hop_from_zero when tie occurs
            if method_name == "hop_from_zero":
                score += 0.5

            if score > best_score:
                best_score = score
                best_candidate = (method_name, exp_start, exp_disps)
                best_match_count = matching_steps

        # Threshold: if student start matched or at least one step matched, accept candidate
        if best_candidate and best_score >= 10.0:
            m_name, exp_s, exp_d = best_candidate
            return MatchedMethod(
                method_name=m_name,  # type: ignore[arg-type]
                expected_start=exp_s,
                expected_displacements=exp_d,
                is_exact_match=False,
                matching_step_count=best_match_count,
            )

        # Fallback to hop_from_zero template if start is close to zero
        if abs(student_start - 0.0) <= 2.0:
            return MatchedMethod(
                method_name="hop_from_zero",
                expected_start=0.0,
                expected_displacements=list(addends),
                is_exact_match=False,
                matching_step_count=0,
            )

        return MatchedMethod(
            method_name="unrecognized",
            expected_start=None,
            expected_displacements=list(addends),
            is_exact_match=False,
            matching_step_count=0,
        )
