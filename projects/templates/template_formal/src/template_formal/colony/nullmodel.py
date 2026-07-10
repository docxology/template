"""A random-choice null-model baseline for the colony convergence claim.

``tests/colony/test_colony_convergence_statistics.py`` establishes that the
real stigmergic mechanism (``colony/experiment.py``'s ``run_colony_trial``)
converges at a real, Wilson-bounded rate under heterogeneity and sensing
noise. That number is meaningless as evidence *for the mechanism* unless it
is compared against a baseline that has no mechanism at all -- a colony of
agents that pick a location uniformly at random every tick, completely
ignorant of the pheromone field, of each other's choices, and of any
preference. If the null model converges nearly as often as the real
mechanism, the real mechanism is not actually doing anything a coin flip
would not also do; if it converges far less often, the real mechanism's
higher rate is evidence of a real effect, not an artifact of how
"convergence" happens to be defined.

This module is deliberately minimal and structurally isolated from the rest
of the colony machinery: :func:`run_null_model_trial` never imports or
references the shared stigmergic substrate type, the per-agent free-energy
decision-loop class, or its belief-state type (see
``colony/pheromone.py``/``agent/agent.py`` for those) -- there is no shared
substrate to read, no free-energy computation, and no per-agent SQLite
file. Each agent's choice each tick is exactly
``random.Random(seed).choice(locations)``, nothing else. This is proven,
not merely claimed, by
``tests/colony/test_nullmodel.py::test_nullmodel_module_never_references_pheromone_field_or_agent_machinery``,
which reads this module's own source text and asserts the literal absence
of those symbol names -- a grep-verifiable structural guarantee, not a
docstring promise.

The only piece of machinery this module *does* reuse is
:func:`~template_formal.colony.experiment.find_sustained_consensus_tick` --
the same "first tick where every agent agrees on one location, sustained to
the end" definition the real-mechanism harness uses -- so a rate comparison
between the two harnesses is a genuine apples-to-apples comparison of
*convergence under the identical definition*, not two different notions of
"converged" being compared as if they were the same thing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from template_formal.colony.experiment import find_sustained_consensus_tick


@dataclass(frozen=True, slots=True)
class NullModelTrialConfig:
    """One fully-specified, seeded null-model trial configuration.

    Deliberately has no ``preference_mean_range``, ``preference_variance``,
    ``sensing_noise_std``, ``deposit_amount``, or ``decay`` field -- the
    null model has no preferences, no sensing, no pheromone deposits, and
    no evaporation, because it has no pheromone field at all.

    Attributes:
        num_agents: How many independent random choosers participate.
        locations: The candidate locations every agent chooses among each
            tick, uniformly at random (must be non-empty).
        num_ticks: How many choice ticks to run.
        seed: Seeds this trial's single ``random.Random`` stream -- the
            same seed always reproduces the exact same
            ``choice_history``.
    """

    num_agents: int
    locations: tuple[str, ...]
    num_ticks: int
    seed: int

    def __post_init__(self) -> None:
        """Reject malformed configurations at construction time.

        Mirrors ``ColonyTrialConfig.__post_init__``'s discipline
        (``colony/experiment.py``) for the fields the two configs share.
        """
        if self.num_agents < 1:
            raise ValueError(f"num_agents must be >= 1, got {self.num_agents}")
        if not self.locations:
            raise ValueError("locations must be non-empty")
        if self.num_ticks < 1:
            raise ValueError(f"num_ticks must be >= 1, got {self.num_ticks}")


@dataclass(frozen=True, slots=True)
class NullModelTrialResult:
    """The full, reproducible trace of one :func:`run_null_model_trial` call.

    Attributes:
        seed: The configuration's seed (carried through for convenience).
        choice_history: One tuple of chosen location names per tick, one
            entry per agent, in agent-index order.
        converged: Whether :func:`~template_formal.colony.experiment.find_sustained_consensus_tick`
            found a sustained consensus tick in ``choice_history``.
        consensus_tick: The first tick index at which all agents' random
            choices happened to agree on one location *and stayed agreed*
            through the trial's last tick, or ``None`` if no such tick
            exists.
    """

    seed: int
    choice_history: tuple[tuple[str, ...], ...]
    converged: bool
    consensus_tick: int | None


def run_null_model_trial(config: NullModelTrialConfig) -> NullModelTrialResult:
    """Run one real, seeded, reproducible null-model trial and return its full trace.

    Each agent's choice each tick is ``rng.choice(config.locations)`` --
    drawn from a single ``random.Random(config.seed)`` stream, advanced
    deterministically tick-by-tick and agent-by-agent (fixed iteration
    order), so a given ``config.seed`` always reproduces the exact same
    ``choice_history``. There is no pheromone field, no belief state, no
    free-energy computation, and no SQLite file anywhere in this function --
    the null model's only source of behavior is the RNG.

    Args:
        config: The trial configuration; ``config.seed`` seeds the single
            ``random.Random`` stream this entire trial draws from.

    Returns:
        The full :class:`NullModelTrialResult` trace.
    """
    rng = random.Random(config.seed)
    locations: Sequence[str] = config.locations

    choice_history: list[tuple[str, ...]] = []
    for _tick in range(config.num_ticks):
        tick_choices = tuple(rng.choice(locations) for _ in range(config.num_agents))
        choice_history.append(tick_choices)

    consensus_tick = find_sustained_consensus_tick(choice_history)
    return NullModelTrialResult(
        seed=config.seed,
        choice_history=tuple(choice_history),
        converged=consensus_tick is not None,
        consensus_tick=consensus_tick,
    )
