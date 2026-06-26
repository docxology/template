"""Noise-band confirmation for stochastic metrics.

Because the objective is noisy, a single observed improvement may be a draw of
the evaluation noise rather than a real gain. Following the AutoScientists
acceptance protocol, a candidate is confirmed only when its mean metric over
several seeds exceeds the incumbent by more than the empirical noise band.

The acceptance rule is **strictly greater than**, not ≥: a candidate whose
mean-over-seeds delta equals the band exactly is *not* confirmed. This ensures
the noise-band shrinks only actual noise, never a zero-gain tie.

This estimator is domain-agnostic. It is kept standalone here so the exemplar
runs self-contained, and a synchronized generic copy lives at
``infrastructure.scientific.confirmation`` for reuse by any other project that
compares a stochastic metric to a baseline.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Confirmation:
    """Outcome of a multi-seed confirmation check."""

    candidate_mean: float
    baseline_metric: float
    delta: float
    noise_band: float
    confirmed: bool


def confirm_improvement(
    evaluate: Callable[[tuple[float, ...], int], float],
    candidate: tuple[float, ...],
    baseline_metric: float,
    seeds: Sequence[int],
    noise_scale: float,
    sigma: float = 2.0,
) -> Confirmation:
    """Confirm a candidate beats ``baseline_metric`` beyond the noise band.

    Args:
        evaluate: Deterministic ``(params, seed) -> metric`` evaluator.
        candidate: Parameter vector under test.
        baseline_metric: Incumbent champion metric to beat.
        seeds: Distinct seeds to average the candidate over (>= 1).
        noise_scale: Per-evaluation noise magnitude of the objective.
        sigma: Width of the noise band in standard errors of the mean.

    Returns:
        A :class:`Confirmation`; ``confirmed`` is True only when the mean
        candidate metric exceeds the baseline by more than the band.
    """
    if not seeds:
        raise ValueError("seeds must be non-empty")
    samples = [evaluate(candidate, seed) for seed in seeds]
    mean = statistics.fmean(samples)
    standard_error = noise_scale / (len(seeds) ** 0.5)
    band = sigma * standard_error
    delta = mean - baseline_metric
    return Confirmation(
        candidate_mean=mean,
        baseline_metric=baseline_metric,
        delta=delta,
        noise_band=band,
        confirmed=delta > band,
    )
