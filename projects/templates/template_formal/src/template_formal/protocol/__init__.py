"""Session-type-shaped protocol state machine and its wire format."""

from template_formal.protocol.errors import MalformedMessage, ProtocolViolation
from template_formal.protocol.session import (
    ClosedSession,
    EstablishedSession,
    HandshakingSession,
    IdleSession,
    MessageKind,
    SessionConsumedError,
    SessionEndpoint,
    WireMessage,
    decode_wire_message,
    encode_wire_message,
)

__all__ = [
    "MalformedMessage",
    "ProtocolViolation",
    "ClosedSession",
    "EstablishedSession",
    "HandshakingSession",
    "IdleSession",
    "MessageKind",
    "SessionConsumedError",
    "SessionEndpoint",
    "WireMessage",
    "decode_wire_message",
    "encode_wire_message",
]
