"""Behavioral tests for the in-process fault-injectable message bus.

Covers ISC-20 (typed bus, no sockets), ISC-21 (independently toggleable
drop/duplicate/corrupt/reorder), ISC-22 (seeded determinism), and ISC-68
(anti: fault modes must be shown to actually fire, not merely exist
disabled-by-default).
"""

from __future__ import annotations

import pytest

from template_formal.network.bus import FaultConfig, FaultInjector, InProcessBus, UnknownEndpointError
from template_formal.protocol.session import WireMessage, decode_wire_message, encode_wire_message
from template_formal.types.ids import AgentId, new_agent_id, new_message_id
from template_formal.types.result import Err, Ok


def _sample_message(sender: AgentId, payload: bytes = b"hello-bytes") -> WireMessage:
    return WireMessage(msg_id=new_message_id(), sender=sender, kind="data", payload=payload)


def _new_bus(fault_config: FaultConfig | None = None) -> InProcessBus[WireMessage]:
    return InProcessBus(encode=encode_wire_message, decode=decode_wire_message, fault_config=fault_config)


def test_bus_send_and_recv_round_trip_with_no_faults() -> None:
    bus = _new_bus()
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    message = _sample_message(sender_id)
    bus.send(recipient_id, message)
    bus.flush()

    received = bus.try_recv(recipient_id)
    assert isinstance(received, Ok)
    assert received.value.payload == b"hello-bytes"
    assert received.value.sender == sender_id


def test_bus_recv_on_empty_inbox_returns_none() -> None:
    bus = _new_bus()
    recipient_id = new_agent_id()
    bus.register(recipient_id)
    assert bus.try_recv(recipient_id) is None


def test_bus_send_before_flush_is_not_yet_delivered() -> None:
    bus = _new_bus()
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    bus.send(recipient_id, _sample_message(sender_id))
    assert bus.pending_count() == 1
    assert bus.inbox_count(recipient_id) == 0
    assert bus.try_recv(recipient_id) is None


def test_bus_send_to_unregistered_recipient_raises() -> None:
    bus = _new_bus()
    sender_id = new_agent_id()
    bus.register(sender_id)
    with pytest.raises(UnknownEndpointError):
        bus.send(new_agent_id(), _sample_message(sender_id))


def test_bus_recv_from_unregistered_agent_raises() -> None:
    bus = _new_bus()
    with pytest.raises(UnknownEndpointError):
        bus.try_recv(new_agent_id())


def test_drop_mode_prevents_delivery_entirely() -> None:
    fault_config = FaultConfig(seed=1, drop_probability=1.0)
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    bus.send(recipient_id, _sample_message(sender_id))
    bus.flush()

    assert bus.pending_count() == 0
    assert bus.inbox_count(recipient_id) == 0
    assert bus.try_recv(recipient_id) is None


def test_duplicate_mode_delivers_the_same_message_twice() -> None:
    fault_config = FaultConfig(seed=2, duplicate_probability=1.0)
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    bus.send(recipient_id, _sample_message(sender_id))
    bus.flush()

    first = bus.try_recv(recipient_id)
    second = bus.try_recv(recipient_id)
    third = bus.try_recv(recipient_id)

    assert isinstance(first, Ok)
    assert isinstance(second, Ok)
    assert third is None
    assert first.value.msg_id == second.value.msg_id


def test_corrupt_mode_flips_bytes_and_decode_fails() -> None:
    fault_config = FaultConfig(seed=3, corrupt_probability=1.0)
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    bus.send(recipient_id, _sample_message(sender_id))
    bus.flush()

    received = bus.try_recv(recipient_id)
    assert isinstance(received, Err)


def test_reorder_mode_can_actually_change_delivery_order() -> None:
    # Seed=3 is verified (by direct interpreter check against this exact
    # FaultInjector call sequence during development) to actually swap a
    # 2-element delivery batch -- a "reorder" mode that never demonstrably
    # changes order would make ISC-21/68 vacuous.
    fault_config = FaultConfig(seed=3, reorder=True)
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    first_sent = _sample_message(sender_id, payload=b"first")
    second_sent = _sample_message(sender_id, payload=b"second")
    bus.send(recipient_id, first_sent)
    bus.send(recipient_id, second_sent)
    bus.flush()

    first_received = bus.try_recv(recipient_id)
    second_received = bus.try_recv(recipient_id)

    assert isinstance(first_received, Ok)
    assert isinstance(second_received, Ok)
    delivered_ids = [first_received.value.msg_id, second_received.value.msg_id]
    sent_ids = [first_sent.msg_id, second_sent.msg_id]
    assert set(delivered_ids) == set(sent_ids)
    assert delivered_ids != sent_ids  # actually reordered, not coincidentally identical


def test_reorder_disabled_by_default_preserves_send_order() -> None:
    fault_config = FaultConfig(seed=3)  # same seed as the reorder test above, but reorder=False here
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    first_sent = _sample_message(sender_id, payload=b"first")
    second_sent = _sample_message(sender_id, payload=b"second")
    bus.send(recipient_id, first_sent)
    bus.send(recipient_id, second_sent)
    bus.flush()

    first_received = bus.try_recv(recipient_id)
    second_received = bus.try_recv(recipient_id)
    assert isinstance(first_received, Ok)
    assert isinstance(second_received, Ok)
    assert [first_received.value.msg_id, second_received.value.msg_id] == [first_sent.msg_id, second_sent.msg_id]


def test_fault_injector_determinism_same_seed_same_sequence() -> None:
    config = FaultConfig(seed=42, drop_probability=0.5, duplicate_probability=0.5, corrupt_probability=0.5)
    injector_a = FaultInjector(config)
    injector_b = FaultInjector(config)

    sequence_a = [(injector_a.roll_drop(), injector_a.roll_duplicate(), injector_a.roll_corrupt()) for _ in range(20)]
    sequence_b = [(injector_b.roll_drop(), injector_b.roll_duplicate(), injector_b.roll_corrupt()) for _ in range(20)]

    assert sequence_a == sequence_b

    # Anti-vacuity: with p=0.5 across 60 rolls, both True and False must show
    # up, or this "determinism" proof would trivially hold for an injector
    # that always returns the same constant value.
    flattened = [value for triple in sequence_a for value in triple]
    assert True in flattened
    assert False in flattened


def test_fault_injector_different_seeds_can_diverge() -> None:
    config_a = FaultConfig(seed=1, drop_probability=0.5, duplicate_probability=0.5, corrupt_probability=0.5)
    config_b = FaultConfig(seed=2, drop_probability=0.5, duplicate_probability=0.5, corrupt_probability=0.5)
    injector_a = FaultInjector(config_a)
    injector_b = FaultInjector(config_b)

    sequence_a = [(injector_a.roll_drop(), injector_a.roll_duplicate(), injector_a.roll_corrupt()) for _ in range(20)]
    sequence_b = [(injector_b.roll_drop(), injector_b.roll_duplicate(), injector_b.roll_corrupt()) for _ in range(20)]

    assert sequence_a != sequence_b


def test_fault_injector_corrupt_is_a_noop_on_empty_bytes() -> None:
    injector = FaultInjector(FaultConfig(seed=1))
    assert injector.corrupt(b"") == b""


def test_corrupt_disabled_by_default_leaves_bytes_intact() -> None:
    fault_config = FaultConfig(seed=3)  # corrupt_probability defaults to 0.0
    bus = _new_bus(fault_config)
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)

    bus.send(recipient_id, _sample_message(sender_id))
    bus.flush()

    received = bus.try_recv(recipient_id)
    assert isinstance(received, Ok)
