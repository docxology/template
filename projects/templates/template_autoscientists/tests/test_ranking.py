"""Tests for effect-size ranking."""

from __future__ import annotations

import pytest

from src.ranking import axis_effect_sizes, rank_axes
from src.state import ExperimentOutcome, Proposal


def _outcome(axis: int, delta: float) -> ExperimentOutcome:
    return ExperimentOutcome(
        proposal=Proposal(axis=axis, step=0.5, rationale="r", proposer="t"),
        params=(0.0,),
        metric=0.0,
        delta_vs_champion=delta,
        seed=7,
        confirmed=True,
    )


def test_effect_size_is_mean_absolute_delta() -> None:
    log = [_outcome(0, 0.4), _outcome(0, -0.2), _outcome(1, 0.1)]
    effects = axis_effect_sizes(log, [0, 1, 2])
    assert effects[0] == pytest.approx(0.3)
    assert effects[1] == pytest.approx(0.1)
    assert effects[2] == 0.0


def test_effect_size_ignores_outcomes_outside_requested_axes() -> None:
    log = [_outcome(5, 0.9), _outcome(0, 0.2)]
    effects = axis_effect_sizes(log, [0])
    assert effects == {0: pytest.approx(0.2)}


def test_untried_axes_sort_first() -> None:
    log = [_outcome(0, 0.5), _outcome(1, 0.1)]
    # Axis 2 is untried -> first; among tried, larger effect first.
    assert rank_axes(log, [0, 1, 2]) == [2, 0, 1]


def test_ties_break_by_index() -> None:
    log = [_outcome(0, 0.3), _outcome(1, 0.3)]
    assert rank_axes(log, [1, 0]) == [0, 1]


def test_empty_log_keeps_index_order() -> None:
    assert rank_axes([], [3, 1, 2]) == [1, 2, 3]


def test_single_axis_returns_singleton() -> None:
    """Edge case: one axis is always first regardless of log content."""
    assert rank_axes([], [7]) == [7]
    assert rank_axes([_outcome(7, 0.5)], [7]) == [7]


def test_all_tried_with_equal_effect_breaks_by_index() -> None:
    """When every axis has been tried and all effects are equal, sort by index."""
    log = [_outcome(2, 0.3), _outcome(0, 0.3), _outcome(1, 0.3)]
    assert rank_axes(log, [0, 1, 2]) == [0, 1, 2]


def test_axis_absent_from_requested_axes_is_excluded() -> None:
    """axis_effect_sizes ignores outcomes for axes not in the requested set."""
    log = [_outcome(99, 5.0)]
    effects = axis_effect_sizes(log, [0, 1])
    assert 99 not in effects
    assert effects == {0: 0.0, 1: 0.0}
