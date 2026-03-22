"""Phenomenological insect body composition presets (illustrative).

Mass fractions and tissue densities are **not** species-specific measurements;
they support reproducible scenario analysis. Widen bounds for uncertainty study.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

# Nominal component densities (kg/m³) — order-of-magnitude materials science
DENSITY_CUTICLE_KG_M3: float = 1300.0
DENSITY_SOFT_TISSUE_KG_M3: float = 1050.0
DENSITY_HEMOLYMPH_KG_M3: float = 1035.0
# Phenomenological effective density for gas-filled lumina in a **mass-fraction**
# mixture model. Literal air (~1.2 kg/m³) cannot be used with percent-level mass
# fractions in 1/ρ = Σ w_i/ρ_i without collapsing ρ; this proxy encodes
# tracheal/spiracular volume effects at toy-model resolution.
DENSITY_INTERNAL_GAS_SPACE_KG_M3: float = 240.0


@dataclass(frozen=True)
class CompositionPreset:
    """Named mass-fraction map (must sum to 1) plus metadata."""

    name: str
    mass_fractions: dict[str, float]
    description: str


def default_component_densities_kg_m3() -> dict[str, float]:
    """Standard component density table used with presets."""
    return {
        "cuticle": DENSITY_CUTICLE_KG_M3,
        "soft_tissue": DENSITY_SOFT_TISSUE_KG_M3,
        "hemolymph": DENSITY_HEMOLYMPH_KG_M3,
        "internal_gas": DENSITY_INTERNAL_GAS_SPACE_KG_M3,
    }


def preset_adult_fly_illustrative() -> CompositionPreset:
    """Illustrative winged insect: moderate internal gas compartment (toy model)."""
    return CompositionPreset(
        name="adult_fly_illustrative",
        mass_fractions={
            "cuticle": 0.12,
            "soft_tissue": 0.58,
            "hemolymph": 0.25,
            "internal_gas": 0.05,
        },
        description="Phenomenological adult fly–like mass split for model demos.",
    )


def preset_larva_illustrative() -> CompositionPreset:
    """Illustrative soft-bodied larva: small internal gas compartment in model."""
    return CompositionPreset(
        name="larva_illustrative",
        mass_fractions={
            "cuticle": 0.08,
            "soft_tissue": 0.72,
            "hemolymph": 0.19,
            "internal_gas": 0.01,
        },
        description="Phenomenological larva-like preset with low internal_gas fraction.",
    )


def preset_arid_beetle_illustrative() -> CompositionPreset:
    """Heavier cuticle, lower hemolymph — still illustrative."""
    return CompositionPreset(
        name="arid_beetle_illustrative",
        mass_fractions={
            "cuticle": 0.22,
            "soft_tissue": 0.52,
            "hemolymph": 0.20,
            "internal_gas": 0.06,
        },
        description="Phenomenological beetle-like preset emphasizing cuticle.",
    )


def list_presets() -> list[CompositionPreset]:
    """All built-in presets."""
    return [
        preset_adult_fly_illustrative(),
        preset_larva_illustrative(),
        preset_arid_beetle_illustrative(),
    ]


def find_preset(name: str) -> CompositionPreset:
    """Return preset by name."""
    for p in list_presets():
        if p.name == name:
            return p
    raise ValueError(f"unknown preset: {name}")


def normalize_fractions(raw: Mapping[str, float]) -> dict[str, float]:
    """Normalize a mapping of non-negative masses to mass fractions summing to 1."""
    if not raw:
        raise ValueError("empty fractions")
    total = sum(raw.values())
    if total <= 0:
        raise ValueError("sum of masses must be positive")
    return {k: v / total for k, v in raw.items()}
