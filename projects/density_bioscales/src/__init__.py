"""Density across biological and fluid scales — public API."""

from __future__ import annotations

from buoyancy import BuoyancyRegime, buoyancy_regime, density_difference_kg_m3, relative_density
from composite_density import mixture_density_mass_fractions
from constants import (
    DRY_AIR_MOLAR_MASS_KG_MOL,
    R_UNIVERSAL,
    STANDARD_PRESSURE_PA,
    T_STP_K,
)
from envelopes import Interval, interval_from_samples, scale_interval
from fluid_reference import (
    ETHANOL_DENSITY_20C_KG_M3,
    reference_liquids_table,
    water_density_linear_celsius,
)
from ideal_gas import (
    DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3,
    DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3,
    dry_air_density_stp_ideal_kg_m3,
    ideal_gas_density_kg_m3,
)
from insect_composition import (
    CompositionPreset,
    find_preset,
    list_presets,
    normalize_fractions,
    preset_adult_fly_illustrative,
)
from scenarios import (
    mixture_density_for_preset,
    scenario_custom_mass_map,
    scenario_water_contrast_at_25c,
    sweep_air_fraction_interval,
    sweep_internal_gas_mass_fraction_interval,
)

__all__ = [
    "BuoyancyRegime",
    "CompositionPreset",
    "DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3",
    "DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3",
    "DRY_AIR_MOLAR_MASS_KG_MOL",
    "ETHANOL_DENSITY_20C_KG_M3",
    "Interval",
    "R_UNIVERSAL",
    "STANDARD_PRESSURE_PA",
    "T_STP_K",
    "buoyancy_regime",
    "density_difference_kg_m3",
    "dry_air_density_stp_ideal_kg_m3",
    "find_preset",
    "ideal_gas_density_kg_m3",
    "interval_from_samples",
    "list_presets",
    "mixture_density_for_preset",
    "mixture_density_mass_fractions",
    "normalize_fractions",
    "preset_adult_fly_illustrative",
    "reference_liquids_table",
    "relative_density",
    "scale_interval",
    "scenario_custom_mass_map",
    "scenario_water_contrast_at_25c",
    "sweep_air_fraction_interval",
    "sweep_internal_gas_mass_fraction_interval",
    "water_density_linear_celsius",
]
