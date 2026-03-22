"""Tests for scaled-lattice formulation and Dirichlet bookkeeping."""

from __future__ import annotations

import math

import pytest

from diophantine_bounds import (
    dirichlet_pigeonhole_upper_bound,
    distance_to_nearest_integer,
    max_integer_residual_over_q,
    min_rational_distance_via_scaled_lattice,
)
from rational_distance import min_rational_distance


def test_distance_to_nearest_integer_half() -> None:
    assert distance_to_nearest_integer(1.25) == pytest.approx(0.25)
    assert distance_to_nearest_integer(1.75) == pytest.approx(0.25)


def test_distance_to_nearest_integer_negative() -> None:
    assert distance_to_nearest_integer(-1.3) == pytest.approx(0.3)


def test_distance_nonfinite_rejected() -> None:
    with pytest.raises(ValueError):
        distance_to_nearest_integer(float("nan"))


@pytest.mark.parametrize("x", [math.pi, math.e, math.sqrt(2.0), -math.pi, 12.718281828])
@pytest.mark.parametrize("q_max", [1, 3, 15, 80])
def test_lattice_matches_brute_force(x: float, q_max: int) -> None:
    b = min_rational_distance(x, q_max)
    ell = min_rational_distance_via_scaled_lattice(x, q_max)
    assert ell == pytest.approx(b, rel=0.0, abs=1e-14)


def test_dirichlet_bound_q_max() -> None:
    assert dirichlet_pigeonhole_upper_bound(10) == pytest.approx(1.0 / 11.0)


def test_dirichlet_residual_pi_obeyed() -> None:
    q_max = 50
    mx = max_integer_residual_over_q(math.pi, q_max)
    assert mx <= dirichlet_pigeonhole_upper_bound(q_max) + 1e-12


def test_lattice_q_invalid() -> None:
    with pytest.raises(ValueError):
        min_rational_distance_via_scaled_lattice(1.0, 0)


def test_dirichlet_bound_invalid_q() -> None:
    with pytest.raises(ValueError):
        dirichlet_pigeonhole_upper_bound(0)


def test_max_residual_nonfinite() -> None:
    with pytest.raises(ValueError):
        max_integer_residual_over_q(float("inf"), 5)


def test_max_residual_q_invalid() -> None:
    with pytest.raises(ValueError):
        max_integer_residual_over_q(1.0, 0)


def test_lattice_nonfinite_x() -> None:
    with pytest.raises(ValueError):
        min_rational_distance_via_scaled_lattice(float("nan"), 5)
    with pytest.raises(ValueError):
        min_rational_distance_via_scaled_lattice(float("inf"), 5)


def test_max_residual_nonfinite_x_inf() -> None:
    with pytest.raises(ValueError):
        max_integer_residual_over_q(float("inf"), 5)
