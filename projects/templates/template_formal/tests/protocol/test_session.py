"""Behavioral tests for the session-type-shaped protocol state machine.

Covers ISC-16..17 (phase-tagged classes, methods return the next phase),
ISC-19 (runtime consumed-flag guard pairing the static mypy proof in
``bad_phase_transition.py``), and ISC-26 (real bytes round trip, with a
paired negative control on truncated/corrupted bytes).
"""

from __future__ import annotations

import zlib

import pytest

from template_formal.protocol.errors import ProtocolViolation
from template_formal.protocol.session import (
    ClosedSession,
    EstablishedSession,
    HandshakingSession,
    IdleSession,
    SessionConsumedError,
    WireMessage,
    decode_wire_message,
    encode_wire_message,
)
from template_formal.types.ids import new_agent_id, new_message_id
from template_formal.types.result import Err, Ok


def test_idle_open_returns_handshaking_session_and_hello_message() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    idle = IdleSession(local_id=local_id)

    handshaking, hello = idle.open(peer_id)

    assert isinstance(handshaking, HandshakingSession)
    assert handshaking.local_id == local_id
    assert handshaking.peer_id == peer_id
    assert hello.kind == "hello"
    assert hello.sender == local_id
    assert hello.payload == b""


def test_idle_open_twice_on_same_instance_raises_session_consumed_error() -> None:
    idle = IdleSession(local_id=new_agent_id())
    idle.open(new_agent_id())
    with pytest.raises(SessionConsumedError):
        idle.open(new_agent_id())


def test_idle_accept_hello_returns_established_session_and_ack() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    idle = IdleSession(local_id=local_id)
    hello = WireMessage(msg_id=new_message_id(), sender=peer_id, kind="hello", payload=b"")

    result = idle.accept_hello(hello)

    assert isinstance(result, Ok)
    established, ack = result.value
    assert isinstance(established, EstablishedSession)
    assert established.local_id == local_id
    assert established.peer_id == peer_id
    assert ack.kind == "hello_ack"
    assert ack.sender == local_id


def test_idle_accept_hello_rejects_wrong_kind_as_protocol_violation() -> None:
    idle = IdleSession(local_id=new_agent_id())
    wrong_kind = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"")

    result = idle.accept_hello(wrong_kind)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)
    assert "hello" in result.error.reason


def test_idle_accept_hello_twice_on_same_instance_raises_session_consumed_error() -> None:
    idle = IdleSession(local_id=new_agent_id())
    hello = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="hello", payload=b"")
    idle.accept_hello(hello)
    with pytest.raises(SessionConsumedError):
        idle.accept_hello(hello)


def test_handshaking_complete_returns_established_session() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    idle = IdleSession(local_id=local_id)
    handshaking, _hello = idle.open(peer_id)
    ack = WireMessage(msg_id=new_message_id(), sender=peer_id, kind="hello_ack", payload=b"")

    result = handshaking.complete(ack)

    assert isinstance(result, Ok)
    assert isinstance(result.value, EstablishedSession)
    assert result.value.local_id == local_id
    assert result.value.peer_id == peer_id


def test_handshaking_complete_rejects_wrong_kind_as_protocol_violation() -> None:
    peer_id = new_agent_id()
    idle = IdleSession(local_id=new_agent_id())
    handshaking, _hello = idle.open(peer_id)
    wrong_kind = WireMessage(msg_id=new_message_id(), sender=peer_id, kind="data", payload=b"")

    result = handshaking.complete(wrong_kind)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)


def test_handshaking_complete_rejects_reply_from_wrong_sender() -> None:
    idle = IdleSession(local_id=new_agent_id())
    handshaking, _hello = idle.open(new_agent_id())
    impostor = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="hello_ack", payload=b"")

    result = handshaking.complete(impostor)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)
    assert "unexpected sender" in result.error.reason


def test_handshaking_complete_twice_on_same_instance_raises_session_consumed_error() -> None:
    peer_id = new_agent_id()
    idle = IdleSession(local_id=new_agent_id())
    handshaking, _hello = idle.open(peer_id)
    ack = WireMessage(msg_id=new_message_id(), sender=peer_id, kind="hello_ack", payload=b"")
    handshaking.complete(ack)
    with pytest.raises(SessionConsumedError):
        handshaking.complete(ack)


def test_established_send_and_receive_round_trip_payload() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    a = EstablishedSession(local_id=local_id, peer_id=peer_id)
    b = EstablishedSession(local_id=peer_id, peer_id=local_id)

    data_msg = a.send(b"pheromone-tick-report")
    result = b.receive(data_msg)

    assert isinstance(result, Ok)
    assert result.value == b"pheromone-tick-report"


