"""Named scenarios combining composition, mixture rule, and medium contrast.

Outputs are model artefacts under stated presets, not measured biology.
"""

from __future__ import annotations

from composite_density import mixture_density_mass_fractions
from envelopes import Interval, interval_from_samples
from fluid_reference import WATER_DENSITY_25C_KG_M3
from insect_composition import (
    CompositionPreset,
    default_component_densities_kg_m3,
    normalize_fractions,
)


def internal_gas_export_sweep_bounds(preset: CompositionPreset) -> tuple[float, float]:
    """Default internal_gas mass-fraction range for tabular exports and figures.

    Lower bound is fixed at 0.01; upper bound extends slightly beyond the
    preset's nominal internal_gas fraction so sensitivity bands are visible
    without re-tuning per manuscript revision.
    """
    g = preset.mass_fractions["internal_gas"]
    return 0.01, max(0.02, g + 0.04)


def mixture_density_for_preset(
    preset: CompositionPreset,
    component_density_kg_m3: dict[str, float] | None = None,
) -> float:
    """Effective body density for a composition preset."""
    densities = (
        default_component_densities_kg_m3()
        if component_density_kg_m3 is None
        else component_density_kg_m3
    )
    return mixture_density_mass_fractions(preset.mass_fractions, densities)


def sweep_internal_gas_mass_fraction_interval(
    base_preset: CompositionPreset,
    gas_fraction_min: float,
    gas_fraction_max: float,
    component_density_kg_m3: dict[str, float] | None = None,
) -> Interval:
    """Envelope effective density when only the internal_gas mass fraction varies.

    Other components are scaled proportionally so all mass fractions sum to 1.
    """
    if (
        gas_fraction_min < 0
        or gas_fraction_max > 1
        or gas_fraction_min > gas_fraction_max
    ):
        raise ValueError("invalid internal_gas fraction bounds")
    densities = (
        default_component_densities_kg_m3()
        if component_density_kg_m3 is None
        else component_density_kg_m3
    )
    gas_key = "internal_gas"
    samples: list[float] = []
    for f_gas in (gas_fraction_min, gas_fraction_max):
        other = {k: v for k, v in base_preset.mass_fractions.items() if k != gas_key}
        if not other:
            raise ValueError("preset must have non-gas components")
        scale = (1.0 - f_gas) / sum(other.values())
        adjusted = {k: v * scale for k, v in other.items()}
        adjusted[gas_key] = f_gas
        samples.append(mixture_density_mass_fractions(adjusted, densities))
    return interval_from_samples(samples)


def scenario_water_contrast_at_25c(
    preset: CompositionPreset,
    component_density_kg_m3: dict[str, float] | None = None,
) -> tuple[float, float]:
    """Return (rho_body, rho_water) at reference 25 °C water density."""
    rho_b = mixture_density_for_preset(preset, component_density_kg_m3)
    return rho_b, WATER_DENSITY_25C_KG_M3


def scenario_custom_mass_map(
    masses: dict[str, float],
    component_density_kg_m3: dict[str, float] | None = None,
) -> float:
    """Mixture density from arbitrary non-negative masses (normalized)."""
    fr = normalize_fractions(masses)
    densities = (
        default_component_densities_kg_m3()
        if component_density_kg_m3 is None
        else component_density_kg_m3
    )
    return mixture_density_mass_fractions(fr, densities)


# Backward-compatible alias (spec / manuscript wording)
def sweep_air_fraction_interval(
    base_preset: CompositionPreset,
    air_fraction_min: float,
    air_fraction_max: float,
    component_density_kg_m3: dict[str, float] | None = None,
) -> Interval:
    """Alias for :func:`sweep_internal_gas_mass_fraction_interval`."""
    return sweep_internal_gas_mass_fraction_interval(
        base_preset, air_fraction_min, air_fraction_max, component_density_kg_m3
    )
