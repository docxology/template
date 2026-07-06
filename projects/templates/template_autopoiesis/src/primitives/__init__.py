"""Primitives package for template_autopoiesis.

Provides collect_primitives() which returns a mapping from domain name to a
tuple of PrimitiveSpec objects.  Each PrimitiveSpec encapsulates a callable
kernel, example inputs, expected outputs, tolerances, and negative controls.
"""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple[PrimitiveSpec, ...]]:
    """Return all registered primitive specs grouped by domain."""
    from . import optimization, dynamics, statistics, signal, graph

    return {
        "optimization": optimization.PRIMITIVES,
        "dynamics": dynamics.PRIMITIVES,
        "statistics": statistics.PRIMITIVES,
        "signal": signal.PRIMITIVES,
        "graph": graph.PRIMITIVES,
    }


__all__ = ["PrimitiveSpec", "collect_primitives"]
