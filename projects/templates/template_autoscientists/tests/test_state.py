"""Tests for the shared-state records."""

from __future__ import annotations

from src.state import Champion, ExperimentOutcome, Proposal, SharedState


def _outcome(metric: float, delta: float, confirmed: bool, axis: int = 0, step: float = 0.5) -> ExperimentOutcome:
    return ExperimentOutcome(
        proposal=Proposal(axis=axis, step=step, rationale="r", proposer="t0"),
        params=(metric,),
        metric=metric,
        delta_vs_champion=delta,
        seed=7,
        confirmed=confirmed,
    )


def test_proposal_direction_label() -> None:
    assert Proposal(0, 0.5, "r", "t").direction == "increase"
    assert Proposal(0, -0.5, "r", "t").direction == "decrease"
    assert Proposal(0, 0.0, "r", "t").direction == "increase"


def test_outcome_improved_requires_confirmation_and_positive_delta() -> None:
    assert _outcome(1.0, 0.2, confirmed=True).improved is True
    assert _outcome(1.0, 0.2, confirmed=False).improved is False
    assert _outcome(1.0, -0.1, confirmed=True).improved is False
    assert _outcome(1.0, 0.0, confirmed=True).improved is False


def test_record_promotes_champion_on_improvement() -> None:
    state = SharedState(champion=Champion(params=(0.0,), metric=0.0, experiment_index=-1))
    state.record(_outcome(0.5, 0.5, confirmed=True))
    assert state.champion.metric == 0.5
    assert state.champion.experiment_index == 0
    assert state.best_so_far() == 0.5


def test_record_keeps_champion_when_not_improved() -> None:
    state = SharedState(champion=Champion(params=(0.0,), metric=0.3, experiment_index=-1))
    state.record(_outcome(0.1, -0.2, confirmed=True))
    assert state.champion.metric == 0.3
    assert len(state.log) == 1


def test_with_champion_resets_log() -> None:
    state = SharedState(champion=Champion(params=(0.0,), metric=0.0, experiment_index=-1))
    state.record(_outcome(0.5, 0.5, confirmed=True))
    fresh = state.with_champion(Champion(params=(1.0,), metric=9.0, experiment_index=-1))
    assert fresh.champion.metric == 9.0
    assert fresh.log == []
    # Original is untouched.
    assert len(state.log) == 1
