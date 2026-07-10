"""Known-good fixture: ``InMemoryPheromoneField``'s structural conformance to
``PheromoneField`` type-checks cleanly (ISC-32).

`mypy --strict` MUST accept this file (exit 0). It exists as a
positive-control regression guard: `src/` itself never assigns an
`InMemoryPheromoneField()` instance to a `PheromoneField`-typed variable --
every real assignment of that shape lives in `tests/colony/test_pheromone.py`
and `tests/colony/test_colony_integration.py`, neither of which
`tests/test_mypy_oracle.py` type-checks. A `src/`-only mypy gate is
therefore structurally blind to a broken structural conformance between
`InMemoryPheromoneField` and the `PheromoneField` Protocol it claims to
satisfy (mirrors the `Agent[BeliefState]` blind spot documented in
ISA.md's Changelog, found by Forge's cross-vendor audit). See
`bad_pheromone_protocol_violation.py` for the paired negative control that
proves mypy actually rejects a broken conformance of this same shape.
"""

from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField


def build_and_exercise_field() -> float:
    field: PheromoneField = InMemoryPheromoneField()
    field.deposit("nest", 1.0)
    field.deposit("nest", 0.5)
    field.evaporate(0.1)
    return field.sense("nest")
