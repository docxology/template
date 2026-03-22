"""Deterministic sampling strategies for reference distributions."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


def uniform_unit_samples(n: int, rng: np.random.Generator) -> np.ndarray:
    """``n`` independent Uniform(0, 1) samples."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return rng.random(size=n)


def quadratic_irrationals(
    square_free_integers: Iterable[int],
    rng: np.random.Generator,
    n_per_root: int,
) -> np.ndarray:
    """Draw ``sqrt(k)`` mod 1 for random square-free ``k`` from the given set.

    Args:
        square_free_integers: Candidate radicands (each should be square-free > 1).
        rng: NumPy random generator.
        n_per_root: Replications per chosen root.

    Returns:
        1-D array of fractional parts ``sqrt(k) - floor(sqrt(k))`` with length
        ``len(list(square_free_integers)) * n_per_root``.
    """
    roots = list(square_free_integers)
    if not roots:
        return np.array([], dtype=np.float64)
    if n_per_root < 0:
        raise ValueError("n_per_root must be non-negative")
    out: list[float] = []
    for k in roots:
        if k < 2:
            continue
        s = math.sqrt(float(k))
        frac = s - math.floor(s)
        out.extend([frac] * n_per_root)
    return np.array(out, dtype=np.float64)


def beta_unit_samples(
    n: int,
    a: float,
    b: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """``n`` independent ``Beta(a, b)`` draws (supported on ``(0,1)``)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters a and b must be positive")
    if n == 0:
        return np.array([], dtype=np.float64)
    return rng.beta(a, b, size=n)


def random_quadratic_mod1(
    candidates: Sequence[int],
    rng: np.random.Generator,
    n: int,
) -> np.ndarray:
    """Sample ``n`` values ``sqrt(k) - floor(sqrt(k))`` with random ``k`` from ``candidates``."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return np.array([], dtype=np.float64)
    c = [k for k in candidates if k >= 2]
    if not c:
        return np.array([], dtype=np.float64)
    picks = rng.choice(np.array(c, dtype=int), size=n)
    out = np.empty(n, dtype=np.float64)
    for i, k in enumerate(picks):
        s = math.sqrt(float(k))
        out[i] = s - math.floor(s)
    return out
