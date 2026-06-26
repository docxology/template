"""Tests for proposer agents.

The deterministic proposer and the Hermes reply parser are tested without any
mocks. The live ``HermesProposer.propose`` path is covered separately by the
``requires_ollama`` test in ``test_hermes_live.py``.
"""

from __future__ import annotations

import pytest

from hermes_proposer import HermesProposer

from src.agents import DeterministicProposer, _extract_json
from src.state import Champion, ExperimentOutcome, Proposal, SharedState


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


def test_hermes_prompt_lists_retired_directions() -> None:
    proposer = HermesProposer()
    prompt = proposer._prompt(_state((1.0, 2.0)), axes=[0, 1], avoid=frozenset({(1, "increase")}))
    assert "Retired directions to avoid: axis 1 increase" in prompt


def _dummy_outcome(axis: int) -> ExperimentOutcome:
    return ExperimentOutcome(
        proposal=Proposal(axis=axis, step=0.5, rationale="r", proposer="t"),
        params=(0.0,),
        metric=0.0,
        delta_vs_champion=-0.1,
        seed=7,
        confirmed=False,
    )


def test_extract_json_pulls_object_from_chatter() -> None:
    raw = 'Sure! Here is my answer:\n{"axis": 1, "step": 0.5}\nHope that helps.'
    assert _extract_json(raw) == '{"axis": 1, "step": 0.5}'


def test_extract_json_raises_without_object() -> None:
    with pytest.raises(ValueError, match="no JSON object found"):
        _extract_json("there is no json here")


def test_hermes_parse_valid_reply() -> None:
    proposer = HermesProposer()
    raw = '{"axis": 2, "step": -0.75, "rationale": "go down"}'
    proposal = proposer._parse(raw, axes=[0, 1, 2], proposer_id="hermes0")
    assert proposal.axis == 2
    assert proposal.step == -0.75
    assert proposal.rationale == "go down"
    assert proposal.proposer == "hermes0"


def test_hermes_parse_defaults_blank_rationale() -> None:
    proposer = HermesProposer()
    proposal = proposer._parse('{"axis": 0, "step": 0.5}', axes=[0], proposer_id="h")
    assert proposal.rationale == "hermes proposal"


def test_hermes_parse_rejects_out_of_scope_axis() -> None:
    proposer = HermesProposer()
    with pytest.raises(ValueError, match="outside assigned"):
        proposer._parse('{"axis": 9, "step": 0.5}', axes=[0, 1], proposer_id="h")


def test_hermes_prompt_includes_state_and_axes() -> None:
    proposer = HermesProposer()
    state = _state((1.0, 2.0))
    prompt = proposer._prompt(state, axes=[0, 1])
    assert "Axes you may modify: [0, 1]" in prompt
    assert "(none)" in prompt  # empty history


def test_hermes_prompt_renders_recent_history() -> None:
    proposer = HermesProposer()
    state = _state((1.0,))
    state.log.append(
        ExperimentOutcome(
            proposal=Proposal(axis=0, step=0.5, rationale="r", proposer="t"),
            params=(1.5,),
            metric=0.9,
            delta_vs_champion=0.2,
            seed=7,
            confirmed=True,
        )
    )
    prompt = proposer._prompt(state, axes=[0])
    assert "axis=0" in prompt
    assert "confirmed=True" in prompt


def test_hermes_parse_rejects_out_of_scope_axis_negative_control() -> None:
    """Negative control: a reply with an axis outside the assigned set must be rejected."""
    proposer = HermesProposer()
    # axes=[0, 1] but the model replied with axis=5.
    with pytest.raises(ValueError, match="outside assigned"):
        proposer._parse('{"axis": 5, "step": 1.0}', axes=[0, 1], proposer_id="h")


def test_hermes_parse_negative_step_is_accepted() -> None:
    """Negative step values are valid (they probe in the decrease direction)."""
    proposer = HermesProposer()
    proposal = proposer._parse('{"axis": 0, "step": -1.0, "rationale": "go down"}', axes=[0], proposer_id="h")
    assert proposal.step == -1.0
    assert proposal.direction == "decrease"


def test_extract_json_with_nested_braces() -> None:
    """_extract_json uses outermost { ... } so nested content is kept."""
    raw = 'prefix {"outer": {"inner": 1}} suffix'
    extracted = _extract_json(raw)
    assert extracted == '{"outer": {"inner": 1}}'


def test_extract_json_rejects_trailing_brace_only() -> None:
    """_extract_json raises when there is a } but no { (end < start impossible)."""
    with pytest.raises(ValueError, match="no JSON object found"):
        _extract_json("} no opening brace")
