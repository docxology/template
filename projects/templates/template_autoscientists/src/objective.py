"""Deterministic synthetic research objective.

A stand-in for the expensive, stochastic evaluation an AutoScientists run would
optimize (validation loss, Spearman correlation, ...). It is multi-axis with a
single global optimum, several deceptive local optima, and seeded evaluation
noise, so that the noise-band confirmation mechanism has something real to do.

Evaluation is a pure function of ``(params, seed)`` — identical inputs always
yield identical outputs — which is what lets the whole exemplar render
reproducibly.
"""

from __future__ import annotations

import hashlib
import math


def _seed_noise(params: tuple[float, ...], seed: int, scale: float) -> float:
    """Deterministic zero-centred noise derived from ``(params, seed)``.

    Uses a hash of the rounded parameter vector so that re-evaluating the same
    point on a *different* seed gives a different draw (modelling run-to-run
    variance), while the same seed always reproduces the same value.
    """
    key = f"{seed}:" + ",".join(f"{p:.6f}" for p in params)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    unit = int.from_bytes(digest[:8], "big") / float(1 << 64)  # [0, 1)
    return (unit - 0.5) * 2.0 * scale


class SyntheticObjective:
    """Multi-axis objective with deceptive structure and seeded noise.

    Higher is better. The clean landscape is a smooth global peak at
    ``optimum`` minus shallow cosine ripples that create deceptive local optima
    along each axis.
    """

    def __init__(
        self,
        dimensions: int = 4,
        optimum: tuple[float, ...] | None = None,
        noise_scale: float = 0.02,
        ripple: float = 0.15,
    ) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be >= 1")
        if optimum is not None and len(optimum) != dimensions:
            raise ValueError("optimum length must equal dimensions")
        self.dimensions = dimensions
        self.optimum = optimum if optimum is not None else tuple(0.0 for _ in range(dimensions))
        self.noise_scale = noise_scale
        self.ripple = ripple

    def clean(self, params: tuple[float, ...]) -> float:
        """Noise-free objective value (the ground truth being searched)."""
        if len(params) != self.dimensions:
            raise ValueError("params length must equal dimensions")
        value = 0.0
        for p, opt in zip(params, self.optimum):
            gap = p - opt
            value -= gap * gap
            value -= self.ripple * (1.0 - math.cos(2.0 * math.pi * gap))
        return value

    def evaluate(self, params: tuple[float, ...], seed: int) -> float:
        """Noisy observation of the objective at ``params`` under ``seed``."""
        return self.clean(params) + _seed_noise(params, seed, self.noise_scale)

    def start_params(self) -> tuple[float, ...]:
        """A fixed, deterministic starting point away from the optimum."""
        return tuple(opt + 1.5 for opt in self.optimum)
