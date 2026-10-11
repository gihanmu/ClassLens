"""Unit tests for Cohort Statistics, Misconception Clustering, and Exit Ticket Verification."""

from __future__ import annotations

import pytest

from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.cohort.contracts import CohortStatistics
from services.worker.cohort.exit_ticket_validator import ExitTicketValidator
from services.worker.cohort.statistics_calculator import CohortStatisticsCalculator
from services.worker.cohort.synthesizer import CohortSynthesizer
from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES


@pytest.fixture
def analyzed_13_responses():
    """Runs the 13 mock fixtures through the multi-agent pipeline."""
    return [
        MultiAgentPipeline.analyze_response(resp_id)
        for resp_id in MOCK_FIXTURES.keys()
    ]


def test_tc_006_01_exact_frequencies(analyzed_13_responses):
    """TC-006.01: Verifies exact frequency counts and percentages across 13 responses."""
    stats: CohortStatistics = CohortStatisticsCalculator.calculate(analyzed_13_responses)

    assert stats.total_responses == 13
    assert stats.correct_count == 7
    assert stats.correct_percentage == 53.8

    assert stats.error_count == 4
    assert stats.error_percentage == 30.8

    assert stats.unreadable_count == 1
    assert stats.unreadable_percentage == 7.7

    assert stats.incomplete_count == 1
    assert stats.incomplete_percentage == 7.7

    # Total student states sum to 13
    assert (
        stats.correct_count
        + stats.error_count
        + stats.unreadable_count
        + stats.incomplete_count
    ) == 13


def test_tc_006_02_misconception_clustering(analyzed_13_responses):
    """TC-006.02: Verifies misconception clustering and dominant cluster identification."""
    stats: CohortStatistics = CohortStatisticsCalculator.calculate(analyzed_13_responses)

    assert len(stats.misconception_clusters) >= 3

    # Dominant cluster must be MISC-ARITH-OFF-BY-ONE with exactly 2 students
    dominant = stats.misconception_clusters[0]
    assert dominant.taxonomy_id == "MISC-ARITH-OFF-BY-ONE"
    assert dominant.affected_count == 2
    assert dominant.affected_percentage == 15.4

    # Ranking must be in descending order
    counts = [c.affected_count for c in stats.misconception_clusters]
    assert counts == sorted(counts, reverse=True)


def test_tc_006_03_sympy_exit_ticket_verification():
    """TC-006.03: Verifies all generated exit ticket questions evaluate to True using SymPy."""
    dummy_stats = CohortStatistics(
        total_responses=13,
        correct_count=7,
        correct_percentage=53.8,
        error_count=4,
        error_percentage=30.8,
        incomplete_count=1,
        incomplete_percentage=7.7,
        unreadable_count=1,
        unreadable_percentage=7.7,
        misconception_clusters=[],
    )

    intelligence = CohortSynthesizer.synthesize_insights(dummy_stats)

    assert len(intelligence.formative_exit_ticket) == 3
    for item in intelligence.formative_exit_ticket:
        assert item.sympy_verified is True, f"Item {item.question_number} failed SymPy check"
        assert item.prompt is not None
        assert item.expected_answer is not None


def test_cohort_empty_responses():
    """Verifies graceful handling of empty response list."""
    stats = CohortStatisticsCalculator.calculate([])
    assert stats.total_responses == 0
    assert stats.correct_count == 0
    assert stats.correct_percentage == 0.0
    assert stats.misconception_clusters == []


def test_cohort_synthesizer_narrative_and_actions(analyzed_13_responses):
    """Verifies that CohortSynthesizer produces narrative and differentiated actions."""
    stats = CohortStatisticsCalculator.calculate(analyzed_13_responses)
    intelligence = CohortSynthesizer.synthesize_insights(stats)

    assert "7/13" in intelligence.executive_narrative
    assert "Off-by-One" in intelligence.executive_narrative
    assert len(intelligence.differentiated_actions) == 3
    assert len(intelligence.dominant_misconceptions) <= 2
