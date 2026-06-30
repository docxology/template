"""Tests for src.methods_dsl.examples_methods — the two worked examples."""

from __future__ import annotations

from src.methods_dsl.compiler import compile_method
from src.methods_dsl.examples_methods import (
    all_example_methods,
    pbs_preparation_method,
    sensor_calibration_method,
)
from src.methods_dsl.validation import run_all_gates
from src.methods_dsl.vocabulary import Target


def test_pbs_preparation_method_is_valid_and_human_target():
    method = pbs_preparation_method()
    assert method.target is Target.HUMAN
    assert all(g.passed for g in run_all_gates(method))


def test_pbs_preparation_method_compiles_with_five_steps():
    plan = compile_method(pbs_preparation_method())
    assert len(plan.steps) == 5
    assert [s.step_id for s in plan.steps] == [1, 2, 3, 4, 5]


def test_sensor_calibration_method_mixes_automated_and_human_targets():
    method = sensor_calibration_method()
    assert method.target is Target.AUTOMATED
    targets = {step.target for step in method.steps}
    assert Target.AUTOMATED in targets
    assert Target.HUMAN in targets  # the operator sign-off step
    assert all(g.passed for g in run_all_gates(method))


def test_sensor_calibration_method_compiles_with_four_steps():
    plan = compile_method(sensor_calibration_method())
    assert len(plan.steps) == 4


def test_all_example_methods_returns_both_in_fixed_order():
    methods = all_example_methods()
    assert [m.name for m in methods] == ["PBSPreparation", "SensorCalibrationSweep"]
