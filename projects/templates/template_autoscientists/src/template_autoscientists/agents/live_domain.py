"""Strict numeric proposals and public shared-state prompts; no executable output."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from ..analysis.state import Proposal, SharedState


class CoordinationBlocked(ValueError):
    """Required installed local capability or bounded time is unavailable."""


class CoordinationFailed(ValueError):
    """A responding provider or scientific acceptance contract failed."""


@dataclass(frozen=True)
class LiveSettings:
    """Equal ceilings for both arms, with no model acquisition or paid calls."""

    model: str
    endpoint: str = "http://127.0.0.1:11434"
    experiments_per_arm: int = 6
    num_predict: int = 512
    request_timeout_seconds: int = 60
    run_timeout_seconds: int = 600

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("an explicitly selected installed model is required")
        for name, low, high in (
            ("experiments_per_arm", 3, 6),
            ("num_predict", 64, 512),
            ("request_timeout_seconds", 1, 60),
            ("run_timeout_seconds", 1, 600),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in [{low},{high}]")


def proposal_schema(axes: Sequence[int]) -> dict[str, object]:
    """Constrain generation as well as independently validating its output."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "axis": {"type": "integer", "enum": list(axes)},
            "step": {"type": "number", "minimum": -1, "maximum": 1},
            "rationale": {"type": "string", "minLength": 1, "maxLength": 2048},
        },
        "required": ["axis", "step", "rationale"],
    }


def parse_proposal(raw: str, axes: Sequence[int], proposer_id: str, avoid: frozenset[tuple[int, str]]) -> Proposal:
    """Reject chatter, duplicate keys, coercions, retired directions, and code."""

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate proposal key")
            result[key] = value
        return result

    try:
        payload = json.loads(raw, object_pairs_hook=unique)
    except ValueError as exc:
        raise CoordinationFailed("proposal must be exactly one JSON object") from exc
    if not isinstance(payload, dict) or set(payload) != {"axis", "step", "rationale"}:
        raise CoordinationFailed("proposal requires exactly axis, step, rationale; code and paths are forbidden")
    axis, step, rationale = payload["axis"], payload["step"], payload["rationale"]
    if type(axis) is not int or axis not in axes:
        raise CoordinationFailed("proposal axis must be an integer inside assigned axes")
    if type(step) not in (int, float) or not math.isfinite(step) or not 0 < abs(step) <= 1:
        raise CoordinationFailed("proposal step must be finite, nonzero, and in [-1,1]")
    if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 2048:
        raise CoordinationFailed("proposal rationale must be a bounded nonempty string")
    proposal = Proposal(axis=axis, step=float(step), rationale=rationale, proposer=proposer_id)
    if (axis, proposal.direction) in avoid:
        raise CoordinationFailed("proposal uses a retired direction")
    return proposal


def public_context(
    state: SharedState, axes: Sequence[int], proposer_id: str, avoid: frozenset[tuple[int, str]]
) -> dict[str, object]:
    """Bind every generation to the actual preceding shared state and assignment."""
    context = {
        "proposer": proposer_id,
        "assigned_axes": list(axes),
        "champion": asdict(state.champion),
        "experiment_log": [asdict(outcome) for outcome in state.log],
        "retired_directions": [list(item) for item in sorted(avoid)],
    }
    # JSON-normalize tuples so the stored context equals the actual prompt data.
    normalized: dict[str, object] = json.loads(json.dumps(context, allow_nan=False))
    return normalized


def public_prompt(context: dict[str, object]) -> str:
    """Only the synthetic public state enters prompts, never clean-score labels."""
    return (
        "Propose one numeric experiment to maximize the observed metric. "
        "Read the shared champion, preceding outcomes, assigned axes, and retired directions. "
        "Change exactly one assigned axis by a finite nonzero step in [-1,1]. "
        "Avoid every retired direction. Return only JSON with axis, step, rationale. "
        "No code, file paths, commands, or additional keys.\n" + json.dumps(context, sort_keys=True, allow_nan=False)
    )
