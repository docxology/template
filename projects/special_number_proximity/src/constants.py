"""Named mathematical constants and coarse number-theoretic classification."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class NumberClass(str, Enum):
    """Informative label for exposition (not a formal proof of transcendence)."""

    TRANSCENDENTAL = "transcendental"
    IRRATIONAL_ALGEBRAIC = "irrational_algebraic"
    RATIONAL = "rational"


@dataclass(frozen=True)
class NamedConstant:
    """A real number used in experiments."""

    key: str
    value: float
    number_class: NumberClass
    note: str


def named_constants() -> dict[str, NamedConstant]:
    """Return a stable registry of standard constants for analysis scripts."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return {
        "pi": NamedConstant(
            "pi",
            math.pi,
            NumberClass.TRANSCENDENTAL,
            "Circle constant; transcendental (Lindemann–Weierstrass context).",
        ),
        "e": NamedConstant(
            "e",
            math.e,
            NumberClass.TRANSCENDENTAL,
            "Natural exponential base; transcendental (Hermite).",
        ),
        "sqrt2": NamedConstant(
            "sqrt2",
            math.sqrt(2.0),
            NumberClass.IRRATIONAL_ALGEBRAIC,
            "Root of x^2 - 2; irrational algebraic degree 2.",
        ),
        "sqrt3": NamedConstant(
            "sqrt3",
            math.sqrt(3.0),
            NumberClass.IRRATIONAL_ALGEBRAIC,
            "Root of x^2 - 3.",
        ),
        "golden_ratio": NamedConstant(
            "golden_ratio",
            phi,
            NumberClass.IRRATIONAL_ALGEBRAIC,
            "Degree-2 algebraic; badly approximable (bounded partial quotients).",
        ),
        "one_sixth": NamedConstant(
            "one_sixth",
            1.0 / 6.0,
            NumberClass.RATIONAL,
            "Rational control; equals ζ(2)/π² exactly as 1/6.",
        ),
        "ln2": NamedConstant(
            "ln2",
            math.log(2.0),
            NumberClass.TRANSCENDENTAL,
            "Natural log of 2; transcendental (Lindemann-type results for log algebraics).",
        ),
    }


def constant_lookup() -> Mapping[str, float]:
    """Map keys to raw floating values."""
    return {k: v.value for k, v in named_constants().items()}
