"""Deterministic compilation: Method -> Plan.

Mirrors BPL's compiler pipeline (Parse -> Semantic Check -> Lower -> Schedule
-> Execute -> Export) and its design principle #5: "Same source + same
options -> same plan hash. Non-deterministic metadata (timestamps, UUIDs) is
isolated." :func:`compile_method` runs every gate in
:func:`~src.methods_dsl.validation.run_all_gates`, schedules steps with a
deterministic topological sort (Kahn's algorithm, ties broken by ascending
``step_id``), and hashes the resulting plan with a canonical JSON encoding so
the hash is reproducible across processes and platforms.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from ._logging import get_logger
from .model import Method, Step
from .validation import GateResult, run_all_gates

logger = get_logger(__name__)


class CycleError(ValueError):
    """Raised by :func:`topological_order` when the step-dependency graph has a cycle."""


class MethodValidationError(ValueError):
    """Raised by :func:`compile_method` when any validation gate fails."""

    def __init__(self, method_name: str, gate_results: tuple[GateResult, ...]) -> None:
        failed = [g for g in gate_results if not g.passed]
        detail = "; ".join(f"{g.name}: {', '.join(g.issues)}" for g in failed)
        super().__init__(f"method {method_name!r} failed validation: {detail}")
        self.method_name = method_name
        self.gate_results = gate_results


def topological_order(method: Method) -> tuple[Step, ...]:
    """Return *method*'s steps in a deterministic dependency-respecting order.

    Kahn's algorithm: repeatedly remove a step whose dependencies are all
    already scheduled, breaking ties by ascending ``step_id`` so the same
    method always yields the same order (no reliance on dict/set iteration
    order, which Python does not guarantee to be stable across versions for
    this purpose).

    Raises:
        CycleError: If the dependency graph is not acyclic.
    """
    steps_by_id = {step.step_id: step for step in method.steps}
    remaining_deps = {step.step_id: set(step.depends_on) for step in method.steps}
    scheduled: list[Step] = []
    scheduled_ids: set[int] = set()

    while len(scheduled) < len(method.steps):
        ready = sorted(
            step_id
            for step_id, deps in remaining_deps.items()
            if step_id not in scheduled_ids and deps <= scheduled_ids
        )
        if not ready:
            unscheduled = sorted(set(steps_by_id) - scheduled_ids)
            raise CycleError(f"method {method.name!r} has a cyclic dependency among steps {unscheduled}")
        next_id = ready[0]
        scheduled.append(steps_by_id[next_id])
        scheduled_ids.add(next_id)

    return tuple(scheduled)


@dataclass(frozen=True)
class PlanStep:
    """One scheduled step in a compiled :class:`Plan`."""

    step_id: int
    name: str
    kind: str
    target: str
    order: int


@dataclass(frozen=True)
class Plan:
    """A deterministically compiled, scheduled execution plan."""

    method_name: str
    method_version: str
    target: str
    steps: tuple[PlanStep, ...]
    plan_hash: str

    def to_canonical_dict(self) -> dict[str, object]:
        """Canonical (sorted-key, hash-input-equivalent) dict representation."""
        return {
            "method_name": self.method_name,
            "method_version": self.method_version,
            "target": self.target,
            "steps": [
                {"step_id": s.step_id, "name": s.name, "kind": s.kind, "target": s.target, "order": s.order}
                for s in self.steps
            ],
        }


def _compute_plan_hash(method_name: str, method_version: str, target: str, ordered_steps: tuple[Step, ...]) -> str:
    payload = {
        "method_name": method_name,
        "method_version": method_version,
        "target": target,
        "steps": [
            {
                "step_id": step.step_id,
                "name": step.name,
                "kind": step.kind.value,
                "target": step.target.value,
                "order": order,
            }
            for order, step in enumerate(ordered_steps)
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compile_method(method: Method) -> Plan:
    """Validate and deterministically compile *method* into a :class:`Plan`.

    Raises:
        MethodValidationError: If any gate in
            :func:`~src.methods_dsl.validation.run_all_gates` fails.
    """
    gate_results = run_all_gates(method)
    if not all(gate.passed for gate in gate_results):
        logger.warning(
            "method %r failed validation (%d/%d gates passed)",
            method.name,
            sum(g.passed for g in gate_results),
            len(gate_results),
        )
        raise MethodValidationError(method.name, gate_results)

    ordered = topological_order(method)
    plan_hash = _compute_plan_hash(method.name, method.version, method.target.value, ordered)
    plan_steps = tuple(
        PlanStep(step_id=step.step_id, name=step.name, kind=step.kind.value, target=step.target.value, order=order)
        for order, step in enumerate(ordered)
    )
    logger.info(
        "compiled method %r v%s -> plan %s (%d steps)", method.name, method.version, plan_hash[:12], len(plan_steps)
    )
    return Plan(
        method_name=method.name,
        method_version=method.version,
        target=method.target.value,
        steps=plan_steps,
        plan_hash=plan_hash,
    )
