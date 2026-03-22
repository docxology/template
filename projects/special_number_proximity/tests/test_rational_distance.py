"""Tests for rational approximation distance."""

import math

import pytest

from rational_distance import (
    min_q_squared_error,
    min_rational_distance,
    min_rational_distance_fractional,
    min_rational_distance_mod1,
    rational_at_min_distance,
    rational_at_min_q_squared_error,
)


def test_exact_rational_hits_zero() -> None:
    assert min_rational_distance(3 / 7, 7) == 0.0
    d, p, q = rational_at_min_distance(3 / 7, 7)
    assert d == 0.0
    assert p / q == pytest.approx(3 / 7)


def test_one_sixth_at_q_max_six() -> None:
    assert min_rational_distance(1.0 / 6.0, 6) == 0.0


def test_sqrt2_not_too_close_with_small_q() -> None:
    s = math.sqrt(2.0)
    d = min_rational_distance(s, 5)
    assert d > 1e-3


def test_rational_at_min_distance_reports_triple() -> None:
    x = 0.4142135623730950
    d, p, q = rational_at_min_distance(x, 200)
    assert d == abs(x - p / q)
    assert 1 <= q <= 200


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        min_rational_distance(1.0, 0)
    with pytest.raises(ValueError):
        rational_at_min_distance(float("nan"), 10)
    with pytest.raises(ValueError):
        rational_at_min_distance(float("inf"), 10)


def test_min_rational_distance_fractional_matches_manual() -> None:
    x = math.pi
    frac = x - math.floor(x)
    assert min_rational_distance_fractional(x, 50) == min_rational_distance(frac, 50)


def test_min_rational_distance_mod1_nan() -> None:
    assert min_rational_distance_mod1(float("nan"), 10) is None


def test_min_rational_distance_mod1_finite() -> None:
    r = min_rational_distance_mod1(12.718, 30)
    assert r is not None
    assert r == min_rational_distance(12.718 - math.floor(12.718), 30)


def test_q_squared_error_matches_manual() -> None:
    x = math.sqrt(2.0)
    q_max = 20
    m, p, q = rational_at_min_q_squared_error(x, q_max)
    assert m == min_q_squared_error(x, q_max)
    assert m == (q * q) * abs(x - p / q)


def test_q_squared_error_invalid() -> None:
    with pytest.raises(ValueError):
        rational_at_min_q_squared_error(1.0, 0)
    with pytest.raises(ValueError):
        rational_at_min_q_squared_error(float("nan"), 5)
