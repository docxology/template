"""In-process typed message bus with seeded fault injection (ISC-20..22, ISC-26).

Models the "network" layer of the decentralized ant-robot simulation: agent
endpoints exchange messages entirely in-process -- no real sockets, per the
ISA's ``Out of Scope`` -- but messages are still marshalled through injected
``encode``/``decode`` callables to real ``bytes`` before they sit in an
inbox, so that "corrupt" fault mode has genuine bytes to mutate rather than
a Python object reference it could only swap or leave alone.

Fault injection is seeded (``random.Random(seed)``) and each mode --
``drop``, ``duplicate``, ``corrupt``, ``reorder`` -- is independently
toggleable via :class:`FaultConfig`. The same seed reproduces the exact same
sequence of fault decisions (:class:`FaultInjector`, verified by
``tests/network/test_bus.py::test_fault_injector_determinism_same_seed_same_sequence``),
which is what makes a fault-injected test run reproducible rather than
merely "sometimes flaky in a way that happens to pass."

None of the fault modes raise for an expected condition: a dropped message
is simply never enqueued, and a corrupted frame is delivered as corrupted
bytes for the receiver's own ``decode`` to reject via
``Result.Err(MalformedMessage(...))`` -- the bus itself never inspects
message *content*, only wire *bytes*.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar

from template_formal.protocol.errors import MalformedMessage
from template_formal.types.ids import AgentId
from template_formal.types.result import Result

MsgT = TypeVar("MsgT")


class UnknownEndpointError(RuntimeError):
    """Raised when send/recv targets an :class:`AgentId` never registered.

    A wiring bug (talking to an agent the bus doesn't know about) is a
    programmer error, not an expected network fault, so it raises rather
    than returning ``Result.Err``.
    """


@dataclass(frozen=True, slots=True)
class FaultConfig:
    """Seeded, independently toggleable fault-injection configuration.

    Each probabilistic mode is drawn independently from the same
    ``random.Random(seed)`` stream, in the fixed per-send order
    drop -> duplicate -> corrupt, plus one reorder decision per
    :meth:`InProcessBus.flush` batch -- so two :class:`FaultInjector`
    instances built from an identical ``FaultConfig`` reproduce an
    identical fault sequence bit-for-bit (ISC-22).
    """

    seed: int
    drop_probability: float = 0.0
    duplicate_probability: float = 0.0
    corrupt_probability: float = 0.0
    reorder: bool = False


class FaultInjector:
    """Deterministic fault-injection engine driven by ``random.Random(seed)``."""

    def __init__(self, config: FaultConfig) -> None:
        self._config = config
        self._rng = random.Random(config.seed)

    def roll_drop(self) -> bool:
        """Return ``True`` iff this send should be silently dropped."""
        return self._rng.random() < self._config.drop_probability

    def roll_duplicate(self) -> bool:
        """Return ``True`` iff this send should be enqueued a second time."""
        return self._rng.random() < self._config.duplicate_probability

    def roll_corrupt(self) -> bool:
        """Return ``True`` iff this send's bytes should be corrupted."""
        return self._rng.random() < self._config.corrupt_probability

    def corrupt(self, data: bytes) -> bytes:
        """Flip every bit of one deterministically-chosen byte in ``data``.

        A no-op on an empty frame (nothing to flip). Flipping a whole byte
        (XOR ``0xFF``) rather than a single bit maximizes the chance any
        downstream integrity check (e.g. a CRC32) actually notices, without
        needing to know the wire format.
        """
        if not data:
            return data
        index = self._rng.randrange(len(data))
        mutable = bytearray(data)
        mutable[index] ^= 0xFF
        return bytes(mutable)

    def reorder_batch(self, batch: list[tuple[AgentId, bytes]]) -> list[tuple[AgentId, bytes]]:
        """Shuffle a delivery batch in place-equivalent fashion, if enabled."""
        if not self._config.reorder or len(batch) < 2:
            return batch
        shuffled = list(batch)
        self._rng.shuffle(shuffled)
        return shuffled


@dataclass(slots=True)
class InProcessBus(Generic[MsgT]):
    """An in-process, typed, optionally fault-injecting message bus.

    Parameterized over the message type ``MsgT`` it carries; callers supply
    ``encode``/``decode`` so the bus itself stays agnostic of any particular
    wire format (the protocol layer's ``WireMessage`` codec is one such
    pairing -- see ``template_formal.protocol.session``).
    """

    encode: Callable[[MsgT], bytes]
    decode: Callable[[bytes], Result[MsgT, MalformedMessage]]
    fault_config: FaultConfig | None = None
    _injector: FaultInjector | None = field(init=False, default=None)
    _inboxes: dict[AgentId, list[bytes]] = field(init=False, default_factory=dict)
    _pending: list[tuple[AgentId, bytes]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self._injector = FaultInjector(self.fault_config) if self.fault_config is not None else None

    def register(self, agent_id: AgentId) -> None:
        """Create an empty inbox for ``agent_id`` if one doesn't already exist."""
        self._inboxes.setdefault(agent_id, [])

    def send(self, recipient: AgentId, message: MsgT) -> None:
        """Encode and enqueue ``message`` for ``recipient``, applying faults.

        Enqueued frames sit in an internal pending batch until
        :meth:`flush` moves them into the recipient's inbox -- that batch
        boundary is what gives "reorder" something to reorder.
        """
        if recipient not in self._inboxes:
            raise UnknownEndpointError(f"unregistered bus recipient: {recipient!r}")
        wire_bytes = self.encode(message)
        injector = self._injector
        if injector is None:
            self._pending.append((recipient, wire_bytes))
            return
        if injector.roll_drop():
            return
        if injector.roll_corrupt():
            wire_bytes = injector.corrupt(wire_bytes)
        self._pending.append((recipient, wire_bytes))
        if injector.roll_duplicate():
            self._pending.append((recipient, wire_bytes))

    def flush(self) -> None:
        """Move the pending batch into recipient inboxes, reordering if enabled."""
        batch, self._pending = self._pending, []
        if self._injector is not None:
            batch = self._injector.reorder_batch(batch)
        for recipient, wire_bytes in batch:
            self._inboxes[recipient].append(wire_bytes)

    def try_recv(self, agent_id: AgentId) -> Result[MsgT, MalformedMessage] | None:
        """Pop and decode the oldest frame in ``agent_id``'s inbox.

        Returns ``None`` if the inbox is empty (nothing has arrived yet --
        e.g. because it was dropped, or simply hasn't been flushed). A
        non-``None`` result is always a decode :class:`Result`: ``Ok`` for a
        clean frame, ``Err(MalformedMessage(...))`` for one that failed its
        integrity check.
        """
        if agent_id not in self._inboxes:
            raise UnknownEndpointError(f"unregistered bus recipient: {agent_id!r}")
        inbox = self._inboxes[agent_id]
        if not inbox:
            return None
        wire_bytes = inbox.pop(0)
        return self.decode(wire_bytes)

    def pending_count(self) -> int:
        """Number of frames enqueued but not yet delivered by :meth:`flush`."""
        return len(self._pending)

    def inbox_count(self, agent_id: AgentId) -> int:
        """Number of undelivered (unread) frames sitting in ``agent_id``'s inbox."""
        return len(self._inboxes.get(agent_id, []))
