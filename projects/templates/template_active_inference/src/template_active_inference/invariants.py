"""Compatibility facade for analytical invariant builders.

Prefer ``from analytical.invariants import ...`` in new code.
"""

from analytical.invariants import (
    CORE_INVARIANTS,
    InvariantFn,
    all_invariants_pass,
    run_invariants,
)

__all__ = [
    "CORE_INVARIANTS",
    "InvariantFn",
    "all_invariants_pass",
    "run_invariants",
]
