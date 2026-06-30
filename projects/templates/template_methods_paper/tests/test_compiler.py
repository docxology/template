"""Tests for src.methods_dsl.compiler — deterministic compilation."""

from __future__ import annotations

import pytest

from src.methods_dsl.compiler import (
    CycleError,
    MethodValidationError,
    compile_method,
    topological_order,
)


def test_topological_order_linear(linear_method):
    order = topological_order(linear_method)
    assert [s.step_id for s in order] == [1, 2, 3]


def test_topological_order_diamond_deterministic_tiebreak(diamond_method):
    order = topological_order(diamond_method)
    # Both 2 and 3 become ready simultaneously after 1; the deterministic
    # tie-break (ascending step_id) must always pick 2 before 3.
    assert [s.step_id for s in order] == [1, 2, 3, 4]


def test_topological_order_raises_cycle_error(cyclic_method):
    with pytest.raises(CycleError, match="cyclic dependency"):
        topological_order(cyclic_method)


def test_compile_method_produces_plan_with_correct_step_count(linear_method):
    plan = compile_method(linear_method)
    assert plan.method_name == "LinearDemo"
    assert len(plan.steps) == 3
    assert [s.order for s in plan.steps] == [0, 1, 2]


def test_compile_method_raises_on_invalid_method(cyclic_method):
    with pytest.raises(MethodValidationError, match="failed validation"):
        compile_method(cyclic_method)


def test_compile_method_raises_on_target_mismatch(target_mismatch_method):
    with pytest.raises(MethodValidationError) as exc_info:
        compile_method(target_mismatch_method)
    assert exc_info.value.method_name == "TargetMismatch"
    assert any(not g.passed for g in exc_info.value.gate_results)


def test_compile_method_is_deterministic(linear_method):
    """Negative control for BPL's determinism guarantee: same Method -> same plan_hash, every time."""
    hashes = {compile_method(linear_method).plan_hash for _ in range(5)}
    assert len(hashes) == 1


def test_compile_method_hash_changes_with_step_order_change(linear_method, diamond_method):
    """Different methods must not collide (negative control for the hash itself)."""
    assert compile_method(linear_method).plan_hash != compile_method(diamond_method).plan_hash


def test_plan_to_canonical_dict_matches_hash_inputs(linear_method):
    plan = compile_method(linear_method)
    canonical = plan.to_canonical_dict()
    assert canonical["method_name"] == "LinearDemo"
    assert len(canonical["steps"]) == 3
    assert canonical["steps"][0]["order"] == 0
