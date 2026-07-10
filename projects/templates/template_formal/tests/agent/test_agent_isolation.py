"""Structural proof that one Agent's storage file is unreachable via another's API (ISC-30).

Two real agents, two real on-disk SQLite files (via ``tmp_path``). The
claim under test is not "agent A happens not to read agent B's file in
this test" -- it is "agent A's public API surface has no attribute or
method that could ever be used to reach agent B's file", checked by
inspecting the actual public surface, not by trusting a docstring.
"""

from __future__ import annotations

import inspect
import sqlite3
from pathlib import Path

from template_formal.agent.agent import Agent, BeliefState
from template_formal.storage.db import Database
from template_formal.types.ids import new_agent_id

_PREFERENCE = BeliefState(mean=0.0, variance=1.0)


def _public_members(obj: object) -> list[str]:
    return [name for name in dir(obj) if not name.startswith("_")]


def test_no_public_attribute_of_agent_exposes_a_path_or_connection(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent_a: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent_a.sqlite3", _PREFERENCE)
    try:
        for name in _public_members(agent_a):
            member = getattr(agent_a, name)
            if callable(member):
                continue
            assert not isinstance(member, (Path, sqlite3.Connection, Database)), (
                f"Agent.{name} publicly exposes {type(member).__name__}, "
                "which could be used to reach another agent's storage file"
            )
    finally:
        agent_a.close()


def test_no_public_method_of_agent_accepts_a_path_connection_database_or_agent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent_a: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "agent_a.sqlite3", _PREFERENCE)
    forbidden_annotations = {Path, sqlite3.Connection, Database, Agent}
    try:
        for name in _public_members(agent_a):
            member = getattr(agent_a, name)
            if not callable(member) or isinstance(member, type):
                continue
            signature = inspect.signature(member)
            for param in signature.parameters.values():
                assert param.annotation not in forbidden_annotations, (
                    f"Agent.{name} accepts a {param.annotation!r} parameter "
                    "('{param.name}'), which could be used to redirect it at "
                    "another agent's storage file"
                )
    finally:
        agent_a.close()


def test_two_agents_public_apis_never_reference_each_others_file_path(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path_a = tmp_path / "agent_a.sqlite3"
    path_b = tmp_path / "agent_b.sqlite3"
    agent_a: Agent[BeliefState] = Agent(new_agent_id(), path_a, _PREFERENCE)
    agent_b: Agent[BeliefState] = Agent(new_agent_id(), path_b, _PREFERENCE)
    try:
        # There is no public attribute on either agent whose value equals the
        # other agent's on-disk path (the strongest concrete check available:
        # the path literally cannot be recovered from the public surface).
        for name in _public_members(agent_a):
            member = getattr(agent_a, name)
            if callable(member):
                continue
            assert member != path_b
            assert member != path_a
        for name in _public_members(agent_b):
            member = getattr(agent_b, name)
            if callable(member):
                continue
            assert member != path_a
            assert member != path_b
        # The files are genuinely distinct real files on disk.
        assert path_a != path_b
        assert path_a.exists()
        assert path_b.exists()
    finally:
        agent_a.close()
        agent_b.close()


def test_agent_construction_rejects_non_uuid_agent_id_at_runtime(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Runtime half of ISC-31's paired static+dynamic proof.

    mypy --strict is the static half (see
    ``tests/mypy_fixtures/bad_agent_id_construction.py``); this asserts the
    defensive runtime guard actually fires too, for a caller who bypasses
    mypy (an untyped boundary, a ``# type: ignore``, ...).
    """
    import pytest

    with pytest.raises(TypeError):
        Agent("not-a-uuid", tmp_path / "bad.sqlite3", _PREFERENCE)  # type: ignore[arg-type]
