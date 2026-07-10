"""A deterministic, seeded colony-trial harness -- statistical rigor for the convergence claim.

``tests/colony/test_colony_integration.py`` demonstrates the stigmergic
positive-feedback mechanism with one fixed, symmetric configuration
(identical agents, zero sensing noise): a single run is enough to show the
mechanism is *real*, but it is not enough to support a *rate* claim like
"the colony reaches consensus" as a general property of the mechanism
rather than an artifact of that one symmetric setup. This module adds the
missing layer: a **pure, reproducible** per-seed trial function that
injects the two sources of realistic variation the original test
deliberately held fixed --

1. **Heterogeneous per-agent preferences** -- each agent's preferred
   pheromone concentration (:class:`~template_formal.agent.agent.BeliefState`
   mean) is drawn independently, once per agent, in a fixed order, from
   ``random.Random(config.seed)``.
2. **Sensing noise** -- every candidate's predicted mean is
   ``field.sense(location) + rng.gauss(0, config.sensing_noise_std)``
   (or, when ``config.sensed_concentration_cap`` is set,
   ``min(field.sense(location), cap) + rng.gauss(...)`` -- the cap models a
   saturating sensor and is applied strictly *before* the noise term, so it
   never reduces measurement noise, only bounds the signal the noise is
   added to), drawn from the *same* seeded stream, advanced deterministically
   tick-by-tick and agent-by-agent (fixed iteration order), so a given
   ``config.seed`` always reproduces the exact same draw sequence and
   therefore the exact same ``choice_history``/``concentration_history`` --
   mirroring the reproducibility guarantee
   ``tests/network/test_bus.py::test_fault_injector_determinism_same_seed_same_sequence``
   already establishes for the fault injector's own seeded stream.

All stochasticity lives in this harness layer, drawn from a
``random.Random`` instance this module owns -- :meth:`~template_formal.agent.agent.Agent.decide`
itself is never touched or reseeded; its documented tie-break behavior
(the first candidate, in ``candidates`` order, achieving the minimum
expected free energy) is exactly the same one
``tests/colony/test_colony_integration.py`` already relies on and tests.

Real, on-disk SQLite files back every agent in every trial (per
``Out of Scope`` / ISC-66: no ``:memory:`` durability shortcut), created
under a per-trial subdirectory of the caller-supplied ``db_dir`` so that
many trials (e.g. the N=150 statistical-rigor suite in
``tests/colony/test_colony_convergence_statistics.py``) can safely share
one ``tmp_path`` without agent-file name collisions across seeds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from template_formal.agent.agent import Agent, BeliefState, CandidateAction
from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField
from template_formal.types.ids import new_agent_id
from template_formal.types.result import Err

_CANDIDATE_VARIANCE = 1.0
"""Fixed predicted-outcome variance for every sensed candidate (matches the
original ``tests/colony/test_colony_integration.py`` convention of holding
this term fixed so only the *mean* term carries the sensed/noisy signal)."""


@dataclass(frozen=True, slots=True)
class ColonyTrialConfig:
    """One fully-specified, seeded colony-trial configuration.

    Attributes:
        num_agents: How many real :class:`~template_formal.agent.agent.Agent`
            instances participate in this trial.
        locations: The candidate pheromone-field locations every agent
            chooses among each tick (must be non-empty).
        num_ticks: How many decision ticks to run.
        preference_mean_range: ``(low, high)`` bounds ``rng.uniform`` draws
            each agent's preferred concentration mean from.
        preference_variance: The fixed preference variance shared by every
            agent's :class:`~template_formal.agent.agent.BeliefState`
            preference (only the mean varies per agent).
        sensing_noise_std: Standard deviation of the zero-mean Gaussian
            noise added to every sensed candidate mean each tick.
        deposit_amount: Pheromone deposited at an agent's chosen location
            each tick (see :meth:`~template_formal.colony.pheromone.PheromoneField.deposit`).
        decay: Fraction evaporated from every location's concentration at
            the end of each tick (see
            :meth:`~template_formal.colony.pheromone.PheromoneField.evaporate`).
        seed: Seeds this trial's single ``random.Random`` stream -- the same
            seed always reproduces the exact same trial trace.
        sensed_concentration_cap: Optional saturating ceiling on a
            candidate's *sensed* concentration (``field.sense(location)``),
            applied *before* the sensing-noise term is added -- models a
            saturating/bounded sensor, not reduced measurement noise.
            ``None`` (the default) means unchanged behavior: every existing
            trial/test that does not set this field observes byte-for-byte
            the same trace it always has. When set, must be ``> 0.0`` (a
            cap of ``0.0`` or below would clip every candidate to the same
            floor regardless of location, destroying the sensor's ability
            to discriminate at all -- a degenerate configuration, not a
            legitimate "very tight cap"). See ``run_colony_trial`` for where
            the clip is applied, and ``manuscript/05_results_discussion.md``
            (Experiment A's ablation) for the falsifiable hypothesis this
            field exists to test.
    """

    num_agents: int
    locations: tuple[str, ...]
    num_ticks: int
    preference_mean_range: tuple[float, float]
    preference_variance: float
    sensing_noise_std: float
    deposit_amount: float
    decay: float
    seed: int
    sensed_concentration_cap: float | None = None

    def __post_init__(self) -> None:
        """Reject nonsensical numeric fields at construction time.

        Mirrors the ``__post_init__`` runtime-guard discipline already
        established in ``storage/schema.py`` (``Column``/``TableSchema``
        validating their SQL identifier at construction) and
        ``storage/transaction.py`` (isolation-level literal validation) --
        see ``## Decisions`` for why this closes the same gap for the
        remaining unvalidated numeric config surface. ``decay`` is
        documented above as "fraction evaporated ... at the end of each
        tick", so it must be a fraction in ``[0.0, 1.0]``; a value outside
        that range would silently pass to
        :meth:`~template_formal.colony.pheromone.PheromoneField.evaporate`
        every tick until *that* call finally raised deep inside the
        simulation loop, far from the actual misconfiguration.
        ``sensing_noise_std`` is a standard deviation fed to
        ``random.gauss`` and must be non-negative (``0.0`` is a legal,
        deterministic "no noise" parameter for ``gauss``). ``preference_variance``
        is fed directly into :class:`~template_formal.agent.agent.BeliefState`
        (at construction time, `~template_formal.colony.experiment.run_colony_trial`),
        which validates ``variance`` must be strictly ``> 0.0`` (a third-
        adversarial-pass fix, ISC-81) -- so this field is validated with the
        *same, stricter* bound here rather than a looser ``>= 0.0`` that
        would accept ``0.0`` and only fail one call later inside
        ``run_colony_trial``, deep in the trial loop rather than at config
        construction (a cross-vendor audit caught this exact
        guard-boundary mismatch; see ``## Decisions``).
        """
        if not (0.0 <= self.decay <= 1.0):
            raise ValueError(f"decay must be a fraction within [0.0, 1.0], got {self.decay}")
        if self.sensing_noise_std < 0.0:
            raise ValueError(f"sensing_noise_std must be non-negative, got {self.sensing_noise_std}")
        if self.preference_variance <= 0.0:
            raise ValueError(f"preference_variance must be > 0.0 (matches BeliefState), got {self.preference_variance}")
        if self.sensed_concentration_cap is not None and self.sensed_concentration_cap <= 0.0:
            raise ValueError(f"sensed_concentration_cap must be > 0.0 when set, got {self.sensed_concentration_cap}")


@dataclass(frozen=True, slots=True)
class ColonyTrialResult:
    """The full, reproducible trace of one :func:`run_colony_trial` call.

    Attributes:
        seed: The configuration's seed (carried through for convenience).
        choice_history: One tuple of chosen location names per tick, one
            entry per agent, in agent-construction order.
        concentration_history: One mapping of location -> sensed
            concentration per tick, snapshotted immediately after that
            tick's evaporation step.
        preference_means: Each agent's drawn preferred concentration mean,
            in agent-construction order (the heterogeneity this harness
            injects -- see module docstring).
        converged: Whether :func:`find_sustained_consensus_tick` found a
            sustained consensus tick in ``choice_history``.
        consensus_tick: The first tick index at which all agents agreed on
            one location *and stayed agreed on that same location* through
            the trial's last tick, or ``None`` if no such tick exists.
    """

    seed: int
    choice_history: tuple[tuple[str, ...], ...]
    concentration_history: tuple[Mapping[str, float], ...]
    preference_means: tuple[float, ...]
    converged: bool
    consensus_tick: int | None


def find_sustained_consensus_tick(choice_history: Sequence[Sequence[str]]) -> int | None:
    """The first tick where every agent agrees on one location, sustained to the end.

    "Sustained" means: not merely unanimous *at* that tick, but every
    subsequent tick in ``choice_history`` is also unanimous on that exact
    same location. A tick that is unanimous but later followed by
    disagreement (a false start) is deliberately skipped in favor of a
    later tick that genuinely holds through the end -- see
    ``tests/colony/test_colony_stats_unit.py`` for the hand-crafted
    fixture proving this (agreement-then-broken-then-resustained must
    return the *later* sustained index, not the earlier false start).

    Args:
        choice_history: One sequence of per-agent choice names per tick
            (``choice_history[tick][agent_index]``).

    Returns:
        The earliest sustained-consensus tick index, or ``None`` if no
        tick in ``choice_history`` starts a run of unanimous agreement on
        one location that lasts through the final tick (including the
        degenerate case of an empty ``choice_history``).
    """
    num_ticks = len(choice_history)
    for start in range(num_ticks):
        tick_choices = choice_history[start]
        if not tick_choices:
            continue
        candidate_winner = tick_choices[0]
        if any(choice != candidate_winner for choice in tick_choices):
            continue
        sustained = all(
            len(choice_history[later]) > 0 and all(choice == candidate_winner for choice in choice_history[later])
            for later in range(start, num_ticks)
        )
        if sustained:
            return start
    return None


def run_colony_trial(config: ColonyTrialConfig, db_dir: Path) -> ColonyTrialResult:
    """Run one real, seeded, reproducible colony trial and return its full trace.

    Every agent gets its own real, on-disk SQLite file (under a
    per-trial subdirectory of ``db_dir`` named by ``config.seed``) and one
    real :class:`~template_formal.colony.pheromone.InMemoryPheromoneField`
    is shared among them, exactly as in
    ``tests/colony/test_colony_integration.py`` -- the only difference is
    that preferences are heterogeneous (drawn per agent from
    ``config.seed``) and every sensed candidate mean carries seeded
    Gaussian noise, per the module docstring.

    Args:
        config: The trial configuration; ``config.seed`` seeds the single
            ``random.Random`` stream this entire trial draws from, in a
            fixed order (all agent preferences first, then noise draws
            tick-by-tick/agent-by-agent), so re-running with the same
            ``config`` always reproduces byte-for-byte the same
            ``choice_history``/``concentration_history``.
        db_dir: Parent directory for this trial's per-agent SQLite files
            (a real, on-disk directory -- typically a ``tmp_path`` in
            tests). Safe to reuse across many trials with distinct seeds:
            each trial gets its own ``db_dir / f"trial_{config.seed}"``
            subdirectory.

    Returns:
        The full :class:`ColonyTrialResult` trace.

    Raises:
        ValueError: If ``config.num_agents < 1``, ``config.locations`` is
            empty, or ``config.num_ticks < 1`` -- a malformed
            configuration is a programmer error, not an expected trial
            outcome.
    """
    if config.num_agents < 1:
        raise ValueError(f"num_agents must be >= 1, got {config.num_agents}")
    if not config.locations:
        raise ValueError("locations must be non-empty")
    if config.num_ticks < 1:
        raise ValueError(f"num_ticks must be >= 1, got {config.num_ticks}")

    rng = random.Random(config.seed)

    # Fixed order: draw every agent's preference mean first, before any
    # tick's noise draws -- this ordering is itself part of what "seed ->
    # exact trace" reproduces.
    preference_means = tuple(rng.uniform(*config.preference_mean_range) for _ in range(config.num_agents))

    trial_dir = db_dir / f"trial_{config.seed}"
    trial_dir.mkdir(parents=True, exist_ok=True)

    field: PheromoneField = InMemoryPheromoneField()
    agents: list[Agent[BeliefState]] = [
        Agent(
            new_agent_id(),
            trial_dir / f"agent_{index}.sqlite3",
            BeliefState(mean=preference_means[index], variance=config.preference_variance),
        )
        for index in range(config.num_agents)
    ]

    choice_history: list[tuple[str, ...]] = []
    concentration_history: list[Mapping[str, float]] = []

    try:
        for _tick in range(config.num_ticks):
            tick_choices: list[str] = []
            for agent in agents:
                candidates = [
                    CandidateAction(
                        name=location,
                        predicted_state=BeliefState(
                            mean=(
                                (
                                    field.sense(location)
                                    if config.sensed_concentration_cap is None
                                    else min(field.sense(location), config.sensed_concentration_cap)
                                )
                                + rng.gauss(0.0, config.sensing_noise_std)
                            ),
                            variance=_CANDIDATE_VARIANCE,
                        ),
                    )
                    for location in config.locations
                ]
                decision = agent.decide(candidates)
                if isinstance(decision, Err):
                    # Unreachable in practice: candidates is never empty
                    # because config.locations is validated non-empty
                    # above. Guarded explicitly rather than silently
                    # assumed, per this repo's never-raise-for-Result
                    # convention -- a genuine Err here is a harness bug.
                    raise RuntimeError(f"agent.decide unexpectedly failed on a non-empty candidate list: {decision}")
                chosen = decision.value
                recorded = agent.record_observation(chosen)
                if isinstance(recorded, Err):
                    raise RuntimeError(f"agent.record_observation unexpectedly failed: {recorded.error}")
                field.deposit(chosen.name, config.deposit_amount)
                tick_choices.append(chosen.name)
            field.evaporate(config.decay)
            choice_history.append(tuple(tick_choices))
            concentration_history.append({location: field.sense(location) for location in config.locations})
    finally:
        for agent in agents:
            agent.close()

    consensus_tick = find_sustained_consensus_tick(choice_history)
    return ColonyTrialResult(
        seed=config.seed,
        choice_history=tuple(choice_history),
        concentration_history=tuple(concentration_history),
        preference_means=preference_means,
        converged=consensus_tick is not None,
        consensus_tick=consensus_tick,
    )
