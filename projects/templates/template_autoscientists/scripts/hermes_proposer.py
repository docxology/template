"""Live Hermes proposer — infrastructure LLM wiring lives in scripts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import TYPE_CHECKING

from src.agents import _extract_json
from src.state import Proposal, SharedState

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient


class HermesProposer:
    """Live proposer backed by a Hermes model served through Ollama."""

    def __init__(self, model: str = "hermes3", step: float = 0.5) -> None:
        self.model = model
        self.step = step
        self._client: LLMClient | None = None

    def _ensure_client(self) -> LLMClient:  # pragma: no cover - requires live Ollama
        if self._client is None:
            from infrastructure.llm.core.client import LLMClient

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
        from infrastructure.llm.core.config import GenerationOptions

        client = self._ensure_client()
        raw = client.query(
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


__all__ = ["HermesProposer"]
