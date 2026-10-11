"""Independent numeric contract controls; no provider replacements."""

import json

import pytest

from template_autoscientists.agents.live_domain import (
    CoordinationFailed,
    LiveSettings,
    parse_proposal,
    proposal_schema,
    public_context,
    public_prompt,
)
from template_autoscientists.analysis.state import Champion, SharedState


@pytest.mark.parametrize(
    "field,value",
    [
        ("experiments_per_arm", True),
        ("experiments_per_arm", 3.5),
        ("experiments_per_arm", 2),
        ("experiments_per_arm", 7),
        ("num_predict", 513),
        ("num_predict", False),
        ("request_timeout_seconds", 61),
        ("run_timeout_seconds", 601),
        ("model", None),
        ("model", " "),
    ],
)
def test_limits_are_exact_typed_and_bounded(field, value) -> None:
    values = {"model": "fixture:latest", field: value}
    with pytest.raises(ValueError):
        LiveSettings(**values)


@pytest.mark.parametrize(
    "payload",
    [
        {"axis": True, "step": -0.5, "rationale": "x"},
        {"axis": "0", "step": -0.5, "rationale": "x"},
        {"axis": 9, "step": -0.5, "rationale": "x"},
        {"axis": 0, "step": True, "rationale": "x"},
        {"axis": 0, "step": 0, "rationale": "x"},
        {"axis": 0, "step": 1.1, "rationale": "x"},
        {"axis": 0, "step": float("inf"), "rationale": "x"},
        {"axis": 0, "step": float("nan"), "rationale": "x"},
        {"axis": 0, "step": -0.5, "rationale": None},
        {"axis": 0, "step": -0.5, "rationale": " "},
        {"axis": 0, "step": -0.5, "rationale": "x" * 2049},
        {"axis": 0, "step": -0.5, "rationale": "x", "code": "print(1)"},
        [],
    ],
)
def test_invalid_provider_proposals_fail_closed(payload) -> None:
    with pytest.raises(CoordinationFailed):
        parse_proposal(json.dumps(payload), [0, 1], "team0", frozenset())


@pytest.mark.parametrize("raw", ["prefix {}", "{} trailing", '{"axis":0,"axis":1,"step":0.5,"rationale":"x"}'])
def test_chatter_and_duplicate_keys_are_not_repaired(raw: str) -> None:
    with pytest.raises(CoordinationFailed):
        parse_proposal(raw, [0, 1], "team0", frozenset())


def test_retired_direction_rejected_and_state_prompt_bound() -> None:
    state = SharedState(Champion((1.5, 1.5), -4.5, -1))
    avoid = frozenset({(0, "decrease")})
    context = public_context(state, [0], "team0", avoid)
    prompt = public_prompt(context)
    assert json.loads(prompt.split("\n", 1)[1]) == context
    assert context["experiment_log"] == []
    assert proposal_schema([0])["properties"]["axis"]["enum"] == [0]
    with pytest.raises(CoordinationFailed, match="retired"):
        parse_proposal('{"axis":0,"step":-0.5,"rationale":"x"}', [0], "team0", avoid)
    proposal = parse_proposal('{"axis":0,"step":0.5,"rationale":"x"}', [0], "team0", avoid)
    assert proposal.direction == "increase"
