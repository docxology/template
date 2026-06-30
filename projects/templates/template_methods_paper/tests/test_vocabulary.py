"""Tests for src.methods_dsl.vocabulary — controlled step/target vocabulary."""

from __future__ import annotations

from src.methods_dsl.vocabulary import StepKind, Target, target_accepts


def test_step_kind_values_are_lowercase_strings():
    for kind in StepKind:
        assert kind.value == kind.value.lower()


def test_target_values():
    assert {t.value for t in Target} == {"human", "automated", "simulation"}


def test_target_accepts_compute_only_on_automated():
    assert target_accepts(Target.AUTOMATED, StepKind.COMPUTE) is True
    assert target_accepts(Target.HUMAN, StepKind.COMPUTE) is False
    assert target_accepts(Target.SIMULATION, StepKind.COMPUTE) is False


def test_target_accepts_non_automated_only_kind_everywhere():
    for target in Target:
        assert target_accepts(target, StepKind.ADD) is True
        assert target_accepts(target, StepKind.MEASURE) is True
