"""Tests for buoyancy helpers."""

from __future__ import annotations

import pytest

import buoyancy


def test_relative_density_water_vs_water() -> None:
    assert buoyancy.relative_density(997.0, 997.0) == pytest.approx(1.0)


def test_floats_when_lighter() -> None:
    assert (
        buoyancy.buoyancy_regime(900.0, 1000.0) == buoyancy.BuoyancyRegime.FLOATS
    )


def test_sinks_when_heavier() -> None:
    assert buoyancy.buoyancy_regime(1100.0, 1000.0) == buoyancy.BuoyancyRegime.SINKS


def test_neutral_within_tol() -> None:
    assert (
        buoyancy.buoyancy_regime(1000.0, 1000.0, rel_tol=1e-9)
        == buoyancy.BuoyancyRegime.NEUTRAL
    )


def test_density_difference() -> None:
    assert buoyancy.density_difference_kg_m3(1005.0, 1000.0) == pytest.approx(5.0)


def test_relative_density_bad_medium() -> None:
    with pytest.raises(ValueError):
        buoyancy.relative_density(1000.0, 0.0)


def test_relative_density_bad_body() -> None:
    with pytest.raises(ValueError):
        buoyancy.relative_density(0.0, 1000.0)
