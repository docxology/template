"""Primitives package — generated for domain: graph."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the graph domain."""
    from . import graph
    return {"graph": graph.PRIMITIVES}


__all__ = ["PrimitiveSpec", "collect_primitives"]
