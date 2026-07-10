"""Expected-failure error types for the protocol and network layers.

Both errors are ordinary frozen dataclasses carried inside :class:`Result.Err
<template_formal.types.result.Err>`. Per the ISA's affine-discipline
principle, a dropped/corrupted network message or a violated protocol
invariant is an *expected, recoverable* condition -- not a programmer bug --
so neither is ever raised as a Python exception. Contrast
``SessionConsumedError`` in :mod:`template_formal.protocol.session`, which
guards genuine affine-reuse programmer misuse and *does* raise.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProtocolViolation:
    """An expected protocol-level failure.

    Covers wrong message kind for the current phase, a reply from an
    unexpected sender, or a handshake that never completes (timeout) because
    the network never delivered the awaited reply.
    """

    reason: str


@dataclass(frozen=True, slots=True)
class MalformedMessage:
    """An expected wire-level failure: bytes that fail to decode.

    Produced when a frame is truncated, carries a bad magic/kind byte, fails
    its CRC32 integrity check, or has a payload-length mismatch -- exactly
    the class of fault a fault-injecting network bus's "corrupt" mode is
    meant to trigger (ISC-24). This is the runtime guard mypy --strict cannot
    provide: the wire boundary is untyped bytes, not a Python object.
    """

    reason: str
