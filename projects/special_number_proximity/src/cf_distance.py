"""Best distance among continued-fraction convergents up to a denominator cap.

Semiconvergents can beat the last ``q \\leq Q`` convergent for fixed ``Q``, so the
value here is generally **at least** the global ``\\delta_Q`` from exhaustive search.
It is still a cheap certificate and matches ``\\delta_Q`` for many ``(x, Q)`` pairs.
"""

from __future__ import annotations

import math

from continued_fractions import continued_fraction_terms, convergents


def min_distance_among_convergents(x: float, q_max: int, max_terms: int = 96) -> tuple[float, int, int]:
    """Minimum ``|x - p/q|`` over convergents with ``q \\leq q_max`` (``x > 0``)."""
    if not math.isfinite(x) or x <= 0:
        raise ValueError("x must be a finite positive real")
    if q_max < 1:
        raise ValueError("q_max must be >= 1")
    terms = continued_fraction_terms(x, max_terms=max_terms)
    best_d = float("inf")
    best_p, best_q = 0, 1
    for p, q in convergents(terms):
        if q > q_max:
            break
        d = abs(x - p / q)
        if d < best_d:
            best_d = d
            best_p, best_q = p, q
    return best_d, best_p, best_q
