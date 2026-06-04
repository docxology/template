"""Proposer agents and the language-model plug-in seam.

The search loop depends only on the :class:`Proposer` protocol. Two real
implementations are provided:

* :class:`DeterministicProposer` — a rule-based policy used for the
  reproducible exemplar runs, tests, and the rendered figures. No mocks: it is
  a genuine proposer that reads the shared state and emits a concrete proposal.
* :class:`HermesProposer` — the live AutoScientists agent. It renders the
  shared state to a prompt and asks a Hermes model (served by Ollama) which
  axis and direction to try next, then parses the structured reply. Its import
  of the infrastructure LLM client is lazy so the deterministic core can be
  tested without Ollama installed.

Swapping ``DeterministicProposer`` for ``HermesProposer`` is the only change
needed to turn the deterministic reference run into a live agentic one.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Protocol

from .state import Proposal, SharedState


class Proposer(Protocol):
    """Anything that can propose the next experiment from shared state."""

    def propose(
        self,
        state: SharedState,
        axes: Sequence[int],
        proposer_id: str,
        avoid: frozenset[tuple[int, str]] = frozenset(),
    ) -> Proposal:
        """Return the next proposal for the given subset of axes.

        ``avoid`` is the set of retired ``(axis, direction)`` pairs from the
        dead-end registry; a faithful proposer steers clear of them so the
        registry actually prunes the search rather than only reshaping team
        assignment.
        """
        ...


class DeterministicProposer:
    """Rule-based proposer: probe each assigned axis in its better direction.

    For each call it picks the next axis in ``axes`` (round-robin by experiment
    count) and chooses the step sign that most recently improved that axis in
    the log, defaulting to a downhill probe toward the optimum origin. When the
    chosen direction has been retired (passed in ``avoid``) it flips to the
    still-live opposite direction, so the dead-end registry actually steers the
    rule-based search. Fully deterministic given the shared state.
    """

    def __init__(self, step: float = 0.5) -> None:
        if step <= 0:
            raise ValueError("step must be positive")
        self.step = step

    def propose(
        self,
        state: SharedState,
        axes: Sequence[int],
        proposer_id: str,
        avoid: frozenset[tuple[int, str]] = frozenset(),
    ) -> Proposal:
        if not axes:
            raise ValueError("axes must be non-empty")
        axis = axes[len(state.log) % len(axes)]
        sign = self._last_improving_sign(state, axis)
        sign = self._respect_avoid(axis, sign, avoid)
        return Proposal(
            axis=axis,
            step=sign * self.step,
            rationale=f"probe axis {axis} {'up' if sign > 0 else 'down'}",
            proposer=proposer_id,
        )

    @staticmethod
    def _respect_avoid(axis: int, sign: float, avoid: frozenset[tuple[int, str]]) -> float:
        """Flip away from a retired direction when the opposite is still live."""
        chosen = "increase" if sign > 0 else "decrease"
        opposite = "decrease" if sign > 0 else "increase"
        if (axis, chosen) in avoid and (axis, opposite) not in avoid:
            return -sign
        return sign

    @staticmethod
    def _last_improving_sign(state: SharedState, axis: int) -> float:
        for outcome in reversed(state.log):
            if outcome.proposal.axis == axis and outcome.improved:
                return 1.0 if outcome.proposal.step >= 0 else -1.0
        # Default: probe toward the origin from the current champion.
        current = state.champion.params[axis]
        return -1.0 if current > 0 else 1.0


class HermesProposer:
    """Live proposer backed by a Hermes model served through Ollama.

    Requires a running Ollama daemon with the configured Hermes model pulled
    (e.g. ``ollama pull hermes3``). Exercised only by ``requires_ollama`` tests
    and the opt-in live demo; never on the deterministic coverage path.
    """

    def __init__(self, model: str = "hermes3", step: float = 0.5) -> None:
        self.model = model
        self.step = step
        self._client: object | None = None

    def _ensure_client(self) -> object:  # pragma: no cover - requires live Ollama
        if self._client is None:
            from infrastructure.llm.core.client import LLMClient  # lazy: keeps core import-light

            self._client = LLMClient()
        return self._client

    def _prompt(self, state: SharedState, axes: Sequence[int], avoid: frozenset[tuple[int, str]] = frozenset()) -> str:
        recent = state.log[-5:]
        history = "\n".join(
            f"  axis={o.proposal.axis} step={o.proposal.step:+.3f} "
            f"metric={o.metric:.4f} delta={o.delta_vs_champion:+.4f} "
            f"confirmed={o.confirmed}"
            for o in recent
        )
        retired = ", ".join(f"axis {axis} {direction}" for axis, direction in sorted(avoid))
        return (
            "You coordinate a long-running optimization search.\n"
            f"Champion metric: {state.champion.metric:.4f}\n"
            f"Champion params: {list(state.champion.params)}\n"
            f"Axes you may modify: {list(axes)}\n"
            f"Retired directions to avoid: {retired or '(none)'}\n"
            f"Recent experiments:\n{history or '  (none)'}\n\n"
            "Propose the next experiment as JSON with keys "
            '"axis" (int), "step" (float), "rationale" (str). '
            "Reply with only the JSON object."
        )

    def propose(  # pragma: no cover - requires live Ollama
        self,
        state: SharedState,
        axes: Sequence[int],
        proposer_id: str,
        avoid: frozenset[tuple[int, str]] = frozenset(),
    ) -> Proposal:
        if not axes:
            raise ValueError("axes must be non-empty")
        from infrastructure.llm.core.config import GenerationOptions  # lazy

        client = self._ensure_client()
        raw = client.query(  # type: ignore[attr-defined]
            self._prompt(state, axes, avoid),
            model=self.model,
            options=GenerationOptions(temperature=0.0, seed=0),
        )
        return self._parse(raw, axes, proposer_id)

    def _parse(self, raw: str, axes: Sequence[int], proposer_id: str) -> Proposal:
        payload = json.loads(_extract_json(raw))
        axis = int(payload["axis"])
        if axis not in axes:
            raise ValueError(f"model proposed axis {axis} outside assigned {list(axes)}")
        step = float(payload["step"])
        rationale = str(payload.get("rationale", "")).strip() or "hermes proposal"
        return Proposal(axis=axis, step=step, rationale=rationale, proposer=proposer_id)


def _extract_json(raw: str) -> str:
    """Pull the first JSON object out of a model reply."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in model reply")
    return raw[start : end + 1]
