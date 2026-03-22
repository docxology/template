"""Tests for sampling helpers."""

import numpy as np
import pytest

from sampling import (
    beta_unit_samples,
    quadratic_irrationals,
    random_quadratic_mod1,
    uniform_unit_samples,
)


def test_uniform_unit_samples_shape_and_bounds() -> None:
    rng = np.random.default_rng(0)
    u = uniform_unit_samples(500, rng)
    assert u.shape == (500,)
    assert np.all(u >= 0) and np.all(u < 1)


def test_uniform_negative_n_raises() -> None:
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError):
        uniform_unit_samples(-1, rng)


def test_quadratic_irrationals_length() -> None:
    rng = np.random.default_rng(2)
    v = quadratic_irrationals([2, 3, 5], rng, n_per_root=4)
    assert v.shape == (12,)
    assert np.all((v >= 0) & (v < 1))


def test_random_quadratic_mod1() -> None:
    rng = np.random.default_rng(3)
    v = random_quadratic_mod1([2, 3, 5, 7], rng, 100)
    assert v.shape == (100,)
    assert np.all((v >= 0) & (v < 1))


def test_random_quadratic_empty_candidates() -> None:
    rng = np.random.default_rng(4)
    assert random_quadratic_mod1([], rng, 5).size == 0
    assert random_quadratic_mod1([1], rng, 5).size == 0


def test_quadratic_irrationals_empty_roots() -> None:
    rng = np.random.default_rng(5)
    assert quadratic_irrationals([], rng, 3).size == 0


def test_quadratic_irrationals_skips_small_k() -> None:
    rng = np.random.default_rng(6)
    assert quadratic_irrationals([0, 1], rng, 2).size == 0


def test_quadratic_irrationals_negative_n_per_root() -> None:
    rng = np.random.default_rng(8)
    with pytest.raises(ValueError):
        quadratic_irrationals([2], rng, -1)


def test_random_quadratic_negative_n() -> None:
    rng = np.random.default_rng(9)
    with pytest.raises(ValueError):
        random_quadratic_mod1([2], rng, -1)


def test_random_quadratic_zero_n() -> None:
    rng = np.random.default_rng(10)
    assert random_quadratic_mod1([2, 3], rng, 0).size == 0


def test_beta_unit_samples_shape() -> None:
    rng = np.random.default_rng(11)
    x = beta_unit_samples(200, 2.0, 5.0, rng)
    assert x.shape == (200,)
    assert np.all(x > 0) and np.all(x < 1)


def test_beta_zero_n() -> None:
    rng = np.random.default_rng(12)
    assert beta_unit_samples(0, 1.0, 1.0, rng).size == 0


def test_beta_bad_parameters() -> None:
    rng = np.random.default_rng(13)
    with pytest.raises(ValueError):
        beta_unit_samples(10, 0.0, 1.0, rng)
    with pytest.raises(ValueError):
        beta_unit_samples(-1, 1.0, 1.0, rng)
