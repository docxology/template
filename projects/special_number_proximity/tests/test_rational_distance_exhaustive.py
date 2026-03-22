"""Brute-force verification of the three-p scan for small Q."""

from __future__ import annotations

import numpy as np
import pytest

from rational_distance import rational_at_min_distance


def _brute_delta(x: float, q_max: int) -> float:
    """Exhaustive minimum |x - p/q| for x in [0,1), p in 0..q (sufficient for mod-1)."""
    best = float("inf")
    for q in range(1, q_max + 1):
        for p in range(0, q + 1):
            d = abs(x - p / q)
            if d < best:
                best = d
    return best


@pytest.mark.parametrize("q_max", [5, 12, 30])
@pytest.mark.parametrize("seed", [0, 1, 2, 42])
def test_scan_matches_brute_fractional(q_max: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(15):
        x = float(rng.random())
        d_scan, _, _ = rational_at_min_distance(x, q_max)
        d_br = _brute_delta(x, q_max)
        assert d_scan == pytest.approx(d_br, rel=0.0, abs=1e-15)


def test_scan_matches_brute_shifted_interval() -> None:
    """For x = k + frac, distances match frac case (rationals p/q shift consistently)."""
    rng = np.random.default_rng(99)
    q_max = 18
    for _ in range(10):
        frac = float(rng.random())
        k = int(rng.integers(-3, 4))
        x = k + frac
        d_scan, _, _ = rational_at_min_distance(x, q_max)
        d_frac, _, _ = rational_at_min_distance(frac, q_max)
        assert d_scan == pytest.approx(d_frac, rel=0.0, abs=1e-14)
