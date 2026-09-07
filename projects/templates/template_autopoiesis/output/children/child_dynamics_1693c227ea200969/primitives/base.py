"""Base primitive specification dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class PrimitiveSpec:
    """Specification for a single primitive kernel function."""

    name: str
    domain: str
    fn: Callable
    callable_name: str
    example_input: Any
    expected: Any
    tolerance: float = 1e-6
    negative_control: Optional[Callable] = None
