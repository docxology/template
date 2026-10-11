"""Proposer agents and the language-model plug-in seam.

The search loop depends only on the :class:`Proposer` protocol. Two real
implementations are provided:

* :class:`DeterministicProposer` — a rule-based policy used for the
  reproducible exemplar runs, tests, and the rendered figures. No mocks: it is
  a genuine proposer that reads the shared state and emits a concrete proposal.
The bounded local-model adapter lives in ``agents/live_transport.py``. Its
paired-run orchestration and custody are separate from this pure reference policy.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..analysis.state import Proposal, SharedState


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
        """Initialize the deterministic proposer with a fixed step size.

        Args:
            step: The magnitude of each proposed parameter step (must be > 0).

        Raises:
            ValueError: If ``step`` is not positive.
        """
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
        """Process propose."""
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
        """Return the step sign that most recently improved *axis*, or probe toward the origin."""
        for outcome in reversed(state.log):
            if outcome.proposal.axis == axis and outcome.improved:
                return 1.0 if outcome.proposal.step >= 0 else -1.0
        # Default: probe toward the origin from the current champion.
        current = state.champion.params[axis]
        return -1.0 if current > 0 else 1.0
