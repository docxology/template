"""Tests for src.methods_dsl.model — Parameter, Resource, Step, Method."""

from __future__ import annotations

import pytest

from src.methods_dsl.model import Method, MethodModelError, Parameter, Resource, Step
from src.methods_dsl.units import Quantity
from src.methods_dsl.vocabulary import StepKind, Target


def test_parameter_requires_name():
    with pytest.raises(MethodModelError, match="non-empty"):
        Parameter("", Quantity(1.0, "mL"))


def test_resource_requires_name_and_kind():
    with pytest.raises(MethodModelError, match="name"):
        Resource("", kind="reagent")
    with pytest.raises(MethodModelError, match="kind"):
        Resource("Water", kind="")


def test_step_requires_positive_step_id():
    with pytest.raises(MethodModelError, match="positive"):
        Step(step_id=0, name="x", kind=StepKind.ADD, target=Target.HUMAN)
    with pytest.raises(MethodModelError, match="positive"):
        Step(step_id=-1, name="x", kind=StepKind.ADD, target=Target.HUMAN)


def test_step_requires_name():
    with pytest.raises(MethodModelError, match="non-empty"):
        Step(step_id=1, name="", kind=StepKind.ADD, target=Target.HUMAN)


def test_step_rejects_self_dependency():
    with pytest.raises(MethodModelError, match="cannot depend on itself"):
        Step(step_id=1, name="x", kind=StepKind.ADD, target=Target.HUMAN, depends_on=(1,))


def test_step_rejects_non_time_expected_duration():
    with pytest.raises(MethodModelError, match="time quantity"):
        Step(
            step_id=1,
            name="x",
            kind=StepKind.ADD,
            target=Target.HUMAN,
            expected_duration=Quantity(10.0, "mL"),
        )


def test_step_accepts_time_expected_duration():
    step = Step(step_id=1, name="x", kind=StepKind.ADD, target=Target.HUMAN, expected_duration=Quantity(10.0, "min"))
    assert step.expected_duration is not None


def test_method_requires_name():
    with pytest.raises(MethodModelError, match="non-empty"):
        Method(
            name="",
            version="1.0",
            target=Target.HUMAN,
            steps=(Step(step_id=1, name="x", kind=StepKind.ADD, target=Target.HUMAN),),
        )


def test_method_requires_at_least_one_step():
    with pytest.raises(MethodModelError, match="at least one step"):
        Method(name="Empty", version="1.0", target=Target.HUMAN, steps=())


def test_method_step_by_id_found_and_missing():
    step = Step(step_id=7, name="x", kind=StepKind.ADD, target=Target.HUMAN)
    method = Method(name="M", version="1.0", target=Target.HUMAN, steps=(step,))
    assert method.step_by_id(7) is step
    with pytest.raises(MethodModelError, match="no step with id"):
        method.step_by_id(99)
