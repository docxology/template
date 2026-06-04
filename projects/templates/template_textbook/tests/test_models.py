"""Tests for the computational backbone (no mocks; real numerics)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from textbook import models


def test_logistic_growth_starts_at_initial_and_approaches_capacity():
    t = np.linspace(0, 50, 100)
    y = models.logistic_growth(t, r=1.0, carrying_capacity=100.0, initial=2.0)
    assert math.isclose(y[0], 2.0, rel_tol=1e-9)
    assert y[-1] == pytest.approx(100.0, abs=1e-3)
    assert np.all(np.diff(y) >= -1e-12)  # monotonic non-decreasing (plateaus at K)
    assert y[1] > y[0]  # strictly increasing before saturation


@pytest.mark.parametrize(
    "kwargs",
    [
        {"r": 0.0, "carrying_capacity": 10.0, "initial": 1.0},
        {"r": 1.0, "carrying_capacity": 0.0, "initial": 1.0},
        {"r": 1.0, "carrying_capacity": 10.0, "initial": 0.0},
        {"r": 1.0, "carrying_capacity": 10.0, "initial": 20.0},
    ],
)
def test_logistic_growth_validates(kwargs):
    with pytest.raises(ValueError):
        models.logistic_growth(np.array([0.0, 1.0]), **kwargs)


def test_saturating_response_half_saturation_and_monotonic():
    y = models.saturating_response(np.array([3.0]), maximum=1.0, half_saturation=3.0)
    assert y[0] == pytest.approx(0.5)
    x = np.linspace(0, 20, 50)
    resp = models.saturating_response(x, maximum=2.0, half_saturation=5.0, hill=2.0)
    assert np.all(np.diff(resp) >= 0)
    assert resp[-1] < 2.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"maximum": 0.0, "half_saturation": 1.0},
        {"maximum": 1.0, "half_saturation": 0.0},
        {"maximum": 1.0, "half_saturation": 1.0, "hill": 0.0},
    ],
)
def test_saturating_response_validates(kwargs):
    with pytest.raises(ValueError):
        models.saturating_response(np.array([1.0]), **kwargs)


def test_saturating_response_rejects_negative_x():
    with pytest.raises(ValueError):
        models.saturating_response(np.array([-1.0]), maximum=1.0, half_saturation=1.0)


def test_exponential_decay_and_half_life():
    rate = 0.5
    th = models.half_life(rate)
    y = models.exponential_decay(np.array([0.0, th]), initial=100.0, rate=rate)
    assert y[0] == pytest.approx(100.0)
    assert y[1] == pytest.approx(50.0, rel=1e-6)


@pytest.mark.parametrize("kwargs", [{"initial": -1.0, "rate": 0.5}, {"initial": 1.0, "rate": -0.5}])
def test_exponential_decay_validates(kwargs):
    with pytest.raises(ValueError):
        models.exponential_decay(np.array([0.0]), **kwargs)


def test_half_life_validates():
    with pytest.raises(ValueError):
        models.half_life(0.0)


def test_linear_fit_recovers_known_line():
    x = np.linspace(0, 10, 11)
    y = 3.0 * x - 2.0
    fit = models.linear_fit(x, y)
    assert fit.slope == pytest.approx(3.0)
    assert fit.intercept == pytest.approx(-2.0)
    assert fit.r_squared == pytest.approx(1.0)
    assert fit.predict(np.array([4.0]))[0] == pytest.approx(10.0)


def test_linear_fit_constant_y_gives_r_squared_one():
    fit = models.linear_fit(np.array([0.0, 1.0, 2.0]), np.array([5.0, 5.0, 5.0]))
    assert fit.slope == pytest.approx(0.0, abs=1e-9)
    assert fit.r_squared == pytest.approx(1.0)


@pytest.mark.parametrize("x,y", [([0.0], [1.0]), ([0.0, 1.0], [1.0])])
def test_linear_fit_validates(x, y):
    with pytest.raises(ValueError):
        models.linear_fit(np.array(x), np.array(y))


def test_descriptive_statistics():
    stats = models.descriptive_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats["mean"] == pytest.approx(3.0)
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["count"] == 5.0
    assert stats["std"] == pytest.approx(math.sqrt(2.0))


def test_descriptive_statistics_empty():
    with pytest.raises(ValueError):
        models.descriptive_statistics([])


def test_normalize_unit_interval():
    out = models.normalize_unit_interval([0.0, 5.0, 10.0])
    assert out[0] == 0.0
    assert out[-1] == 1.0
    assert out[1] == pytest.approx(0.5)


def test_normalize_unit_interval_constant_and_empty():
    assert np.all(models.normalize_unit_interval([7.0, 7.0, 7.0]) == 0.0)
    with pytest.raises(ValueError):
        models.normalize_unit_interval([])
