"""Sanity checks on declared physical constants."""

from __future__ import annotations

import constants


def test_r_universal_positive() -> None:
    assert constants.R_UNIVERSAL > 0


def test_standard_pressure_typical_atm() -> None:
    assert 100_000 < constants.STANDARD_PRESSURE_PA < 102_000


def test_molar_masses_ordered() -> None:
    assert constants.MOLAR_MASS_N2_KG_MOL < constants.MOLAR_MASS_O2_KG_MOL
    assert constants.MOLAR_MASS_O2_KG_MOL < constants.MOLAR_MASS_CO2_KG_MOL
