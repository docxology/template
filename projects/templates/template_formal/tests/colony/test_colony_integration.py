"""N>=3 real Agent instances through a colony tick loop -- emergent convergence (ISC-33, ISC-34).

Three real agents, three real on-disk SQLite files, one shared
:class:`~template_formal.colony.pheromone.InMemoryPheromoneField`. Each
tick, every agent senses the current concentration at two candidate
locations, builds a fresh belief about each (predicted mean = sensed
concentration), and calls its own :meth:`Agent.decide` to pick the one
closer to a shared preference. Whichever location wins deposits more
pheromone there, which is sensed higher next tick -- a real positive
feedback (stigmergic) loop, not a scripted outcome: the coordinator below
(the test function itself) never picks a winner; it only ever reads real
per-agent decisions and a real shared field.

ISC-34 (anti): the coordinator loop holds references only to each
``Agent``'s public interface (``tick`` is not even used here -- the loop
builds candidates from the field and calls ``decide``/``record_observation``
directly) and to the ``PheromoneField`` Protocol object. It never holds
an ``Agent``'s internal ``Database``, ``sqlite3.Connection``, or protocol
``SessionEndpoint`` -- there is no way to reach those from this file, since
``Agent`` never exposes them (see ``tests/agent/test_agent_isolation.py``).
"""

from __future__ import annotations

from template_formal.agent.agent import Agent, BeliefState, CandidateAction
from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField
from template_formal.types.ids import new_agent_id
from template_formal.types.result import Ok

_LOCATIONS = ("north", "south")
_PREFERENCE = BeliefState(mean=10.0, variance=1.0)
_NUM_AGENTS = 3
_NUM_TICKS = 5
_DEPOSIT_AMOUNT = 1.0
_DECAY = 0.02


def _candidates_from_field(field: PheromoneField) -> list[CandidateAction[BeliefState]]:
    """Build this tick's candidates purely from the shared field's public Protocol surface."""
    return [
        CandidateAction(name=location, predicted_state=BeliefState(mean=field.sense(location), variance=1.0))
        for location in _LOCATIONS
    ]


def test_colony_of_three_real_agents_converges_on_one_location_via_real_stigmergy(tmp_path) -> None:  # type: ignore[no-untyped-def]
    field: PheromoneField = InMemoryPheromoneField()
    agents: list[Agent[BeliefState]] = [
        Agent(new_agent_id(), tmp_path / f"agent_{index}.sqlite3", _PREFERENCE) for index in range(_NUM_AGENTS)
    ]

    concentration_history: list[dict[str, float]] = []
    choice_history: list[list[str]] = []

    try:
        for _tick in range(_NUM_TICKS):
            tick_choices: list[str] = []
            for agent in agents:
                candidates = _candidates_from_field(field)
                decision = agent.decide(candidates)
                assert isinstance(decision, Ok)
                chosen = decision.value
                recorded = agent.record_observation(chosen)
                assert isinstance(recorded, Ok)
                field.deposit(chosen.name, _DEPOSIT_AMOUNT)
                tick_choices.append(chosen.name)
            field.evaporate(_DECAY)
            choice_history.append(tick_choices)
            concentration_history.append({location: field.sense(location) for location in _LOCATIONS})

        # Real per-agent state: every agent actually recorded one observation per tick.
        for agent in agents:
            assert agent.observation_count() == _NUM_TICKS

        # Emergent property #1: the colony reaches unanimous consensus on tick 0
        # (all three agents, sensing an identical empty field, independently
        # resolve the same free-energy tie to the same first-listed location --
        # nothing here hardcodes which location that is).
        winner = choice_history[0][0]
        assert all(choice == winner for choice in choice_history[0])

        # Emergent property #2: consensus persists every subsequent tick --
        # real collective behavior, not a one-off coincidence.
        for tick_choices in choice_history:
            assert all(choice == winner for choice in tick_choices)

        # Emergent property #3: the winning location's real, sensed pheromone
        # concentration strictly increases tick over tick (positive feedback),
        # computed from the actual field state after each real tick, not staged.
        winner_series = [concentrations[winner] for concentrations in concentration_history]
        for earlier, later in zip(winner_series, winner_series[1:]):
            assert later > earlier

        # Emergent property #4: the losing location never accumulates any
        # concentration at all, because it was never chosen by any real agent.
        loser = next(location for location in _LOCATIONS if location != winner)
        loser_series = [concentrations[loser] for concentrations in concentration_history]
        assert all(value == 0.0 for value in loser_series)

        # Emergent property #5: the winner's dominance share of total
        # concentration is non-decreasing across ticks (aggregate convergence).
        shares = [
            concentrations[winner] / (concentrations[winner] + concentrations[loser])
            if (concentrations[winner] + concentrations[loser]) > 0.0
            else 0.0
            for concentrations in concentration_history
        ]
        for earlier, later in zip(shares, shares[1:]):
            assert later >= earlier
        assert shares[-1] == 1.0
    finally:
        for agent in agents:
            agent.close()


def test_colony_coordinator_never_touches_an_agents_internal_storage_or_protocol_handle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ISC-34 (anti), made concrete: this test file's own coordinator loop above
    only ever calls public Agent methods (``decide``, ``record_observation``,
    ``observation_count``, ``close``) and the public PheromoneField Protocol
    methods. This test asserts those are, in fact, the entire public surface
    an agent exposes -- so the coordinator loop above could not have reached
    anything else even if it tried."""
    field: PheromoneField = InMemoryPheromoneField()
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "solo.sqlite3", _PREFERENCE)
    try:
        public_agent_members = {name for name in dir(agent) if not name.startswith("_")}
        assert public_agent_members == {
            "agent_id",
            "protocol_phase",
            "initiate_handshake",
            "decide",
            "record_observation",
            "tick",
            "observation_count",
            "close",
        }
        public_field_members = {name for name in dir(field) if not name.startswith("_")}
        assert public_field_members == {"deposit", "sense", "evaporate"}
    finally:
        agent.close()
