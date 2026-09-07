"""Primitives package — generated for domain: optimization."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the optimization domain."""
    from . import optimization
    return {"optimization": optimization.PRIMITIVES}


__all__ = ["PrimitiveSpec", "collect_primitives"]
