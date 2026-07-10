"""Behavioral tests for Agent's storage recording, tick loop, and protocol endpoint (ISC-27)."""

from __future__ import annotations

import sqlite3

import pytest

from template_formal.agent.agent import Agent, BeliefState, CandidateAction, expected_free_energy
from template_formal.protocol.session import WireMessage
from template_formal.types.ids import new_agent_id
from template_formal.types.result import Err, Ok

_PREFERENCE = BeliefState(mean=0.0, variance=1.0)


def test_record_observation_persists_a_real_row_via_select(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "agent.sqlite3"
    agent: Agent[BeliefState] = Agent(new_agent_id(), db_path, _PREFERENCE)
    candidate = CandidateAction(name="forage_north", predicted_state=BeliefState(mean=0.0, variance=1.0))

    assert agent.observation_count() == 0
    recorded = agent.record_observation(candidate)
    assert isinstance(recorded, Ok)
    assert agent.observation_count() == 1

    # Independently verify via a real SELECT against the same on-disk file.
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT key, value FROM observations").fetchall()
    connection.close()
    assert len(rows) == 1
    assert rows[0]["key"] == "forage_north"
    expected_score = expected_free_energy(candidate.predicted_state, _PREFERENCE)
    assert abs(rows[0]["value"] - expected_score) < 1e-9

    agent.close()


def test_tick_decides_and_records_in_one_call(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent.sqlite3", _PREFERENCE)
    candidates = [
        CandidateAction(name="near_preference", predicted_state=BeliefState(mean=0.1, variance=1.0)),
        CandidateAction(name="far_from_preference", predicted_state=BeliefState(mean=5.0, variance=1.0)),
    ]

    result = agent.tick(candidates)
    assert isinstance(result, Ok)
    assert result.value.name == "near_preference"
    assert agent.observation_count() == 1

    # A second tick records a second, independent row.
    second_result = agent.tick(candidates)
    assert isinstance(second_result, Ok)
    assert agent.observation_count() == 2

    agent.close()


def test_tick_over_empty_candidates_propagates_decision_error_without_recording(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent.sqlite3", _PREFERENCE)

    result = agent.tick([])

    assert isinstance(result, Err)
    assert agent.observation_count() == 0
    agent.close()


def test_agent_owns_exactly_one_protocol_endpoint_starting_idle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent.sqlite3", _PREFERENCE)
    assert agent.protocol_phase == "IdleSession"

    peer_id = new_agent_id()
    hello = agent.initiate_handshake(peer_id)

    assert isinstance(hello, WireMessage)
    assert hello.kind == "hello"
    assert agent.protocol_phase == "HandshakingSession"

    agent.close()


def test_initiating_a_second_handshake_on_the_same_agent_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent.sqlite3", _PREFERENCE)
    peer_id = new_agent_id()
    agent.initiate_handshake(peer_id)

    with pytest.raises(RuntimeError):
        agent.initiate_handshake(peer_id)

    agent.close()


def test_agent_id_property_returns_the_constructed_identity(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent_id = new_agent_id()
    agent: Agent[BeliefState] = Agent(agent_id, tmp_path / "agent.sqlite3", _PREFERENCE)
    assert agent.agent_id == agent_id
    agent.close()
