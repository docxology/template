"""Tests for ideal_gas module."""

from __future__ import annotations

import pytest

import ideal_gas
from constants import DRY_AIR_MOLAR_MASS_KG_MOL, STANDARD_PRESSURE_PA, T_STP_K


def test_ideal_gas_nitrogen_stp_order_of_magnitude() -> None:
    from constants import MOLAR_MASS_N2_KG_MOL

    rho = ideal_gas.ideal_gas_density_kg_m3(
        STANDARD_PRESSURE_PA, T_STP_K, MOLAR_MASS_N2_KG_MOL
    )
    assert 1.1 < rho < 1.4


def test_dry_air_stp_inside_literature_band() -> None:
    rho = ideal_gas.dry_air_density_stp_ideal_kg_m3()
    assert ideal_gas.DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3 <= rho
    assert rho <= ideal_gas.DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3


def test_dry_air_stp_matches_manual_formula() -> None:
    rho = ideal_gas.dry_air_density_stp_ideal_kg_m3()
    expected = (STANDARD_PRESSURE_PA * DRY_AIR_MOLAR_MASS_KG_MOL) / (
        __import__("constants").R_UNIVERSAL * T_STP_K
    )
    assert abs(rho - expected) < 1e-9


@pytest.mark.parametrize(
    "bad_p,bad_t,bad_m",
    [
        (-1, 300, 0.029),
        (101325, -1, 0.029),
        (101325, 300, 0),
    ],
)
def test_ideal_gas_rejects_nonpositive(
    bad_p: float, bad_t: float, bad_m: float
) -> None:
    with pytest.raises(ValueError):
        ideal_gas.ideal_gas_density_kg_m3(bad_p, bad_t, bad_m)
