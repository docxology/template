"""Continued fraction expansions and convergents for real numbers."""

from __future__ import annotations

import math
from typing import Iterator, Sequence


def continued_fraction_terms(
    x: float,
    max_terms: int = 64,
    tol: float = 1e-14,
) -> list[int]:
    """Return simple continued fraction partial quotients for ``x`` (``x > 0``).

    Stops when the remainder is within ``tol`` of an integer, ``max_terms`` is
    reached, or a non-finite value appears.

    Args:
        x: Positive real number.
        max_terms: Upper bound on the number of partial quotients.
        tol: Tolerance for detecting a rational tail.

    Returns:
        List ``[a0, a1, ...]`` such that ``x ≈ a0 + 1/(a1 + 1/(...))``.
    """
    if x <= 0 or not math.isfinite(x):
        raise ValueError("x must be a finite positive real number")
    terms: list[int] = []
    v = x
    for _ in range(max_terms):
        a = math.floor(v + tol)
        terms.append(int(a))
        frac = v - a
        if abs(frac) <= tol:
            break
        v = 1.0 / frac
    return terms


def convergents(terms: Sequence[int]) -> Iterator[tuple[int, int]]:
    """Yield convergents ``(p_k, q_k)`` after each partial quotient.

    Args:
        terms: Partial quotients ``[a0, a1, ...]``.

    Yields:
        ``(p, q)`` in lowest terms for each prefix of ``terms``.
    """
    if not terms:
        return
    h_m2, h_m1 = 0, 1
    k_m2, k_m1 = 1, 0
    for a in terms:
        h = a * h_m1 + h_m2
        k = a * k_m1 + k_m2
        yield h, k
        h_m2, h_m1 = h_m1, h
        k_m2, k_m1 = k_m1, k


def value_from_convergent(p: int, q: int) -> float:
    """Return the floating-point value ``p/q``."""
    if q == 0:
        raise ValueError("denominator q must be non-zero")
    return p / q


def continued_fraction_exact_positive_rational(p: int, q: int) -> list[int]:
    """Exact simple continued fraction partial quotients for ``p/q`` (``p, q >= 1``)."""
    if p < 1 or q < 1:
        raise ValueError("p and q must be positive integers")
    terms: list[int] = []
    a, b = p, q
    while b != 0:
        t = a // b
        terms.append(t)
        a, b = b, a - t * b
    return terms
