"""Continued-fraction convergent distance caps."""

from __future__ import annotations

import math

import pytest

from cf_distance import min_distance_among_convergents
from rational_distance import min_rational_distance


def test_convergent_distance_ge_brute_for_pi() -> None:
    q_max = 120
    d_cf, _, _ = min_distance_among_convergents(math.pi, q_max)
    d_br = min_rational_distance(math.pi, q_max)
    assert d_cf >= d_br - 1e-15


def test_golden_ratio_convergent_hits_brute_small_q() -> None:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    for q_max in (8, 21, 55):
        d_cf, p, q = min_distance_among_convergents(phi, q_max)
        d_br = min_rational_distance(phi, q_max)
        assert d_cf == pytest.approx(d_br, rel=1e-12, abs=1e-14)
        assert q <= q_max
        assert abs(phi - p / q) == pytest.approx(d_cf)


def test_cf_distance_positive_x_only() -> None:
    with pytest.raises(ValueError):
        min_distance_among_convergents(-math.pi, 10)


def test_cf_distance_q_max_invalid() -> None:
    with pytest.raises(ValueError):
        min_distance_among_convergents(math.pi, 0)


def test_cf_distance_stops_when_next_convergent_denominator_exceeds_cap() -> None:
    """Large partial quotient makes the second convergent jump past ``q_max``."""
    x = 1.0 + 1.0e-6
    d, p, q = min_distance_among_convergents(x, q_max=5)
    assert q <= 5
    assert d == pytest.approx(abs(x - p / q), rel=0.0, abs=1e-15)
