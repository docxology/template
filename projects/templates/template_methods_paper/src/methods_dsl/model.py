"""Method specification model: Parameter, Resource, Step, Method.

A ``.bpl``-style protocol block (``protocol PrepareLBMedia(...) { @step(1, ...)
add_reagent(...) ... }``) is, structurally, a name, a set of typed parameters,
a set of resources, and an ordered/dependent set of steps. This module encodes
that structure as frozen dataclasses instead of a parsed grammar — a
``Method`` is constructed directly in Python (see ``examples_methods.py``),
which keeps the DSL "controlled vocabulary in code" rather than "new text
syntax + parser", appropriate for a template exemplar's scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .units import Quantity
from .vocabulary import StepKind, Target


class MethodModelError(ValueError):
    """Raised when a model object is constructed with an invalid shape."""


@dataclass(frozen=True)
class Parameter:
    """A named, quantified input to a step or method."""

    name: str
    quantity: Quantity
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise MethodModelError("Parameter.name must be non-empty")


@dataclass(frozen=True)
class Resource:
    """A named physical or logical resource a method operates on.

    Generalizes BPL's ``reagent``/``labware`` declarations: anything a step
    reads from or writes to (a reagent, a container, a dataset, an
    instrument channel).
    """

    name: str
    kind: str
    capacity: Quantity | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise MethodModelError("Resource.name must be non-empty")
        if not self.kind:
            raise MethodModelError("Resource.kind must be non-empty")


@dataclass(frozen=True)
class Step:
    """One step in a method: an intent, its parameters, and its dependencies.

    ``depends_on`` holds the ``step_id`` values that must complete first —
    the explicit DAG edges the compiler's scheduler resolves
    (see ``compiler.compile_method``).
    """

    step_id: int
    name: str
    kind: StepKind
    target: Target
    parameters: tuple[Parameter, ...] = ()
    depends_on: tuple[int, ...] = ()
    expected_duration: Quantity | None = None

    def __post_init__(self) -> None:
        if self.step_id <= 0:
            raise MethodModelError(f"Step.step_id must be positive, got {self.step_id}")
        if not self.name:
            raise MethodModelError("Step.name must be non-empty")
        if self.step_id in self.depends_on:
            raise MethodModelError(f"step {self.step_id} cannot depend on itself")
        if self.expected_duration is not None and self.expected_duration.dimension.value != "time":
            raise MethodModelError(
                f"step {self.step_id} expected_duration must be a time quantity, "
                f"got unit {self.expected_duration.unit!r}"
            )


@dataclass(frozen=True)
class Method:
    """A complete, named method: parameters, resources, and an ordered step set."""

    name: str
    version: str
    target: Target
    steps: tuple[Step, ...]
    resources: tuple[Resource, ...] = field(default_factory=tuple)
    parameters: tuple[Parameter, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            raise MethodModelError("Method.name must be non-empty")
        if not self.steps:
            raise MethodModelError(f"method {self.name!r} must declare at least one step")

    def step_by_id(self, step_id: int) -> Step:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        raise MethodModelError(f"method {self.name!r} has no step with id {step_id}")
