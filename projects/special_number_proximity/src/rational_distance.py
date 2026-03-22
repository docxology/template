"""Minimum distance from a real number to rationals with bounded denominator."""

from __future__ import annotations

import math
from typing import Optional, Tuple


def rational_at_min_distance(x: float, q_max: int) -> Tuple[float, int, int]:
    """Return ``(distance, p, q)`` minimizing ``|x - p/q|`` for ``1 <= q <= q_max``.

    For each denominator ``q``, only ``p`` in ``{round(x*q)-1, round(x*q), round(x*q)+1}``
    need to be checked. The minimizing rational may be unreduced; ``distance`` is still
    exact for IEEE double ``x`` and integer ``p,q``.

    Args:
        x: Real number (finite).
        q_max: Maximum denominator, at least ``1``.

    Returns:
        Tuple of minimum absolute error, numerator, denominator achieving it.
    """
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if q_max < 1:
        raise ValueError("q_max must be >= 1")

    best_d = float("inf")
    best_p = 0
    best_q = 1
    for q in range(1, q_max + 1):
        k = int(round(x * q))
        for p in (k - 1, k, k + 1):
            d = abs(x - p / q)
            if d < best_d:
                best_d = d
                best_p = p
                best_q = q
    return best_d, best_p, best_q


def rational_at_min_q_squared_error(x: float, q_max: int) -> Tuple[float, int, int]:
    """Return ``(q^2 * |x - p/q|, p, q)`` minimized over ``1 <= q <= q_max``.

    For each ``q``, only ``p`` in ``{round(x*q)-1, round(x*q), round(x*q)+1}`` need
    be checked (same candidates as :func:`rational_at_min_distance`). This is the
    classical Lagrange / Hurwitz *quality* scale at bounded denominator: small values
    mean an unusually sharp rational hit relative to ``q``.
    """
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if q_max < 1:
        raise ValueError("q_max must be >= 1")

    best_m = float("inf")
    best_p = 0
    best_q = 1
    for q in range(1, q_max + 1):
        k = int(round(x * q))
        for p in (k - 1, k, k + 1):
            d = abs(x - p / q)
            m = (q * q) * d
            if m < best_m:
                best_m = m
                best_p = p
                best_q = q
    return best_m, best_p, best_q


def min_q_squared_error(x: float, q_max: int) -> float:
    """Minimum of ``q^2 |x - p/q|`` over ``1 <= q <= q_max`` (same ``p`` candidates as ``\\delta_Q``)."""
    m, _, _ = rational_at_min_q_squared_error(x, q_max)
    return m


def min_rational_distance(x: float, q_max: int) -> float:
    """Minimum ``|x - p/q|`` over integers ``p`` and ``1 <= q <= q_max``."""
    d, _, _ = rational_at_min_distance(x, q_max)
    return d


def min_rational_distance_fractional(x: float, q_max: int) -> float:
    """Minimum distance from the fractional part of ``x`` to rationals in ``[0,1)``.

    Uses ``min_rational_distance`` on ``x - floor(x)``.
    """
    frac = x - math.floor(x)
    return min_rational_distance(frac, q_max)


def min_rational_distance_mod1(x: float, q_max: int) -> Optional[float]:
    """Wrap ``x`` to ``[0,1)`` and return min rational distance; ``None`` if degenerate."""
    if not math.isfinite(x):
        return None
    frac = x - math.floor(x)
    return min_rational_distance(frac, q_max)
