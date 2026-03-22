"""Tests for scenario composition."""

from __future__ import annotations

import pytest

import insect_composition
from insect_composition import CompositionPreset
import scenarios


def test_internal_gas_export_sweep_bounds_valid() -> None:
    for p in insect_composition.list_presets():
        lo, hi = scenarios.internal_gas_export_sweep_bounds(p)
        assert 0.0 <= lo < hi <= 1.0


def test_mixture_density_for_preset_reasonable() -> None:
    p = insect_composition.preset_adult_fly_illustrative()
    rho = scenarios.mixture_density_for_preset(p)
    assert 500 < rho < 1200


def test_sweep_internal_gas_increases_interval_width() -> None:
    p = insect_composition.preset_larva_illustrative()
    narrow = scenarios.sweep_internal_gas_mass_fraction_interval(p, 0.02, 0.03)
    wide = scenarios.sweep_internal_gas_mass_fraction_interval(p, 0.01, 0.20)
    assert wide.width() >= narrow.width()


def test_sweep_air_alias_matches_internal_gas() -> None:
    p = insect_composition.preset_adult_fly_illustrative()
    a = scenarios.sweep_air_fraction_interval(p, 0.02, 0.08)
    b = scenarios.sweep_internal_gas_mass_fraction_interval(p, 0.02, 0.08)
    assert a.low == pytest.approx(b.low)
    assert a.high == pytest.approx(b.high)


def test_sweep_internal_gas_invalid_bounds() -> None:
    p = insect_composition.preset_adult_fly_illustrative()
    with pytest.raises(ValueError):
        scenarios.sweep_internal_gas_mass_fraction_interval(p, 0.5, 0.3)


def test_water_contrast() -> None:
    p = insect_composition.preset_arid_beetle_illustrative()
    rb, rw = scenarios.scenario_water_contrast_at_25c(p)
    assert rb > 0 and rw > 0


def test_custom_mass_map() -> None:
    rho = scenarios.scenario_custom_mass_map(
        {"cuticle": 1.0, "soft_tissue": 1.0, "hemolymph": 1.0, "internal_gas": 0.01}
    )
    assert rho > 0


def test_sweep_rejects_only_gas_preset() -> None:
    only_gas = CompositionPreset(
        name="only_gas",
        mass_fractions={"internal_gas": 1.0},
        description="invalid for sweep",
    )
    with pytest.raises(ValueError, match="non-gas"):
        scenarios.sweep_internal_gas_mass_fraction_interval(only_gas, 0.1, 0.2)
