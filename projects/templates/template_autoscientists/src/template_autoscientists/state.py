"""Shared-state records for the AutoScientists coordination model.

These dataclasses are the deterministic core of the exemplar: the champion
``p*``, the experiment log ``L``, and the structured proposal/outcome records
that agents read and write. They mirror the shared state described in
Gao, Fang & Zitnik, *AutoScientists* (arXiv:2605.28655), but contain no agent
or language-model logic so they can be tested deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Proposal:
    """One proposed experiment: perturb ``axis`` by ``step`` (signed)."""

    axis: int
    step: float
    rationale: str
    proposer: str

    @property
    def direction(self) -> str:
        """Sign label used as the dead-end registry key."""
        return "increase" if self.step >= 0 else "decrease"


@dataclass(frozen=True)
class ExperimentOutcome:
    """Result of evaluating a proposal against the objective."""

    proposal: Proposal
    params: tuple[float, ...]
    metric: float
    delta_vs_champion: float
    seed: int
    confirmed: bool

    @property
    def improved(self) -> bool:
        """True when the (confirmed) metric beat the incumbent champion."""
        return self.confirmed and self.delta_vs_champion > 0.0


@dataclass(frozen=True)
class Champion:
    """Current best program ``p*`` with enough state to reproduce it."""

    params: tuple[float, ...]
    metric: float
    experiment_index: int


@dataclass
class SharedState:
    """Mutable shared state read and written by every agent each cycle.

    Holds the immutable champion record plus the append-only experiment log.
    The dead-end registry and stagnation detector live in their own modules so
    each mechanism can be tested and ablated independently.
    """

    champion: Champion
    log: list[ExperimentOutcome] = field(default_factory=list)

    def record(self, outcome: ExperimentOutcome) -> None:
        """Append an outcome and promote the champion when it improves."""
        self.log.append(outcome)
        if outcome.improved:
            self.champion = Champion(
                params=outcome.params,
                metric=outcome.metric,
                experiment_index=len(self.log) - 1,
            )

    def best_so_far(self) -> float:
        """Champion metric — the value plotted against experiment count."""
        return self.champion.metric

    def with_champion(self, champion: Champion) -> SharedState:
        """Return a copy seeded from a different champion (fresh log).

        A public convenience for callers that want to re-seed a search from a
        fixed champion (e.g. warm-starting a fresh run from a known-good point)
        without mutating the original state. The coordination loop does not use
        it — it is provided as an intentional extension point, not dead code.
        """
        return replace(self, champion=champion, log=[])
