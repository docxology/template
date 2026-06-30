"""Tests for src.methods_dsl.validation — staged validation gates."""

from __future__ import annotations

from src.methods_dsl.validation import (
    plan_gate,
    run_all_gates,
    semantic_gate,
    structural_gate,
    target_gate,
)


def test_structural_gate_passes_for_valid_method(linear_method):
    result = structural_gate(linear_method)
    assert result.passed is True
    assert result.issues == ()


def test_structural_gate_catches_unknown_dependency(unknown_dependency_method):
    result = structural_gate(unknown_dependency_method)
    assert result.passed is False
    assert any("unknown step_id 99" in issue for issue in result.issues)


def test_structural_gate_catches_duplicate_step_id(duplicate_step_id_method):
    result = structural_gate(duplicate_step_id_method)
    assert result.passed is False
    assert any("duplicate step_id 1" in issue for issue in result.issues)


def test_semantic_gate_passes_for_valid_method(linear_method):
    result = semantic_gate(linear_method)
    assert result.passed is True


def test_semantic_gate_catches_unknown_unit(unknown_unit_method):
    result = semantic_gate(unknown_unit_method)
    assert result.passed is False
    assert any("unknown unit" in issue for issue in result.issues)


def test_plan_gate_passes_for_acyclic_method(linear_method, diamond_method):
    assert plan_gate(linear_method).passed is True
    assert plan_gate(diamond_method).passed is True


def test_plan_gate_catches_cycle(cyclic_method):
    result = plan_gate(cyclic_method)
    assert result.passed is False
    assert any("cyclic dependency" in issue for issue in result.issues)


def test_target_gate_passes_for_compatible_steps(linear_method, diamond_method):
    assert target_gate(linear_method).passed is True
    assert target_gate(diamond_method).passed is True


def test_target_gate_catches_compute_on_human_target(target_mismatch_method):
    result = target_gate(target_mismatch_method)
    assert result.passed is False
    assert any("cannot run on target" in issue for issue in result.issues)


def test_run_all_gates_returns_four_gates_for_valid_method(linear_method):
    results = run_all_gates(linear_method)
    assert [g.name for g in results] == ["structural", "semantic", "plan", "target"]
    assert all(g.passed for g in results)


def test_run_all_gates_short_circuits_after_structural_failure(duplicate_step_id_method):
    results = run_all_gates(duplicate_step_id_method)
    assert [g.name for g in results] == ["structural", "semantic"]
    assert results[0].passed is False


def test_run_all_gates_short_circuits_after_semantic_failure(unknown_unit_method):
    results = run_all_gates(unknown_unit_method)
    assert [g.name for g in results] == ["structural", "semantic"]
    assert results[0].passed is True
    assert results[1].passed is False


def test_run_all_gates_runs_plan_and_target_when_structural_and_semantic_pass(cyclic_method):
    results = run_all_gates(cyclic_method)
    assert [g.name for g in results] == ["structural", "semantic", "plan", "target"]
    assert results[2].passed is False  # plan gate catches the cycle
