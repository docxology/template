"""Tests for proposer agents.

The deterministic policy is tested with actual state and outcomes. Bounded
local-model parsing and transport contracts have separate tests.
"""

from __future__ import annotations

import pytest

from template_autoscientists.agents.agents import DeterministicProposer
from template_autoscientists.analysis.state import Champion, ExperimentOutcome, Proposal, SharedState


def _state(champion_params: tuple[float, ...]) -> SharedState:
    return SharedState(champion=Champion(params=champion_params, metric=0.0, experiment_index=-1))


def test_deterministic_step_must_be_positive() -> None:
    with pytest.raises(ValueError, match="step must be positive"):
        DeterministicProposer(step=0.0)


def test_deterministic_requires_axes() -> None:
    proposer = DeterministicProposer()
    with pytest.raises(ValueError, match="axes must be non-empty"):
        proposer.propose(_state((1.0,)), [], "t0")


def test_deterministic_probes_toward_origin_by_default() -> None:
    proposer = DeterministicProposer(step=0.5)
    # Champion is positive on axis 0 -> default probe is downhill (negative).
    proposal = proposer.propose(_state((2.0, 2.0)), [0, 1], "t0")
    assert proposal.axis == 0
    assert proposal.step == -0.5
    assert proposal.proposer == "t0"
    assert "down" in proposal.rationale


def test_deterministic_probes_up_when_champion_negative() -> None:
    proposer = DeterministicProposer(step=0.5)
    proposal = proposer.propose(_state((-2.0,)), [0], "t0")
    assert proposal.step == 0.5
    assert "up" in proposal.rationale


def test_deterministic_round_robins_axes_by_log_length() -> None:
    proposer = DeterministicProposer()
    state = _state((1.0, 1.0, 1.0))
    assert proposer.propose(state, [0, 1, 2], "t0").axis == 0
    state.log.append(_dummy_outcome(axis=0))
    assert proposer.propose(state, [0, 1, 2], "t0").axis == 1


def test_deterministic_follows_last_improving_sign() -> None:
    proposer = DeterministicProposer(step=0.5)
    state = _state((2.0,))
    # An earlier improvement came from stepping *up* on axis 0.
    state.log.append(
        ExperimentOutcome(
            proposal=Proposal(axis=0, step=0.5, rationale="r", proposer="t"),
            params=(2.5,),
            metric=1.0,
            delta_vs_champion=0.3,
            seed=7,
            confirmed=True,
        )
    )
    # log length is now 1 -> with a single axis it still selects axis 0.
    proposal = proposer.propose(state, [0], "t0")
    assert proposal.step == 0.5  # reuses the improving (up) sign


def test_deterministic_flips_away_from_retired_direction() -> None:
    proposer = DeterministicProposer(step=0.5)
    # Default probe on a positive champion is downhill (decrease); retiring that
    # direction forces the proposer onto the still-live increase direction.
    proposal = proposer.propose(_state((2.0,)), [0], "t0", avoid=frozenset({(0, "decrease")}))
    assert proposal.step == 0.5
    assert "up" in proposal.rationale


def test_deterministic_keeps_direction_when_both_retired() -> None:
    proposer = DeterministicProposer(step=0.5)
    # Nowhere live to go: the proposer keeps its default rather than flipping
    # onto another retired direction.
    proposal = proposer.propose(_state((2.0,)), [0], "t0", avoid=frozenset({(0, "increase"), (0, "decrease")}))
    assert proposal.step == -0.5


def _dummy_outcome(axis: int) -> ExperimentOutcome:
    return ExperimentOutcome(
        proposal=Proposal(axis=axis, step=0.5, rationale="r", proposer="t"),
        params=(0.0,),
        metric=0.0,
        delta_vs_champion=-0.1,
        seed=7,
        confirmed=False,
    )
