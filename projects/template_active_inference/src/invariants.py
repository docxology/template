"""Compatibility facade for analytical invariant builders."""

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
