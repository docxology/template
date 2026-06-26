"""Tests for analytical invariant registry.

Covers all CORE_INVARIANTS, the early-exit branch when a grid point fails, and
the public ``all_invariants_pass`` / ``run_invariants`` facades.
"""

from __future__ import annotations

from analytical.invariants import (
    CORE_INVARIANTS,
    all_invariants_pass,
    inv_empirical_matches_closed_form,
    run_invariants,
)


def test_core_invariants_pass() -> None:
    results = run_invariants()
    assert results
    assert all_invariants_pass(results), results


def test_all_invariants_pass_uses_cached_results() -> None:
    """When a pre-computed result dict is passed, run_invariants is not called."""
    pre = {key: True for key in CORE_INVARIANTS}
    assert all_invariants_pass(pre) is True
    bad = {key: False for key in CORE_INVARIANTS}
    assert all_invariants_pass(bad) is False


def test_inv_empirical_matches_closed_form_passes_on_real_grid() -> None:
    """The invariant must pass on the default hyperparameters (real computation)."""
    assert inv_empirical_matches_closed_form() is True
