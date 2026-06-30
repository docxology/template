"""Staged validation gates for a :class:`~src.methods_dsl.model.Method`.

BPL's design (https://gitlab.com/bota-biosciences-public/bpl-code) runs six
staged gates before execution: syntax, semantic, plan/DAG, experiment-
parameter, capability, and backend preflight. This DSL constructs methods
directly as Python objects rather than parsing ``.bpl`` source, so the
syntax gate collapses into Python's own construction-time checks
(``model.py``'s ``__post_init__`` validators). The remaining four gates this
module implements are genuine, independently testable analogues of BPL's
semantic, plan, and backend-preflight gates:

1. :func:`structural_gate` — step-id uniqueness and dependency resolvability
   (BPL's plan/DAG gate's prerequisite).
2. :func:`semantic_gate` — every unit used resolves to a known dimension
   (BPL's semantic gate: "the type system catches mL + g at compile time").
3. :func:`plan_gate` — the dependency graph is acyclic (BPL's plan/DAG gate).
4. :func:`target_gate` — every step's execution target is compatible with
   the method's target and its step kind (BPL's backend-preflight gate).

:func:`run_all_gates` runs them in this fixed order and is the only
function the compiler calls — gates never run out of order.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Method
from .units import DimensionError
from .vocabulary import Target, target_accepts

_ALLOWED_STEP_TARGETS: dict[Target, frozenset[Target]] = {
    Target.HUMAN: frozenset({Target.HUMAN}),
    Target.AUTOMATED: frozenset({Target.AUTOMATED, Target.HUMAN}),
    Target.SIMULATION: frozenset({Target.SIMULATION}),
}


@dataclass(frozen=True)
class GateResult:
    """Outcome of one validation gate: pass/fail plus the issues found."""

    name: str
    passed: bool
    issues: tuple[str, ...] = ()


def structural_gate(method: Method) -> GateResult:
    """Check step-id uniqueness and that every dependency resolves."""
    issues: list[str] = []
    seen: set[int] = set()
    for step in method.steps:
        if step.step_id in seen:
            issues.append(f"duplicate step_id {step.step_id}")
        seen.add(step.step_id)
    known_ids = {step.step_id for step in method.steps}
    for step in method.steps:
        for dep in step.depends_on:
            if dep not in known_ids:
                issues.append(f"step {step.step_id} depends_on unknown step_id {dep}")
    return GateResult("structural", passed=not issues, issues=tuple(issues))


def semantic_gate(method: Method) -> GateResult:
    """Check every :class:`~src.methods_dsl.units.Quantity` resolves to a known dimension."""
    issues: list[str] = []

    def _check(label: str, quantity: object) -> None:
        if quantity is None:
            return
        try:
            quantity.dimension  # type: ignore[attr-defined]  # noqa: B018 - property access triggers validation
        except DimensionError as exc:
            issues.append(f"{label}: {exc}")

    for resource in method.resources:
        _check(f"resource {resource.name!r} capacity", resource.capacity)
    for parameter in method.parameters:
        _check(f"method parameter {parameter.name!r}", parameter.quantity)
    for step in method.steps:
        _check(f"step {step.step_id} expected_duration", step.expected_duration)
        for parameter in step.parameters:
            _check(f"step {step.step_id} parameter {parameter.name!r}", parameter.quantity)
    return GateResult("semantic", passed=not issues, issues=tuple(issues))


def plan_gate(method: Method) -> GateResult:
    """Check the step-dependency graph is acyclic (a valid DAG)."""
    from .compiler import CycleError, topological_order  # local import avoids a cycle with compiler.py

    try:
        topological_order(method)
    except CycleError as exc:
        return GateResult("plan", passed=False, issues=(str(exc),))
    return GateResult("plan", passed=True, issues=())


def target_gate(method: Method) -> GateResult:
    """Check every step's target is compatible with the method's target and kind."""
    issues: list[str] = []
    allowed = _ALLOWED_STEP_TARGETS[method.target]
    for step in method.steps:
        if step.target not in allowed:
            issues.append(
                f"step {step.step_id} target {step.target.value!r} is not compatible with "
                f"method target {method.target.value!r}"
            )
        if not target_accepts(step.target, step.kind):
            issues.append(f"step {step.step_id} kind {step.kind.value!r} cannot run on target {step.target.value!r}")
    return GateResult("target", passed=not issues, issues=tuple(issues))


def run_all_gates(method: Method) -> tuple[GateResult, ...]:
    """Run all four gates in the fixed order: structural, semantic, plan, target.

    Stops after ``structural_gate`` and ``semantic_gate`` if either fails,
    since ``plan_gate`` and ``target_gate`` assume a structurally and
    semantically valid method (mirrors BPL's staged short-circuit: a syntax
    failure never reaches the plan gate).
    """
    structural = structural_gate(method)
    semantic = semantic_gate(method)
    if not (structural.passed and semantic.passed):
        return (structural, semantic)
    return (structural, semantic, plan_gate(method), target_gate(method))
