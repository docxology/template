"""Vectorized batch helpers agree with scalar definitions."""

from __future__ import annotations

import math

import numpy as np
import pytest

from rational_distance import min_q_squared_error, min_rational_distance
from statistics_compare import (
    batch_min_q_squared_errors,
    batch_min_rational_distances,
)


def test_batch_min_rational_vectorized_matches_scalar() -> None:
    rng = np.random.default_rng(11)
    xs = rng.random(25)
    q_max = 35
    a = batch_min_rational_distances(xs, q_max, implementation="vectorized")
    b = batch_min_rational_distances(xs, q_max, implementation="scalar")
    np.testing.assert_allclose(a, b, rtol=0.0, atol=0.0)


def test_batch_min_q_squared_vectorized_matches_scalar() -> None:
    rng = np.random.default_rng(12)
    xs = rng.random(20)
    q_max = 28
    a = batch_min_q_squared_errors(xs, q_max, implementation="vectorized")
    b = batch_min_q_squared_errors(xs, q_max, implementation="scalar")
    np.testing.assert_allclose(a, b, rtol=0.0, atol=0.0)


def test_q_squared_rational_goes_zero() -> None:
    assert min_q_squared_error(1.0 / 7.0, 7) == pytest.approx(0.0, abs=1e-15)


def test_q_squared_phi_positive_at_small_q() -> None:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    m = min_q_squared_error(phi, 10)
    assert m > 1e-4
