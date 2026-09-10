"""Stagnation detection and team reorganization.

When the champion stops improving for a window of experiments, AutoScientists
reopens discussion and reorganizes teams around different directions. Here that
is a deterministic signal plus an axis-reassignment that rotates teams onto the
directions ranked most promising and away from retired dead ends.

**Stagnation semantics.** The detector checks the ``improved`` property on each
``ExperimentOutcome`` in the trailing window. An outcome is ``improved`` only
when *both* ``confirmed=True`` AND ``delta_vs_champion > 0.0`` — a positive
delta that failed confirmation (noise-rejected) does NOT clear stagnation, and
neither does a confirmed non-improvement (delta <= 0). This mirrors the
AutoScientists protocol: only confirmed, genuinely-improving experiments
count toward breaking a stagnation streak.
"""

from __future__ import annotations

from collections.abc import Sequence

from .dead_ends import DeadEndRegistry
from .state import SharedState


class StagnationDetector:
    """Fires when the champion has not improved within ``window`` experiments."""

    def __init__(self, window: int = 10) -> None:
        """Initialize the stagnation detector with a trailing-window size.

        Args:
            window: Number of recent experiments to check for improvement (must be >= 1).

        Raises:
            ValueError: If ``window`` < 1.
        """
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window

    def is_stagnant(self, state: SharedState) -> bool:
        """True when no improvement occurred in the last ``window`` outcomes."""
        if len(state.log) < self.window:
            return False
        recent = state.log[-self.window :]
        return not any(outcome.improved for outcome in recent)


def reorganize_axes(
    ranked_axes: Sequence[int],
    num_teams: int,
    registry: DeadEndRegistry,
) -> list[list[int]]:
    """Partition live axes across teams, dropping fully-retired axes.

    An axis is dropped only when *both* of its directions are retired. Live
    axes are dealt round-robin across teams so each team gets a complementary
    slice of the most-promising directions first.

    When *all* axes are fully retired the returned list contains ``num_teams``
    empty sub-lists; the caller (the search loop) detects this and breaks out
    of the experiment budget loop rather than entering an infinite cycle.
    """
    if num_teams < 1:
        raise ValueError("num_teams must be >= 1")
    live = [
        axis
        for axis in ranked_axes
        if not (registry.is_dead_end(axis, "increase") and registry.is_dead_end(axis, "decrease"))
    ]
    teams: list[list[int]] = [[] for _ in range(num_teams)]
    for index, axis in enumerate(live):
        teams[index % num_teams].append(axis)
    return teams
