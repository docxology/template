"""Effective density from immiscible mass fractions (parallel mixture rule).

For mass fractions w_i and component densities ρ_i (all in kg/m³):

    1/ρ = Σ_i w_i / ρ_i

This is the standard mass-weighted harmonic mean for volume-additive mixing.
"""

from __future__ import annotations

from typing import Mapping


def mixture_density_mass_fractions(
    mass_fractions: Mapping[str, float],
    component_density_kg_m3: Mapping[str, float],
) -> float:
    """Compute mixture density from mass fractions and component densities.

    Args:
        mass_fractions: Maps component name to mass fraction (must sum to 1).
        component_density_kg_m3: Maps component name to density (kg/m³), all > 0.

    Returns:
        Mixture density (kg/m³).

    Raises:
        ValueError: If keys mismatch, fractions do not sum to 1 (within tol), or
            any density is non-positive.
    """
    keys = set(mass_fractions.keys())
    if keys != set(component_density_kg_m3.keys()):
        raise ValueError("mass_fractions and component_density_kg_m3 keys must match")
    total = sum(mass_fractions.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"mass fractions must sum to 1, got {total}")
    inv_rho = 0.0
    for name, w in mass_fractions.items():
        if w < 0:
            raise ValueError(f"negative mass fraction for {name}")
        rho_i = component_density_kg_m3[name]
        if rho_i <= 0:
            raise ValueError(f"density for {name} must be positive")
        inv_rho += w / rho_i
    return 1.0 / inv_rho
