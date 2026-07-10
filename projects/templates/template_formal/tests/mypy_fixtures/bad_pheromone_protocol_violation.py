"""Known-bad fixture: a broken ``PheromoneField`` conformance (ISC-32).

`mypy --strict` MUST reject this file. ``_BrokenPheromoneField`` declares an
extra *required* parameter (``note``, no default) on ``deposit`` beyond the
``PheromoneField`` Protocol's ``deposit(self, location: str, amount: float)
-> None`` signature -- a caller holding a ``PheromoneField``-typed reference
can only ever supply ``location``/``amount``, so an implementation that
*requires* a third argument cannot actually satisfy calls made through the
narrow interface, and mypy --strict correctly refuses the assignment on
structural-subtyping grounds. Never imported or executed -- only
type-checked in isolation by ``tests/test_mypy_oracle.py``. Paired positive
control: ``good_pheromone_conformance.py``.
"""

from template_formal.colony.pheromone import PheromoneField


class _BrokenPheromoneField:
    """Structurally almost-conforms, but ``deposit`` requires an extra arg."""

    def deposit(self, location: str, amount: float, note: str) -> None:
        pass

    def sense(self, location: str) -> float:
        return 0.0

    def evaporate(self, decay: float) -> None:
        pass


def bad_usage() -> None:
    # error: Incompatible types in assignment (expression has type "_BrokenPheromoneField", variable has type "PheromoneField")
    field: PheromoneField = _BrokenPheromoneField()
    field.deposit("nest", 1.0)
