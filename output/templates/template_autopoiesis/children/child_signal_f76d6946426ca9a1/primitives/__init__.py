"""Primitives package — generated for domain: signal."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the signal domain."""
    from . import signal
    return {"signal": signal.PRIMITIVES}


__all__ = ["PrimitiveSpec", "collect_primitives"]
