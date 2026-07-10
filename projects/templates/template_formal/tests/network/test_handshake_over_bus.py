"""End-to-end handshake driven through the in-process bus (ISC-16..26).

`_drive_handshake` is the one piece of orchestration logic in this file: it
runs a real two-message handshake (HELLO / HELLO_ACK) between two
`IdleSession` endpoints over a real `InProcessBus`, polling for a bounded
number of ticks. Every phase-transition invariant proven statically in
`tests/mypy_fixtures/bad_phase_transition.py` is paired here with a real,
fault-injected run (ISC-25): the happy path proves the handshake completes
end to end; the drop-mode run proves a `Result.Err(ProtocolViolation(...))`
comes back rather than a crash or a silent phase advance (ISC-23); the
corrupt-mode run proves a `Result.Err(MalformedMessage(...))` comes back
(ISC-24) -- the runtime guard mypy --strict cannot provide, since the wire
boundary is untyped bytes, not a typed Python object.
"""

from __future__ import annotations

from template_formal.network.bus import FaultConfig, InProcessBus
from template_formal.protocol.errors import MalformedMessage, ProtocolViolation
from template_formal.protocol.session import (
    EstablishedSession,
    IdleSession,
    WireMessage,
    decode_wire_message,
    encode_wire_message,
)
from template_formal.types.ids import AgentId, new_agent_id
from template_formal.types.result import Err, Ok, Result


def _new_bus(fault_config: FaultConfig | None = None) -> InProcessBus[WireMessage]:
    return InProcessBus(encode=encode_wire_message, decode=decode_wire_message, fault_config=fault_config)


def _drive_handshake(
    bus: InProcessBus[WireMessage],
    initiator_id: AgentId,
    responder_id: AgentId,
    max_ticks: int = 5,
) -> Result[tuple[EstablishedSession, EstablishedSession], ProtocolViolation | MalformedMessage]:
    """Drive one full handshake to completion over `bus`, or fail typed.

    Polls the bus up to `max_ticks` times per leg. A reply that never
    arrives (e.g. dropped in-flight) yields `Err(ProtocolViolation(...))` --
    a real protocol has no way to distinguish "the peer never replied" from
    "the network ate the reply", so both report identically. A reply that
    arrives corrupted yields `Err(MalformedMessage(...))` propagated
    directly from the wire decoder, never silently swallowed or reframed.
    """
    initiator_idle = IdleSession(local_id=initiator_id)
    responder_idle = IdleSession(local_id=responder_id)

    initiator_hs, hello = initiator_idle.open(responder_id)
    bus.send(responder_id, hello)
    bus.flush()

    hello_result: Result[WireMessage, MalformedMessage] | None = None
    for _ in range(max_ticks):
        polled = bus.try_recv(responder_id)
        if polled is not None:
            hello_result = polled
            break
    if hello_result is None:
        return Err(ProtocolViolation("handshake timed out: no HELLO ever arrived at the responder"))
    if isinstance(hello_result, Err):
        return hello_result

    accept_result = responder_idle.accept_hello(hello_result.value)
    if isinstance(accept_result, Err):
        return accept_result
    responder_established, ack = accept_result.value
    bus.send(initiator_id, ack)
    bus.flush()

    ack_result: Result[WireMessage, MalformedMessage] | None = None
    for _ in range(max_ticks):
        polled = bus.try_recv(initiator_id)
        if polled is not None:
            ack_result = polled
            break
    if ack_result is None:
        return Err(ProtocolViolation("handshake timed out: no HELLO_ACK ever arrived at the initiator"))
    if isinstance(ack_result, Err):
        return ack_result

    complete_result = initiator_hs.complete(ack_result.value)
    if isinstance(complete_result, Err):
        return complete_result
    return Ok((complete_result.value, responder_established))


