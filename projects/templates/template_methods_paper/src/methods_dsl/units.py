"""Minimal dimensional-safety unit system for the methods DSL.

A deliberately small alternative to a full unit library (``pint`` etc.):
just enough dimensional analysis to catch the class of bug BPL's design
principle #3 names directly — "the type system catches ``mL + g`` at
compile time, not at the bench." Every unit string maps to one
:class:`Dimension`; arithmetic across incompatible dimensions raises
:class:`DimensionError` instead of silently producing a meaningless number.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Dimension(Enum):
    """Physical dimension family a unit belongs to."""

    MASS = "mass"
    VOLUME = "volume"
    TEMPERATURE = "temperature"
    TIME = "time"
    MOLAR_CONCENTRATION = "molar_concentration"
    MASS_CONCENTRATION = "mass_concentration"
    COUNT = "count"
    DIMENSIONLESS = "dimensionless"


class DimensionError(ValueError):
    """Raised when an operation mixes incompatible physical dimensions."""


# unit -> (Dimension, multiplicative factor to the dimension's base unit)
# Base units: g (mass), L (volume), degC (temperature, handled separately —
# affine, not multiplicative), s (time), mol/L (molar concentration), g/L
# (mass concentration), count (count).
#
# Molar concentration ("mol/L", "mM") and mass concentration ("g/L") are
# DELIBERATELY distinct Dimension values, not two units of one shared
# "concentration" dimension. Converting between them requires a substance's
# molar mass, which this DSL does not carry (see manuscript §7, "out of
# scope": BPL's MW-aware concentration conversions are not implemented
# here). Without that context, `1 mol/L + 1 g/L` is exactly the same class
# of category error as `1 mL + 1 g` — treating them as compatible would
# silently produce a physically meaningless number. Splitting the dimension
# lets the existing `check_compatible` machinery reject the mix for free.
_UNIT_TABLE: dict[str, tuple[Dimension, float]] = {
    # mass -> base gram
    "g": (Dimension.MASS, 1.0),
    "mg": (Dimension.MASS, 1e-3),
    "kg": (Dimension.MASS, 1e3),
    "ug": (Dimension.MASS, 1e-6),
    # volume -> base liter
    "L": (Dimension.VOLUME, 1.0),
    "mL": (Dimension.VOLUME, 1e-3),
    "uL": (Dimension.VOLUME, 1e-6),
    # time -> base second
    "s": (Dimension.TIME, 1.0),
    "min": (Dimension.TIME, 60.0),
    "h": (Dimension.TIME, 3600.0),
    # molar concentration -> base mol/L
    "mol/L": (Dimension.MOLAR_CONCENTRATION, 1.0),
    "mM": (Dimension.MOLAR_CONCENTRATION, 1e-3),
    # mass concentration -> base g/L (its own dimension — not interchangeable
    # with molar concentration without a molar mass; see note above)
    "g/L": (Dimension.MASS_CONCENTRATION, 1.0),
    # count -> base count
    "count": (Dimension.COUNT, 1.0),
    # dimensionless
    "fraction": (Dimension.DIMENSIONLESS, 1.0),
    "percent": (Dimension.DIMENSIONLESS, 0.01),
}

# Temperature is affine (degC = K - 273.15), so it cannot share the
# multiplicative table above; it is tracked as its own dimension with no
# base-unit conversion beyond degC/K, which this DSL does not need to mix.
_TEMPERATURE_UNITS = {"degC", "K"}


def dimension_of(unit: str) -> Dimension:
    """Resolve *unit* to its :class:`Dimension`.

    Raises:
        DimensionError: If *unit* is not in the controlled vocabulary.
    """
    if unit in _TEMPERATURE_UNITS:
        return Dimension.TEMPERATURE
    entry = _UNIT_TABLE.get(unit)
    if entry is None:
        raise DimensionError(f"unknown unit {unit!r} — not in the controlled unit vocabulary")
    return entry[0]


def known_units() -> tuple[str, ...]:
    """Return every unit string the controlled vocabulary recognizes."""
    return tuple(sorted({*_UNIT_TABLE.keys(), *_TEMPERATURE_UNITS}))


@dataclass(frozen=True)
class Quantity:
    """A value paired with its unit, e.g. ``Quantity(10.0, "mL")``."""

    value: float
    unit: str

    @property
    def dimension(self) -> Dimension:
        """Process dimension."""
        return dimension_of(self.unit)

    def to_base(self) -> float:
        """Convert *value* to the dimension's base unit (mass→g, volume→L, time→s).

        Raises:
            DimensionError: For temperature, which has no shared base unit
                in this DSL (degC and K are tracked but never auto-converted).
        """
        if self.unit in _TEMPERATURE_UNITS:
            raise DimensionError(f"temperature unit {self.unit!r} has no shared base — compare degC to degC only")
        _, factor = _UNIT_TABLE[self.unit]
        return self.value * factor

    def __add__(self, other: Quantity) -> Quantity:
        check_compatible(self, other)
        if self.dimension == Dimension.TEMPERATURE:
            raise DimensionError("temperature quantities are not additive in this DSL")
        base_sum = self.to_base() + other.to_base()
        _, factor = _UNIT_TABLE[self.unit]
        return Quantity(base_sum / factor, self.unit)


def check_compatible(a: Quantity, b: Quantity) -> None:
    """Raise :class:`DimensionError` unless *a* and *b* share a dimension.

    This is the concrete realization of "dimensional safety": the exact
    ``mL + g`` mistake BPL's design principle #3 calls out at compile time.
    """
    if a.dimension != b.dimension:
        raise DimensionError(
            f"incompatible dimensions: {a.unit!r} ({a.dimension.value}) vs {b.unit!r} ({b.dimension.value})"
        )
