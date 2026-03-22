"""Scaled-lattice view of bounded-denominator rational approximation.

For each integer ``q >= 1``, choosing ``p = round(q x)`` minimises ``|x - p/q|``, and

    |x - p/q| = |q x - p| / q,

so with ``||y|| := dist(y, \\mathbb{Z}) = min_{n \\in \\mathbb{Z}} |y - n|``,

    \\delta_Q(x) = min_{1 \\leq q \\leq Q} ||q x|| / q.

This identity is useful for proofs (Dirichlet box principle) and as an independent
implementation check. See manuscript ``03d_scaled_lattice_formulation.md``.
"""

from __future__ import annotations

import math


def distance_to_nearest_integer(y: float) -> float:
    """Return ``||y|| = min_{n \\in \\mathbb{Z}} |y - n|`` for finite ``y``."""
    if not math.isfinite(y):
        raise ValueError("y must be finite")
    fp = y - math.floor(y)
    return min(fp, 1.0 - fp)


def min_rational_distance_via_scaled_lattice(x: float, q_max: int) -> float:
    """Same functional as ``min_rational_distance`` via ``min_q ||q x|| / q``."""
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if q_max < 1:
        raise ValueError("q_max must be >= 1")
    best = float("inf")
    for q in range(1, q_max + 1):
        res = distance_to_nearest_integer(q * x) / q
        if res < best:
            best = res
    return best


def dirichlet_pigeonhole_upper_bound(q_max: int) -> float:
    """Classical ``1 / (q_max + 1)`` upper bound on ``min_{1 \\leq q \\leq q_max} ||q x||``.

    For every real ``x`` there exists ``q`` in ``1..q_max`` with ``||q x|| \\leq 1/(q_max+1)``.
    This bounds the **integer residual**, not ``\\delta_Q(x)`` itself.
    """
    if q_max < 1:
        raise ValueError("q_max must be >= 1")
    return 1.0 / (q_max + 1)


def max_integer_residual_over_q(x: float, q_max: int) -> float:
    """``min_{1 \\leq q \\leq q_max} ||q x||`` (unnormalised; compare to Dirichlet bound)."""
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if q_max < 1:
        raise ValueError("q_max must be >= 1")
    best = float("inf")
    for q in range(1, q_max + 1):
        r = distance_to_nearest_integer(q * x)
        if r < best:
            best = r
    return best
