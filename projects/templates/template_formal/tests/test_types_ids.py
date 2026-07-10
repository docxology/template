"""Behavioral tests for NewType identifier constructors (ISC-1)."""

from __future__ import annotations

from uuid import UUID

from template_formal.types.ids import new_agent_id, new_message_id, new_txn_id


def test_new_agent_id_is_a_real_uuid() -> None:
    agent_id = new_agent_id()
    assert isinstance(agent_id, UUID)


def test_ids_are_unique_across_calls() -> None:
    first = new_agent_id()
    second = new_agent_id()
    assert first != second


def test_message_and_txn_ids_are_distinct_values() -> None:
    message_id = new_message_id()
    txn_id = new_txn_id()
    assert isinstance(message_id, UUID)
    assert isinstance(txn_id, UUID)
    assert message_id != txn_id
