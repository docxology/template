"""Primitives package — generated for domain: dynamics."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the dynamics domain."""
    from . import dynamics
    return {"dynamics": dynamics.PRIMITIVES}


__all__ = ["PrimitiveSpec", "collect_primitives"]
