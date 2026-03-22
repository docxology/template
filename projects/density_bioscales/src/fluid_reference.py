"""Reference liquid densities at stated temperatures.

Values are handbook-style references for reproducible comparisons, not fits to
new experimental data. See module docstrings per substance.
"""

from __future__ import annotations

# Water: ~999.1 kg/m³ at 15 °C, ~997.0 kg/m³ at 25 °C (engineering tables)
WATER_DENSITY_15C_KG_M3: float = 999.1
WATER_DENSITY_25C_KG_M3: float = 997.0

# Ethanol: ~789 kg/m³ at 20 °C (CRC order of magnitude)
ETHANOL_DENSITY_20C_KG_M3: float = 789.0

# Seawater (approx. 3.5 % salinity): ~1025 kg/m³ at 15 °C (illustrative)
SEAWATER_DENSITY_15C_KG_M3: float = 1025.0


def water_density_linear_celsius(
    temp_celsius: float,
    t_ref_celsius: float = 15.0,
    rho_ref_kg_m3: float = WATER_DENSITY_15C_KG_M3,
    thermal_expansion_coeff_per_k: float = 2.07e-4,
) -> float:
    """Linear thermal model: ρ(T) ≈ ρ_ref × (1 − α (T − T_ref)).

    Coefficient α chosen so endpoints approximate 15 °C and 25 °C table values
    (~999.1 and ~997.0 kg/m³) within a few tenths of a kg/m³.

    Args:
        temp_celsius: Temperature in degrees Celsius.
        t_ref_celsius: Reference temperature (°C).
        rho_ref_kg_m3: Density at reference temperature (kg/m³).
        thermal_expansion_coeff_per_k: Volumetric expansion scale (1/K).

    Returns:
        Approximate density (kg/m³).
    """
    delta_t = temp_celsius - t_ref_celsius
    return rho_ref_kg_m3 * (1.0 - thermal_expansion_coeff_per_k * delta_t)


def reference_liquids_table() -> dict[str, dict[str, float]]:
    """Return a serialisable table of reference densities and conditions."""
    return {
        "water": {"temp_c": 15.0, "density_kg_m3": WATER_DENSITY_15C_KG_M3},
        "water_25c": {"temp_c": 25.0, "density_kg_m3": WATER_DENSITY_25C_KG_M3},
        "ethanol": {"temp_c": 20.0, "density_kg_m3": ETHANOL_DENSITY_20C_KG_M3},
        "seawater": {"temp_c": 15.0, "density_kg_m3": SEAWATER_DENSITY_15C_KG_M3},
    }
