"""Effect-size ranking of axes.

The analyst role in AutoScientists prioritizes directions with large observed
effects and deprioritizes axes whose experiments consistently produce tiny
changes. This module turns the experiment log into a deterministic axis
ordering used to assign work to teams.

The effect-size estimator is generic (mean absolute metric delta per axis) and
is a candidate for promotion to ``infrastructure/scientific``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .state import ExperimentOutcome


def axis_effect_sizes(log: Iterable[ExperimentOutcome], axes: Sequence[int]) -> dict[int, float]:
    """Mean absolute metric delta observed per axis (0.0 for untried axes)."""
    totals: dict[int, float] = {axis: 0.0 for axis in axes}
    counts: dict[int, int] = {axis: 0 for axis in axes}
    for outcome in log:
        axis = outcome.proposal.axis
        if axis in totals:
            totals[axis] += abs(outcome.delta_vs_champion)
            counts[axis] += 1
    return {axis: (totals[axis] / counts[axis] if counts[axis] else 0.0) for axis in axes}


def rank_axes(log: Iterable[ExperimentOutcome], axes: Sequence[int]) -> list[int]:
    """Order axes by descending observed effect size.

    Untried axes (effect 0.0) sort *first* so under-explored directions are
    prioritized before the search exploits known-large-effect axes — ties and
    untried axes break by axis index for determinism.
    """
    log = list(log)
    effects = axis_effect_sizes(log, axes)
    tried = {outcome.proposal.axis for outcome in log}

    def key(axis: int) -> tuple[int, float, int]:
        untried_first = 0 if axis not in tried else 1
        return (untried_first, -effects[axis], axis)

    return sorted(axes, key=key)
