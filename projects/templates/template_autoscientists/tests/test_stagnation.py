"""Tests for stagnation detection and team reorganization."""

from __future__ import annotations

import pytest

from src.dead_ends import DeadEndRegistry
from src.stagnation import StagnationDetector, reorganize_axes
from src.state import Champion, ExperimentOutcome, Proposal, SharedState


def _state_with(deltas_confirmed: list[tuple[float, bool]]) -> SharedState:
    state = SharedState(champion=Champion(params=(0.0,), metric=0.0, experiment_index=-1))
    for delta, confirmed in deltas_confirmed:
        state.log.append(
            ExperimentOutcome(
                proposal=Proposal(axis=0, step=0.5, rationale="r", proposer="t"),
                params=(0.0,),
                metric=0.0,
                delta_vs_champion=delta,
                seed=7,
                confirmed=confirmed,
            )
        )
    return state


def test_not_stagnant_before_window_filled() -> None:
    detector = StagnationDetector(window=5)
    state = _state_with([(-0.1, True)] * 3)
    assert detector.is_stagnant(state) is False


def test_stagnant_when_no_improvement_in_window() -> None:
    detector = StagnationDetector(window=3)
    state = _state_with([(0.5, True), (-0.1, True), (-0.2, True), (-0.3, True)])
    assert detector.is_stagnant(state) is True


def test_recent_improvement_clears_stagnation() -> None:
    detector = StagnationDetector(window=3)
    state = _state_with([(-0.1, True), (-0.2, True), (0.4, True)])
    assert detector.is_stagnant(state) is False


def test_window_must_be_positive() -> None:
    with pytest.raises(ValueError, match="window must be >= 1"):
        StagnationDetector(window=0)


def test_reorganize_drops_fully_retired_axes() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(1, "increase")
    reg.record_failure(1, "decrease")
    teams = reorganize_axes([0, 1, 2, 3], num_teams=2, registry=reg)
    flat = [axis for team in teams for axis in team]
    assert 1 not in flat
    assert sorted(flat) == [0, 2, 3]


def test_reorganize_keeps_axis_with_one_live_direction() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(1, "increase")  # decrease still live
    teams = reorganize_axes([0, 1], num_teams=1, registry=reg)
    assert teams == [[0, 1]]


def test_reorganize_round_robin_partition() -> None:
    reg = DeadEndRegistry(threshold=1)
    teams = reorganize_axes([0, 1, 2, 3], num_teams=2, registry=reg)
    assert teams == [[0, 2], [1, 3]]


def test_reorganize_requires_positive_teams() -> None:
    with pytest.raises(ValueError, match="num_teams must be >= 1"):
        reorganize_axes([0, 1], num_teams=0, registry=DeadEndRegistry())


def test_stagnation_requires_positive_delta_to_clear() -> None:
    """Negative control: confirmed=True with delta<=0 does not clear stagnation.

    ``outcome.improved`` requires *both* ``confirmed=True`` AND
    ``delta_vs_champion > 0.0``.  A confirmed non-improvement (delta <= 0)
    must not be counted as an improvement that breaks the stagnation streak.
    """
    detector = StagnationDetector(window=3)
    # Three outcomes that are confirmed but NOT improving (delta == 0 or negative).
    state = _state_with([(0.0, True), (-0.1, True), (0.0, True)])
    # None of the outcomes have delta > 0, so none are improving.
    assert detector.is_stagnant(state) is True


def test_stagnation_not_cleared_by_unconfirmed_positive_delta() -> None:
    """Negative control: a positive delta that fails confirmation does not clear stagnation.

    An outcome with confirmed=False is not an improvement even when its
    delta_vs_champion is positive.
    """
    detector = StagnationDetector(window=3)
    # Three outcomes: positive delta but confirmed=False (noise-rejected).
    state = _state_with([(0.3, False), (0.5, False), (0.2, False)])
    assert detector.is_stagnant(state) is True


def test_reorganize_all_axes_fully_retired_returns_empty_teams() -> None:
    """Negative control: when every axis is fully retired all teams are empty."""
    reg = DeadEndRegistry(threshold=1)
    for axis in (0, 1):
        reg.record_failure(axis, "increase")
        reg.record_failure(axis, "decrease")
    teams = reorganize_axes([0, 1], num_teams=2, registry=reg)
    assert teams == [[], []]