def test_happy_path_step_by_step_reaches_established_on_both_sides() -> None:
    """Exercises the full API surface manually, one wire hop at a time."""
    bus = _new_bus()
    alice_id = new_agent_id()
    bob_id = new_agent_id()
    bus.register(alice_id)
    bus.register(bob_id)

    alice_idle = IdleSession(local_id=alice_id)
    bob_idle = IdleSession(local_id=bob_id)

    alice_hs, hello = alice_idle.open(bob_id)
    bus.send(bob_id, hello)
    bus.flush()

    received_hello = bus.try_recv(bob_id)
    assert isinstance(received_hello, Ok)
    accept_result = bob_idle.accept_hello(received_hello.value)
    assert isinstance(accept_result, Ok)
    bob_established, ack = accept_result.value
    bus.send(alice_id, ack)
    bus.flush()

    received_ack = bus.try_recv(alice_id)
    assert isinstance(received_ack, Ok)
    complete_result = alice_hs.complete(received_ack.value)
    assert isinstance(complete_result, Ok)
    alice_established = complete_result.value

    assert isinstance(alice_established, EstablishedSession)
    assert isinstance(bob_established, EstablishedSession)

    # Data round trip, to be thorough about what "Established" actually unlocks.
    data_msg = alice_established.send(b"pheromone-tick-report")
    bus.send(bob_id, data_msg)
    bus.flush()
    received_data = bus.try_recv(bob_id)
    assert isinstance(received_data, Ok)
    receive_result = bob_established.receive(received_data.value)
    assert isinstance(receive_result, Ok)
    assert receive_result.value == b"pheromone-tick-report"


def test_happy_path_via_driver_reaches_established_on_both_sides() -> None:
    bus = _new_bus()
    alice_id = new_agent_id()
    bob_id = new_agent_id()
    bus.register(alice_id)
    bus.register(bob_id)

    result = _drive_handshake(bus, alice_id, bob_id)

    assert isinstance(result, Ok)
    alice_established, bob_established = result.value
    assert isinstance(alice_established, EstablishedSession)
    assert isinstance(bob_established, EstablishedSession)


def test_drop_mode_yields_protocol_violation_not_a_crash() -> None:
    """ISC-23: drop-mode handshake returns Result.Err(ProtocolViolation), never a crash."""
    fault_config = FaultConfig(seed=7, drop_probability=1.0)
    bus = _new_bus(fault_config)
    alice_id = new_agent_id()
    bob_id = new_agent_id()
    bus.register(alice_id)
    bus.register(bob_id)

    result = _drive_handshake(bus, alice_id, bob_id)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)


def test_corrupt_mode_yields_malformed_message_result() -> None:
    """ISC-24: corrupt-mode handshake returns Result.Err(MalformedMessage), the runtime guard mypy cannot provide."""
    fault_config = FaultConfig(seed=11, corrupt_probability=1.0)
    bus = _new_bus(fault_config)
    alice_id = new_agent_id()
    bob_id = new_agent_id()
    bus.register(alice_id)
    bus.register(bob_id)

    result = _drive_handshake(bus, alice_id, bob_id)

    assert isinstance(result, Err)
    assert isinstance(result.error, MalformedMessage)


def test_duplicate_mode_still_completes_handshake_idempotently() -> None:
    """A duplicated HELLO must not desync the responder: the driver only
    consumes the first copy it polls, and the extra copy is simply left
    sitting unread in the inbox rather than corrupting protocol state."""
    fault_config = FaultConfig(seed=13, duplicate_probability=1.0)
    bus = _new_bus(fault_config)
    alice_id = new_agent_id()
    bob_id = new_agent_id()
    bus.register(alice_id)
    bus.register(bob_id)

    result = _drive_handshake(bus, alice_id, bob_id)

    assert isinstance(result, Ok)
    # The duplicated HELLO's second copy is still sitting in Bob's inbox,
    # and the duplicated HELLO_ACK's second copy in Alice's -- proving
    # "duplicate" really did enqueue twice, not that this test is vacuous.
    assert bus.inbox_count(bob_id) >= 1
    assert bus.inbox_count(alice_id) >= 1
