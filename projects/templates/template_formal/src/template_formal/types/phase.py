"""Phantom phase-marker types shared by the protocol and storage layers.

A phase marker is a zero-runtime-cost class used purely as a type-level
tag: ``Generic[PhaseT]`` containers use these markers to make it a mypy
--strict error to call a phase-specific method on the wrong phase. The
markers carry no fields and are never instantiated — they exist only in
type position (``SessionEndpoint[Established]``), which is what makes them
"phantom".
"""

from __future__ import annotations

from typing import TypeVar


class Idle:
    """Marker: no handshake has been attempted yet."""


class Handshaking:
    """Marker: a handshake is in progress; only handshake methods are legal."""


class Established:
    """Marker: the session is open; only data-transfer methods are legal."""


class Closed:
    """Marker: the session is terminated; no further methods are legal."""


PhaseT = TypeVar("PhaseT", Idle, Handshaking, Established, Closed)
