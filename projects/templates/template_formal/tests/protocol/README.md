# `tests/protocol/` — session-type-shaped state machine tests

Behavioral tests for `src/template_formal/protocol/{session,errors}.py` —
the phase-tagged `IdleSession` → `HandshakingSession` → `EstablishedSession`
→ `ClosedSession` state machine, and the real `bytes` wire format
(`encode_wire_message` / `decode_wire_message`) that gives corruption
something concrete to corrupt.

**Speed:** fast unit-test directory. Every test constructs a handful of
in-process session/message objects and asserts on them directly — no
sockets, no SQLite, no simulation loop. The whole file runs in a fraction
of a second.

## File

| File | Lines | Covers | What it actually tests |
| --- | --- | --- | --- |
| [`test_session.py`](test_session.py) | 280 | ISC-16, ISC-17, ISC-19, ISC-26 | Every phase transition, both success and rejection paths: `IdleSession.open()` returns a `HandshakingSession` plus a real `hello` `WireMessage`; `IdleSession.accept_hello()` returns `Result[Ok[(EstablishedSession, ack)], ProtocolViolation]`, rejecting a wrong-`kind` message; `HandshakingSession.complete()` returns `Result[EstablishedSession, ProtocolViolation]`, rejecting both a wrong `kind` and a reply from an unexpected sender; `EstablishedSession.send`/`.receive` round-trip a payload and reject wrong-kind/wrong-sender messages; `EstablishedSession.close()` returns a `ClosedSession`. **Every one of `open`, `accept_hello`, `complete`, and `close` is separately proven to raise `SessionConsumedError` on a second call to the same instance** — this is the runtime half of the affine-session discipline (ISC-19), pairing the static half proven by `tests/mypy_fixtures/bad_phase_transition.py` (calling `.send` on an `IdleSession` is rejected by mypy because the method doesn't exist on that class at all — a different, stronger guarantee than the runtime-only consumed-flag check this file proves for the methods that *do* exist on each phase). The back half covers the real `bytes` wire format (ISC-26): a round-trip through `encode_wire_message`/`decode_wire_message` preserves the message and produces real header overhead (`len(wire_bytes) > len(payload)`); `decode_wire_message` rejects a truncated frame (`"short"`), a checksum-corrupted frame via a single flipped byte (`"checksum"`, CRC32-caught), empty bytes, corrupted magic bytes (`"magic"`), an unknown kind code (`"kind code"`), and a payload-length-field mismatch (`"length mismatch"`) — each corruption test recomputes the CRC32 trailer over the corrupted body first, so the test isolates the specific check it targets rather than merely tripping the checksum check by accident. |

## Why every phase-transition test has a paired rejection test

ISC-25 (anti) requires that no phase-transition invariant is proven only
on the happy path. Every `open`/`accept_hello`/`complete`/`send`/`receive`
method in this file has at least one test proving its acceptance
condition and at least one proving a concrete rejection condition
(`ProtocolViolation`) — never just "runs without error."
