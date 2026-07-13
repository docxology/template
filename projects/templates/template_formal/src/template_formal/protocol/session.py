"""Session-type-shaped protocol state machine (ISC-16..19, ISC-26).

Four distinct classes -- :class:`IdleSession`, :class:`HandshakingSession`,
:class:`EstablishedSession`, :class:`ClosedSession` -- each fix the shared
:data:`~template_formal.types.phase.PhaseT` type parameter of
:class:`SessionEndpoint` to exactly one phase marker from
:mod:`template_formal.types.phase`. Each phase-transition method returns the
*next* phase's concrete class, never a union that also includes an illegal
successor (ISC-17): e.g. ``IdleSession.open`` returns
``HandshakingSession``, full stop.

What this genuinely proves vs. what it does not
-------------------------------------------------
Because ``send``/``receive`` are defined *only* on ``EstablishedSession`` --
they do not exist as methods on ``IdleSession`` or ``HandshakingSession`` at
all -- calling them on the wrong phase is an ``AttributeError`` under mypy
--strict: an outright type error, not a caught runtime exception. This is
what "illegal states unrepresentable" means here (ISC-18); see
``tests/mypy_fixtures/bad_phase_transition.py`` for the proof-of-detection
fixture.

What mypy --strict *cannot* catch is reusing the *same instance* of a phase
class after it has already produced its successor: ``idle.open(peer)``
returns a fresh ``HandshakingSession``, but nothing in the type system stops
a second, un-reassigned call ``idle.open(peer)`` on the same ``idle``
object -- its type hasn't changed. That is exactly the affine-discipline gap
Python's type system cannot close (see ``ISA`` §Principles); each
transition method here therefore also raises :class:`SessionConsumedError`
at runtime on reuse (ISC-19), pairing the static proof with a dynamic guard.

Wire format
-----------
:func:`encode_wire_message`/:func:`decode_wire_message` marshal a
:class:`WireMessage` to and from real ``bytes`` (ISC-26) -- magic bytes,
a one-byte message kind, the two participant UUIDs, a big-endian payload
length, the payload itself, and a trailing CRC32 checksum over everything
before it. This gives the network layer's "corrupt" fault mode genuine bytes
to mutate and gives the receiver a genuine (not merely typed) way to detect
that mutation.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar
from uuid import UUID

from template_formal.protocol.errors import MalformedMessage, ProtocolViolation
from template_formal.types.ids import AgentId, MessageId, new_message_id
from template_formal.types.phase import Closed, Established, Handshaking, Idle
from template_formal.types.result import Err, Ok, Result

MessageKind = Literal["hello", "hello_ack", "data", "close"]
PhaseT = TypeVar("PhaseT", Idle, Handshaking, Established, Closed)

_MAGIC = b"TF01"
_KIND_CODES: dict[MessageKind, int] = {"hello": 1, "hello_ack": 2, "data": 3, "close": 4}
_CODE_KINDS: dict[int, MessageKind] = {code: kind for kind, code in _KIND_CODES.items()}
_UUID_LEN = 16
_LENGTH_FIELD_LEN = 4
_CHECKSUM_LEN = 4
_HEADER_LEN = len(_MAGIC) + 1 + _UUID_LEN + _UUID_LEN + _LENGTH_FIELD_LEN


@dataclass(frozen=True, slots=True)
class WireMessage:
    """A single protocol message, independent of its wire encoding."""

    msg_id: MessageId
    sender: AgentId
    kind: MessageKind
    payload: bytes


def encode_wire_message(message: WireMessage) -> bytes:
    """Encode ``message`` to real, corruptible wire bytes (ISC-26)."""
    body = (
        _MAGIC
        + bytes([_KIND_CODES[message.kind]])
        + message.msg_id.bytes
        + message.sender.bytes
        + len(message.payload).to_bytes(_LENGTH_FIELD_LEN, "big")
        + message.payload
    )
    checksum = zlib.crc32(body).to_bytes(_CHECKSUM_LEN, "big")
    return bytes(body + checksum)


def decode_wire_message(data: bytes) -> Result[WireMessage, MalformedMessage]:
    """Decode wire bytes, or report exactly why they are malformed.

    Never raises: truncation, a bad magic prefix, an unknown kind byte, a
    payload-length mismatch, and (most importantly for the fault-injecting
    bus's "corrupt" mode) a CRC32 mismatch all return
    ``Err(MalformedMessage(...))`` rather than throwing.
    """
    if len(data) < _HEADER_LEN + _CHECKSUM_LEN:
        return Err(MalformedMessage(f"frame too short: {len(data)} bytes"))
    body, checksum_bytes = data[:-_CHECKSUM_LEN], data[-_CHECKSUM_LEN:]
    expected_checksum = int.from_bytes(checksum_bytes, "big")
    actual_checksum = zlib.crc32(body)
    if expected_checksum != actual_checksum:
        return Err(MalformedMessage(f"checksum mismatch: header says {expected_checksum}, computed {actual_checksum}"))
    if body[0 : len(_MAGIC)] != _MAGIC:
        return Err(MalformedMessage(f"bad magic bytes: {body[0 : len(_MAGIC)]!r}"))
    offset = len(_MAGIC)
    kind_code = body[offset]
    if kind_code not in _CODE_KINDS:
        return Err(MalformedMessage(f"unknown message kind code: {kind_code}"))
    offset += 1
    msg_id_bytes = body[offset : offset + _UUID_LEN]
    offset += _UUID_LEN
    sender_bytes = body[offset : offset + _UUID_LEN]
    offset += _UUID_LEN
    payload_len = int.from_bytes(body[offset : offset + _LENGTH_FIELD_LEN], "big")
    offset += _LENGTH_FIELD_LEN
    payload = body[offset:]
    if len(payload) != payload_len:
        return Err(MalformedMessage(f"payload length mismatch: header says {payload_len}, got {len(payload)}"))
    return Ok(
        WireMessage(
            msg_id=MessageId(UUID(bytes=msg_id_bytes)),
            sender=AgentId(UUID(bytes=sender_bytes)),
            kind=_CODE_KINDS[kind_code],
            payload=payload,
        )
    )


class SessionConsumedError(RuntimeError):
    """Raised when a phase-transition method fires twice on one instance.

    This is the runtime half of the paired static+dynamic proof (ISC-19):
    mypy --strict cannot know that a *particular object* has already been
    consumed -- its type never changes, only a fresh call produces the next
    phase -- so the affine discipline is enforced here at runtime. This is a
    programmer-error condition (holding onto and re-using a stale handle),
    not an expected network/protocol fault, so it raises rather than
    returning ``Result.Err``.
    """


class SessionEndpoint(Generic[PhaseT]):
    """Phantom-tagged base: ``PhaseT`` never appears as a stored field.

    Each concrete subclass below fixes ``PhaseT`` to exactly one phase
    marker from :mod:`template_formal.types.phase` (``SessionEndpoint[Idle]``,
    ``SessionEndpoint[Established]``, ...); the type parameter exists purely
    so mypy can distinguish the phases, matching the shared
    ``Generic[PhaseT]`` convention used by the storage layer's
    ``TransactionHandle``.
    """

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class IdleSession(SessionEndpoint[Idle]):
    """No handshake attempted yet. Two entry points: initiate, or accept."""

    local_id: AgentId
    _consumed: bool = field(default=False, init=False)

    def open(self, peer: AgentId) -> tuple[HandshakingSession, WireMessage]:
        """Initiate a handshake as the connecting side.

        Returns the next-phase :class:`HandshakingSession` together with the
        ``hello`` :class:`WireMessage` the caller must send to ``peer`` over
        the network layer.
        """
        if self._consumed:
            raise SessionConsumedError("IdleSession.open() called twice on the same instance")
        object.__setattr__(self, "_consumed", True)
        hello = WireMessage(msg_id=new_message_id(), sender=self.local_id, kind="hello", payload=b"")
        return HandshakingSession(local_id=self.local_id, peer_id=peer), hello

    def accept_hello(self, hello: WireMessage) -> Result[tuple[EstablishedSession, WireMessage], ProtocolViolation]:
        """Accept an inbound ``hello`` as the responding side.

        The responder already has everything it needs (the peer's identity,
        carried on the ``hello`` frame) to move straight to
        :class:`EstablishedSession`, paired with the ``hello_ack``
        :class:`WireMessage` to send back.
        """
        if self._consumed:
            raise SessionConsumedError("IdleSession.accept_hello() called twice on the same instance")
        object.__setattr__(self, "_consumed", True)
        if hello.kind != "hello":
            return Err(ProtocolViolation(f"expected 'hello', got {hello.kind!r}"))
        ack = WireMessage(msg_id=new_message_id(), sender=self.local_id, kind="hello_ack", payload=b"")
        return Ok((EstablishedSession(local_id=self.local_id, peer_id=hello.sender), ack))


@dataclass(frozen=True, slots=True)
class HandshakingSession(SessionEndpoint[Handshaking]):
    """A handshake is in progress; only ``complete`` is legal here.

    Note that ``send``/``receive``/``close`` -- the ``Established``-only
    methods -- simply do not exist on this class (ISC-18).
    """

    local_id: AgentId
    peer_id: AgentId
    _consumed: bool = field(default=False, init=False)

    def complete(self, hello_ack: WireMessage) -> Result[EstablishedSession, ProtocolViolation]:
        """Consume an inbound ``hello_ack`` to reach :class:`EstablishedSession`."""
        if self._consumed:
            raise SessionConsumedError("HandshakingSession.complete() called twice on the same instance")
        object.__setattr__(self, "_consumed", True)
        if hello_ack.kind != "hello_ack":
            return Err(ProtocolViolation(f"expected 'hello_ack', got {hello_ack.kind!r}"))
        if hello_ack.sender != self.peer_id:
            return Err(ProtocolViolation(f"hello_ack from unexpected sender {hello_ack.sender!r}"))
        return Ok(EstablishedSession(local_id=self.local_id, peer_id=self.peer_id))


@dataclass(frozen=True, slots=True)
class EstablishedSession(SessionEndpoint[Established]):
    """The session is open. ``send``/``receive``/``close`` are legal here
    and *only* here -- they are not defined on :class:`IdleSession` or
    :class:`HandshakingSession` (ISC-18)."""

    local_id: AgentId
    peer_id: AgentId
    _consumed: bool = field(default=False, init=False)

    def send(self, payload: bytes) -> WireMessage:
        """Build a ``data`` :class:`WireMessage` addressed to this session's peer."""
        return WireMessage(msg_id=new_message_id(), sender=self.local_id, kind="data", payload=payload)

    def receive(self, message: WireMessage) -> Result[bytes, ProtocolViolation]:
        """Validate and unwrap an inbound ``data`` frame's payload."""
        if message.kind != "data":
            return Err(ProtocolViolation(f"expected 'data', got {message.kind!r}"))
        if message.sender != self.peer_id:
            return Err(ProtocolViolation(f"data frame from unexpected sender {message.sender!r}"))
        return Ok(message.payload)

    def close(self) -> ClosedSession:
        """Consume this session, producing the terminal :class:`ClosedSession`."""
        if self._consumed:
            raise SessionConsumedError("EstablishedSession.close() called twice on the same instance")
        object.__setattr__(self, "_consumed", True)
        return ClosedSession(local_id=self.local_id, peer_id=self.peer_id)


@dataclass(frozen=True, slots=True)
class ClosedSession(SessionEndpoint[Closed]):
    """Terminal phase. No further methods are legal, so none are defined."""

    local_id: AgentId
    peer_id: AgentId
