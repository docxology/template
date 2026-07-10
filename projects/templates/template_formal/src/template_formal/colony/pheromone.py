"""A typed shared "pheromone field" substrate, accessed only through a narrow ``Protocol``.

Per the ISA's ``Out of Scope``, the colony's coordination layer is
*documentary/typed-interface only* -- a typed shared substrate, not a full
consensus protocol implementation. :class:`PheromoneField` is that
interface: three methods (``deposit``, ``sense``, ``evaporate``), nothing
else. Agent code never receives a raw, shared, mutable ``dict`` -- it only
ever holds a reference typed as :class:`PheromoneField`, so mypy --strict
enforces that agent code can only interact with the substrate through this
narrow surface (ISC-32), regardless of which concrete class actually
backs it. :class:`InMemoryPheromoneField` is the reference in-process
implementation used by this template's colony integration test; a forking
project could substitute a different backend (e.g. one persisting to its
own SQLite file) without changing a line of agent code, precisely because
agent code is written against the ``Protocol``, not the concrete class.

This module makes no claim that structural (``Protocol``-based) typing
gives a runtime access-control guarantee -- Python's attribute access is
never actually restricted at runtime by a ``Protocol``; the narrowing is
edit-time/CI-time only, same as everywhere else in this template (see
``manuscript`` §"What mypy proves").
"""

from __future__ import annotations

from typing import Dict, Protocol


class PheromoneField(Protocol):
    """Narrow structural interface for the colony's shared stigmergic substrate.

    Any object implementing these three methods with these signatures
    satisfies this ``Protocol`` -- structurally, not by inheritance --
    which is exactly the interface :class:`~template_formal.agent.agent.Agent`
    and colony-level test/coordination code are written against.
    """

    def deposit(self, location: str, amount: float) -> None:
        """Increase the pheromone concentration at ``location`` by ``amount`` (``amount >= 0``)."""
        ...

    def sense(self, location: str) -> float:
        """Return the current pheromone concentration at ``location`` (``0.0`` if never deposited)."""
        ...

    def evaporate(self, decay: float) -> None:
        """Multiply every location's concentration by ``(1 - decay)``, ``decay`` in ``[0.0, 1.0]``."""
        ...


class InMemoryPheromoneField:
    """Reference in-process :class:`PheromoneField` implementation.

    Backed by a private ``dict[str, float]`` (``_concentrations``) that is
    never exposed as a public attribute or return value -- every read and
    write goes through ``sense``/``deposit``/``evaporate``. This is what
    ISC-32 means by "not a shared mutable dict exposed directly to agent
    code": the dict exists, but no agent-facing API ever hands out a
    reference to it.
    """

    __slots__ = ("_concentrations",)

    def __init__(self) -> None:
        self._concentrations: Dict[str, float] = {}

    def deposit(self, location: str, amount: float) -> None:
        if amount < 0.0:
            raise ValueError(f"pheromone deposit amount must be non-negative, got {amount}")
        self._concentrations[location] = self._concentrations.get(location, 0.0) + amount

    def sense(self, location: str) -> float:
        return self._concentrations.get(location, 0.0)

    def evaporate(self, decay: float) -> None:
        if not (0.0 <= decay <= 1.0):
            raise ValueError(f"decay must be within [0.0, 1.0], got {decay}")
        for location in list(self._concentrations):
            self._concentrations[location] *= 1.0 - decay
