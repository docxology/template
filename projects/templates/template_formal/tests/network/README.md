# `tests/network/` — in-process fault-injectable bus tests

Behavioral tests for `src/template_formal/network/bus.py` — the typed,
in-process `InProcessBus[MsgT]` message bus with a seeded `FaultInjector`
(drop / duplicate / corrupt / reorder), and the end-to-end handshake that
drives `protocol/session.py`'s state machine through it. No real sockets
anywhere — "networking" here means a real Python object graph with an
explicit, independently-toggleable fault model, per the ISA's Out of Scope
section.

**Speed:** fast unit-test directory. Everything is in-process, seeded, and
bounded (at most a handful of registered endpoints, a handful of messages,
a fixed `max_ticks` poll loop) — no real I/O, no simulation sweeps. The
whole directory runs in a fraction of a second.

## Files

| File | Lines | Covers | What it actually tests |
| --- | --- | --- | --- |
| [`test_bus.py`](test_bus.py) | 227 | ISC-20, ISC-21, ISC-22, ISC-68 | Baseline round-trip send/`flush`/`try_recv` with no faults; `try_recv` on an empty inbox returns `None`; a send before `flush()` is not yet delivered (`pending_count() == 1`, `inbox_count() == 0`); sending to or receiving from an unregistered `AgentId` raises `UnknownEndpointError`. Each fault mode is proven to **actually fire**, not merely exist disabled: `drop_probability=1.0` prevents delivery entirely; `duplicate_probability=1.0` delivers the identical `msg_id` twice, then `None`; `corrupt_probability=1.0` flips bytes so `decode_wire_message` returns `Err`; `reorder=True` at a seed independently verified to swap a 2-element batch actually changes delivery order (`delivered_ids != sent_ids`, both message ids still present) — while the identical seed with `reorder=False` preserves send order (proving the seed alone isn't why it reordered). `FaultInjector` determinism is proven two ways: same-seed reproducibility across 20 rolls of `(drop, duplicate, corrupt)` — with an anti-vacuity check that both `True` and `False` actually appear across the 60 flattened rolls — and that two different seeds can diverge. `FaultInjector.corrupt(b"")` is a no-op. Corrupt mode disabled by default (`corrupt_probability` defaulting to `0.0`) leaves bytes intact. |
| [`test_handshake_over_bus.py`](test_handshake_over_bus.py) | 198 | ISC-16–ISC-26 | `_drive_handshake` is the file's one piece of orchestration: a real two-message HELLO/HELLO_ACK handshake between two `IdleSession` endpoints, polling a real `InProcessBus` up to `max_ticks` times per leg. The happy path is exercised twice — once manually, one wire hop at a time (`test_happy_path_step_by_step_...`), including a data round-trip once both sides reach `EstablishedSession`, and once via the `_drive_handshake` driver. Then every ISC-16..26 phase-transition claim gets its paired fault-injected negative control (ISC-25): drop-mode (`drop_probability=1.0`) yields `Err(ProtocolViolation("handshake timed out..."))`, never a crash (ISC-23); corrupt-mode (`corrupt_probability=1.0`) yields `Err(MalformedMessage(...))`, propagated straight from the wire decoder — the runtime guard mypy cannot provide, since the wire boundary is untyped `bytes` (ISC-24); duplicate-mode still completes the handshake, because the driver only ever consumes the first copy polled, and the test proves the second copy really was enqueued (`inbox_count() >= 1` on both sides after completion), not that "duplicate" silently did nothing. |

## Why the bus never uses real sockets

Per `ISA.md`'s Out of Scope, this is a decentralization-*shaped* substrate,
not a production distributed system: `InProcessBus` is a real in-process
object with real fault injection, not a network stack. The fault modes
exist so the protocol layer's error handling can be exercised against
real dropped/duplicated/corrupted/reordered bytes without needing an
actual unreliable network to produce them.
