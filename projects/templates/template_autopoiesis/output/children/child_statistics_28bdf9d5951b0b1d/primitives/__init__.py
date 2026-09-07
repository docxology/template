"""Primitives package — generated for domain: statistics."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the statistics domain."""
    from . import statistics
    return {"statistics": statistics.PRIMITIVES}


__all__ = ["PrimitiveSpec", "collect_primitives"]
