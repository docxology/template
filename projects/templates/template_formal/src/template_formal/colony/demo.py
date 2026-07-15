"""Real, on-disk colony simulation runners (moved out of ``scripts/`` per the
repo's thin-orchestrator rule: anything beyond real-path wiring, printing,
and JSON I/O is business logic and belongs in ``src/``).

Two independent kinds of run:

- :func:`run_demo_colony` -- three identical agents, five ticks, no seeded
  variation. This is the "guaranteed by construction" mechanism
  demonstration @sec:results-discussion scopes honestly as "not emergence."
- :func:`run_statistics_sweep` -- a real, seeded batch of heterogeneous
  colony trials via :func:`template_formal.colony.experiment.run_colony_trial`,
  the same harness ``tests/colony/test_colony_convergence_statistics.py``
  uses at a larger N for the statistical-rigor claim.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from template_formal.agent.agent import Agent, BeliefState, CandidateAction
from template_formal.colony.experiment import ColonyTrialConfig, ColonyTrialResult, run_colony_trial
from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField
from template_formal.types.ids import new_agent_id
from template_formal.types.result import Ok

LOCATIONS = ("north", "south")
DEMO_PREFERENCE = BeliefState(mean=10.0, variance=1.0)
DEMO_NUM_AGENTS = 3
DEMO_NUM_TICKS = 5
DEMO_DEPOSIT_AMOUNT = 1.0
DEMO_DECAY = 0.02


class DemoSummary(TypedDict):
    """JSON-serializable result of the deterministic demonstration run."""

    num_agents: int
    num_ticks: int
    choice_history: list[list[str]]
    concentration_history: list[dict[str, float]]
    observation_counts: dict[str, int]
    agent_db_paths: list[str]


def _candidates_from_field(field: PheromoneField) -> list[CandidateAction[BeliefState]]:
    """Build one tick's candidates purely from the shared field's public Protocol surface."""
    return [
        CandidateAction(name=location, predicted_state=BeliefState(mean=field.sense(location), variance=1.0))
        for location in LOCATIONS
    ]


def run_demo_colony(output_dir: Path) -> DemoSummary:
    """Run a small, real, on-disk colony simulation and return a summary payload.

    Each :class:`Agent` opens its own real SQLite file under ``output_dir``
    (never ``:memory:``, per ISC-66) and records one real observation per
    tick to that file alone -- the coordinator loop below only ever calls
    each agent's public methods and the shared field's public ``Protocol``
    methods (ISC-34).
    """
    field: PheromoneField = InMemoryPheromoneField()
    agents: list[Agent[BeliefState]] = [
        Agent(new_agent_id(), output_dir / f"agent_{index}.sqlite3", DEMO_PREFERENCE)
        for index in range(DEMO_NUM_AGENTS)
    ]

    choice_history: list[list[str]] = []
    concentration_history: list[dict[str, float]] = []
    try:
        for _tick in range(DEMO_NUM_TICKS):
            tick_choices: list[str] = []
            for agent in agents:
                candidates = _candidates_from_field(field)
                decision = agent.decide(candidates)
                assert isinstance(decision, Ok)
                chosen = decision.value
                recorded = agent.record_observation(chosen)
                assert isinstance(recorded, Ok)
                field.deposit(chosen.name, DEMO_DEPOSIT_AMOUNT)
                tick_choices.append(chosen.name)
            field.evaporate(DEMO_DECAY)
            choice_history.append(tick_choices)
            concentration_history.append({location: field.sense(location) for location in LOCATIONS})

        return {
            "num_agents": DEMO_NUM_AGENTS,
            "num_ticks": DEMO_NUM_TICKS,
            "choice_history": choice_history,
            "concentration_history": concentration_history,
            "observation_counts": {str(agent.agent_id): agent.observation_count() for agent in agents},
            "agent_db_paths": [str(output_dir / f"agent_{index}.sqlite3") for index in range(DEMO_NUM_AGENTS)],
        }
    finally:
        for agent in agents:
            agent.close()


def run_statistics_sweep(
    db_dir: Path, *, num_trials: int, seed_base: int, config_kwargs: dict[str, object]
) -> list[ColonyTrialResult]:
    """Run a modest, real, seeded batch of heterogeneous colony trials.

    Thin wrapper around :func:`template_formal.colony.experiment.run_colony_trial`
    -- all randomness, agent construction, and per-trial SQLite files are the
    real harness's responsibility, not the caller's (ISC-66: every trial's
    agents still get real on-disk files, never ``:memory:``).
    """
    return [
        run_colony_trial(
            ColonyTrialConfig.from_mapping(seed=seed_base + i, values=config_kwargs),
            db_dir,
        )
        for i in range(num_trials)
    ]
