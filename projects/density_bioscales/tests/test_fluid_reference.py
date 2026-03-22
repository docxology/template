"""Tests for fluid_reference module."""

from __future__ import annotations

import fluid_reference


def test_water_15c_in_liquid_band() -> None:
    assert 998.0 < fluid_reference.WATER_DENSITY_15C_KG_M3 < 1000.5


def test_water_linear_matches_endpoints() -> None:
    r15 = fluid_reference.water_density_linear_celsius(15.0)
    r25 = fluid_reference.water_density_linear_celsius(25.0)
    assert abs(r15 - fluid_reference.WATER_DENSITY_15C_KG_M3) < 0.05
    assert abs(r25 - fluid_reference.WATER_DENSITY_25C_KG_M3) < 0.5


def test_reference_table_keys() -> None:
    table = fluid_reference.reference_liquids_table()
    assert len(table) >= 4
    assert "water" in table
    assert table["ethanol"]["density_kg_m3"] == fluid_reference.ETHANOL_DENSITY_20C_KG_M3
