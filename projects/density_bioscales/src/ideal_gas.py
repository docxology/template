"""Ideal-gas density from \\(\\rho = p M / (R T)\\).

Reference STP comparisons use tabulated literature bands in docstrings; ideal gas
is a model, not a measurement.
"""

from __future__ import annotations

from constants import (
    DRY_AIR_MOLAR_MASS_KG_MOL,
    R_UNIVERSAL,
    STANDARD_PRESSURE_PA,
    T_STP_K,
)


def ideal_gas_density_kg_m3(
    pressure_pa: float,
    temperature_k: float,
    molar_mass_kg_mol: float,
) -> float:
    """Compute ideal-gas mass density (kg/m³).

    Args:
        pressure_pa: Absolute pressure in pascals.
        temperature_k: Absolute temperature in kelvin.
        molar_mass_kg_mol: Molar mass in kg/mol.

    Returns:
        Mass density in kg/m³.

    Raises:
        ValueError: If pressure, temperature, or molar mass is non-positive.
    """
    if pressure_pa <= 0:
        raise ValueError("pressure_pa must be positive")
    if temperature_k <= 0:
        raise ValueError("temperature_k must be positive")
    if molar_mass_kg_mol <= 0:
        raise ValueError("molar_mass_kg_mol must be positive")
    return (pressure_pa * molar_mass_kg_mol) / (R_UNIVERSAL * temperature_k)


# Literature-derived dry-air density at STP is often quoted ~1.2–1.3 kg/m³
# (handbooks; ideal gas at 101325 Pa, 273.15 K gives ~1.293 kg/m³ for 0.028965 kg/mol).
DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3: float = 1.18
DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3: float = 1.32


def dry_air_density_stp_ideal_kg_m3(
    pressure_pa: float | None = None,
    temperature_k: float | None = None,
    molar_mass_kg_mol: float | None = None,
) -> float:
    """Dry-air ideal density at STP (default IUPAC pressure and 273.15 K)."""
    p = STANDARD_PRESSURE_PA if pressure_pa is None else pressure_pa
    t = T_STP_K if temperature_k is None else temperature_k
    m = DRY_AIR_MOLAR_MASS_KG_MOL if molar_mass_kg_mol is None else molar_mass_kg_mol
    return ideal_gas_density_kg_m3(p, t, m)
