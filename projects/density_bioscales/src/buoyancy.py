"""Relative density and sink/float classification vs a fluid medium."""

from __future__ import annotations

from enum import Enum


class BuoyancyRegime(str, Enum):
    """Qualitative regime for a rigid body in a static fluid (no surface tension)."""

    FLOATS = "floats"
    NEUTRAL = "neutral"
    SINKS = "sinks"


def relative_density(rho_body_kg_m3: float, rho_medium_kg_m3: float) -> float:
    """Ratio ρ_body / ρ_medium."""
    if rho_medium_kg_m3 <= 0:
        raise ValueError("rho_medium_kg_m3 must be positive")
    if rho_body_kg_m3 <= 0:
        raise ValueError("rho_body_kg_m3 must be positive")
    return rho_body_kg_m3 / rho_medium_kg_m3


def buoyancy_regime(
    rho_body_kg_m3: float,
    rho_medium_kg_m3: float,
    rel_tol: float = 1e-6,
) -> BuoyancyRegime:
    """Classify float/neutral/sink using density comparison.

    Neutral if relative density is 1 within rel_tol.
    """
    r = relative_density(rho_body_kg_m3, rho_medium_kg_m3)
    if abs(r - 1.0) <= rel_tol:
        return BuoyancyRegime.NEUTRAL
    if r < 1.0:
        return BuoyancyRegime.FLOATS
    return BuoyancyRegime.SINKS


def density_difference_kg_m3(rho_body_kg_m3: float, rho_medium_kg_m3: float) -> float:
    """ρ_body − ρ_medium (kg/m³)."""
    return rho_body_kg_m3 - rho_medium_kg_m3
