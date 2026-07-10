# `src/template_formal/network/` — the in-process message bus

Models the colony's networking layer without any real sockets: agents exchange
messages by encoding them to real `bytes` and pushing them through a shared,
seeded, fault-injectable in-process queue. Per the ISA's `Out of Scope`, this
is deliberately *not* a real transport — the point is a typed bus abstraction
that can inject realistic wire-level failure (drop, duplicate, corrupt,
reorder) deterministically, so protocol-layer negative-control tests
(`tests/network/test_handshake_over_bus.py`) can exercise a real handshake
against a real fault instead of a mocked one.

## Modules

| File | Responsibility |
| --- | --- |
| `bus.py` | `InProcessBus[MsgT]` — a typed, in-process send/flush/recv queue with an optional `FaultInjector`; `FaultConfig` declares which fault modes are active and at what probability; `FaultInjector` is the seeded `random.Random` engine that actually rolls drop/duplicate/corrupt/reorder decisions. |

## Public API (`__init__.py`)

```python
from template_formal.network import FaultConfig, FaultInjector, InProcessBus, UnknownEndpointError
```

Nothing else is exported — callers never reach into `bus.py`'s internals
(`_inboxes`, `_pending`) directly.

## Core invariant

The bus never inspects message *content*, only wire *bytes*. `send()` always
runs `encode(message) -> bytes` before a fault can touch it, and `try_recv()`
always runs `decode(bytes) -> Result[MsgT, MalformedMessage]` on the way out —
so "corrupt" mode has genuine bytes to XOR-flip, and a corrupted frame is
delivered as bytes for the *receiver's own* `decode` to reject via
`Result.Err(MalformedMessage(...))`, never a bus-side exception (ISC-26).

Fault injection is a single `random.Random(seed)` stream per `FaultInjector`,
rolled in a fixed per-send order (drop → corrupt → duplicate, per
`InProcessBus.send`'s actual call sequence — `FaultConfig`'s own docstring
says "drop → duplicate → corrupt", which does not match the implementation;
noted here as a real doc/code drift, not fixed as part of this pass since it
does not change the reproducibility guarantee: the same seed still rolls the
same three decisions in the same order in every run), plus one
`reorder` roll per `flush()` batch. Two injectors built from an identical
`FaultConfig` reproduce an identical fault sequence bit-for-bit — this is what
makes a fault-injected test run reproducible rather than "flaky in a way that
happens to pass" (ISC-21, ISC-22). A wiring bug — `send`/`try_recv` against an
`AgentId` that was never `register()`-ed — raises `UnknownEndpointError`
rather than returning a `Result`: that's a programmer error, not an expected
network fault.

`send()` enqueues into an internal `_pending` batch; frames only reach a
recipient's inbox after `flush()` moves them across — that batch boundary is
what gives the `reorder` mode something to reorder, and is why a test that
calls `send()` without `flush()` sees `pending_count() == 1` and
`inbox_count() == 0` (`test_bus_send_before_flush_is_not_yet_delivered`).

## Tests

`tests/network/` — two files:

- `test_bus.py` — the bus and `FaultInjector` in isolation: round-trip
  send/flush/recv, unregistered-endpoint errors, each fault mode individually
  (including "disabled by default" controls), and same-seed/different-seed
  determinism (ISC-20, ISC-21, ISC-22).
- `test_handshake_over_bus.py` — a real `Agent`/protocol handshake driven
  *through* the bus with each fault mode enabled, asserting the receiving
  side's protocol state machine returns a typed `Result.Err` (`ProtocolViolation`
  under drop, `MalformedMessage` under corrupt) rather than crashing or
  silently advancing phase (ISC-23, ISC-24, ISC-25).

## ISA cross-reference

ISC-20, ISC-21, ISC-22, ISC-23, ISC-24, ISC-25, ISC-26, ISC-68 (anti: no fault
mode may be left permanently disabled by default in a way that makes ISC-23/24
vacuously pass on an all-happy-path run). See `ISA.md` for full criteria text.
