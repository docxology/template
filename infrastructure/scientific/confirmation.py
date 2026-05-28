"""Noise-band confirmation for stochastic metrics.

When a metric is measured with run-to-run noise, a single observed improvement
over a baseline may be a draw of that noise rather than a real gain. This module
provides a domain-agnostic acceptance test: average the candidate metric over
several seeds and confirm an improvement only when the mean exceeds the baseline
by more than an empirical noise band (a multiple of the standard error of the
mean).

The estimator is generic — any project comparing a stochastic metric to a
baseline can reuse :func:`confirm_improvement`. It is used by the
``template_autoscientists`` exemplar as the acceptance step of its coordination
loop.
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
        baseline_metric: Incumbent baseline metric to beat.
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
