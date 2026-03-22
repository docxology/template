"""Tests for composite_density module."""

from __future__ import annotations

import pytest

import composite_density


def test_single_component_is_that_density() -> None:
    rho = composite_density.mixture_density_mass_fractions(
        {"a": 1.0},
        {"a": 1234.5},
    )
    assert rho == pytest.approx(1234.5)


def test_two_component_harmonic_mean() -> None:
    # Equal mass 1000 and 2000 -> rho = 2 / (1/1000 + 1/2000) = 1333.33...
    rho = composite_density.mixture_density_mass_fractions(
        {"w": 0.5, "x": 0.5},
        {"w": 1000.0, "x": 2000.0},
    )
    assert rho == pytest.approx(4000.0 / 3.0, rel=1e-6)


def test_fractions_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum"):
        composite_density.mixture_density_mass_fractions(
            {"a": 0.5, "b": 0.4},
            {"a": 1000.0, "b": 1000.0},
        )


def test_keys_must_match() -> None:
    with pytest.raises(ValueError, match="keys"):
        composite_density.mixture_density_mass_fractions(
            {"a": 1.0},
            {"b": 1000.0},
        )


def test_negative_fraction_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        composite_density.mixture_density_mass_fractions(
            {"a": 1.1, "b": -0.1},
            {"a": 1000.0, "b": 1000.0},
        )


def test_nonpositive_density_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        composite_density.mixture_density_mass_fractions(
            {"a": 1.0},
            {"a": 0.0},
        )