def test_established_receive_rejects_wrong_kind_as_protocol_violation() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    established = EstablishedSession(local_id=local_id, peer_id=peer_id)
    wrong_kind = WireMessage(msg_id=new_message_id(), sender=peer_id, kind="hello", payload=b"")

    result = established.receive(wrong_kind)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)


def test_established_receive_rejects_message_from_unexpected_sender() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    established = EstablishedSession(local_id=local_id, peer_id=peer_id)
    impostor_msg = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"x")

    result = established.receive(impostor_msg)

    assert isinstance(result, Err)
    assert isinstance(result.error, ProtocolViolation)


def test_established_close_returns_closed_session() -> None:
    local_id = new_agent_id()
    peer_id = new_agent_id()
    established = EstablishedSession(local_id=local_id, peer_id=peer_id)

    closed = established.close()

    assert isinstance(closed, ClosedSession)
    assert closed.local_id == local_id
    assert closed.peer_id == peer_id


def test_established_close_twice_on_same_instance_raises_session_consumed_error() -> None:
    established = EstablishedSession(local_id=new_agent_id(), peer_id=new_agent_id())
    established.close()
    with pytest.raises(SessionConsumedError):
        established.close()


def test_wire_message_round_trips_through_real_bytes() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"tick-42")

    wire_bytes = encode_wire_message(message)
    assert isinstance(wire_bytes, bytes)
    assert len(wire_bytes) > len(message.payload)  # real header overhead, not a bare passthrough

    decoded = decode_wire_message(wire_bytes)

    assert isinstance(decoded, Ok)
    assert decoded.value == message


def test_decode_wire_message_rejects_truncated_frame() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"tick-42")
    wire_bytes = encode_wire_message(message)

    truncated = wire_bytes[:10]
    result = decode_wire_message(truncated)

    assert isinstance(result, Err)
    assert "short" in result.error.reason


def test_decode_wire_message_rejects_checksum_corrupted_frame() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"tick-42")
    wire_bytes = bytearray(encode_wire_message(message))

    # Flip one byte in the middle of the frame (well inside the header/payload,
    # not the checksum trailer itself) -- CRC32 must catch it.
    flip_index = len(wire_bytes) // 2
    wire_bytes[flip_index] ^= 0xFF

    result = decode_wire_message(bytes(wire_bytes))

    assert isinstance(result, Err)
    assert "checksum" in result.error.reason


def test_decode_wire_message_rejects_empty_bytes() -> None:
    result = decode_wire_message(b"")
    assert isinstance(result, Err)


def test_decode_wire_message_rejects_bad_magic_bytes() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"x")
    wire_bytes = bytearray(encode_wire_message(message))
    wire_bytes[0:4] = b"XXXX"
    # Recompute checksum over the (magic-corrupted) body so this test isolates
    # the magic-byte check from the checksum check -- the checksum must still
    # match for the bad-magic branch specifically to fire.
    body = bytes(wire_bytes[:-4])
    wire_bytes[-4:] = zlib.crc32(body).to_bytes(4, "big")

    result = decode_wire_message(bytes(wire_bytes))

    assert isinstance(result, Err)
    assert "magic" in result.error.reason


def test_decode_wire_message_rejects_unknown_kind_code() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"x")
    wire_bytes = bytearray(encode_wire_message(message))
    wire_bytes[4] = 0xFE  # not a valid kind code
    body = bytes(wire_bytes[:-4])
    wire_bytes[-4:] = zlib.crc32(body).to_bytes(4, "big")

    result = decode_wire_message(bytes(wire_bytes))

    assert isinstance(result, Err)
    assert "kind code" in result.error.reason


def test_decode_wire_message_rejects_payload_length_mismatch() -> None:
    message = WireMessage(msg_id=new_message_id(), sender=new_agent_id(), kind="data", payload=b"exact")
    wire_bytes = bytearray(encode_wire_message(message))
    # Header length field lives right before the payload; corrupt it to claim
    # a longer payload than actually follows.
    header_len = 4 + 1 + 16 + 16
    wire_bytes[header_len : header_len + 4] = (999).to_bytes(4, "big")
    body = bytes(wire_bytes[:-4])
    wire_bytes[-4:] = zlib.crc32(body).to_bytes(4, "big")

    result = decode_wire_message(bytes(wire_bytes))

    assert isinstance(result, Err)
    assert "length mismatch" in result.error.reason
