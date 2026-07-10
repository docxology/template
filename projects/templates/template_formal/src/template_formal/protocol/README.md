# `src/template_formal/protocol/` — session-typed phase state machine + wire format

The handshake/data-transfer protocol two agents speak, expressed as four
distinct classes rather than one class with a phase field. Independent of
transport: this package never touches the network bus, a socket, or
`sqlite3` — it only encodes/decodes `bytes` and transitions typed session
objects.

## Modules

| File | Responsibility |
| --- | --- |
| `session.py` | `SessionEndpoint[PhaseT]` and its four phase-fixed subclasses (`IdleSession`, `HandshakingSession`, `EstablishedSession`, `ClosedSession`); `WireMessage`, `MessageKind`; `encode_wire_message`/`decode_wire_message`; `SessionConsumedError`. |
| `errors.py` | `ProtocolViolation` (expected protocol-level failure — wrong message kind, wrong sender, timeout) and `MalformedMessage` (expected wire-level failure — bytes that fail to decode). Both are `Result.Err` payloads, never raised. |

## Public API (`__init__.py`)

```python
from template_formal.protocol import (
    MalformedMessage, ProtocolViolation,
    ClosedSession, EstablishedSession, HandshakingSession, IdleSession,
    MessageKind, SessionConsumedError, SessionEndpoint, WireMessage,
    decode_wire_message, encode_wire_message,
)
```

## Core invariant

**Illegal states are unrepresentable, not merely rejected.** `IdleSession`,
`HandshakingSession`, `EstablishedSession`, and `ClosedSession` each fix
`SessionEndpoint`'s shared `PhaseT` (from `types/phase.py`) to exactly one
phase marker. `send`/`receive`/`close` are defined **only** on
`EstablishedSession` — they do not exist as methods on `IdleSession` or
`HandshakingSession` at all, so calling one on the wrong phase is a genuine
mypy --strict `AttributeError`-class error (ISC-18), not a caught runtime
exception. Each phase-transition method returns the *next* phase's concrete
class, never a union that also includes an illegal successor (ISC-17) —
e.g. `IdleSession.open` returns `HandshakingSession`, full stop.

**What mypy --strict cannot catch: reusing the same instance.** Nothing
about calling `idle.open(peer)` a second time on the same, un-reassigned
`idle` object is ill-typed — its type hasn't changed. Every transition
method (`IdleSession.open`/`accept_hello`, `HandshakingSession.complete`,
`EstablishedSession.close`) therefore also checks a private `_consumed`
flag and raises `SessionConsumedError` on a second call (ISC-19), pairing
the static proof with a dynamic guard — the same pattern
`storage/transaction.py`'s `TransactionHandle` uses independently, not by
sharing a base class.

**Expected protocol/wire failures return `Result.Err`; only affine reuse
raises.** A wrong message kind, a reply from an unexpected sender, or a
handshake that never completes all come back as
`Err(ProtocolViolation(reason=...))` from `accept_hello`/`complete`/`receive`
— never an exception. `SessionConsumedError` is the one exception this
package raises, reserved for the genuine programmer-error case (a stale
handle re-used after already producing its successor).

**Wire encode/decode round-trips real `bytes`, not object references.**
`encode_wire_message` serializes a `WireMessage` to `_MAGIC` bytes + a
one-byte kind code + two 16-byte UUIDs + a 4-byte big-endian payload length
+ the payload + a trailing 4-byte CRC32 checksum over everything before it
(ISC-26). `decode_wire_message` never raises: a frame too short, a bad
magic prefix, an unknown kind code, a payload-length mismatch, or a CRC32
mismatch each return their own `Err(MalformedMessage(reason=...))` with a
distinct, greppable `reason` substring — this is what gives the network
bus's fault-injecting "corrupt" mode genuine bytes to mutate and the
receiver a genuine (not merely typed) way to detect the mutation.

## Tests

| Test file | Covers |
| --- | --- |
| `tests/protocol/test_session.py` | Every phase transition's happy path and its `Result.Err` fault path (wrong kind, wrong sender), `SessionConsumedError` on double-transition for `IdleSession.open`/`accept_hello`, `HandshakingSession.complete`, and `EstablishedSession.close`, and the full `encode_wire_message`/`decode_wire_message` round trip plus six distinct malformed-frame cases (truncated, checksum-corrupted, empty, bad magic, unknown kind code, payload-length mismatch) — ISC-16, ISC-17, ISC-19, ISC-26. |

Two ISCs for this package are proven **outside** `tests/protocol/`:

- **ISC-18** (calling an `Established`-only method on `Idle` is a mypy
  --strict error) is the negative-control fixture
  `tests/mypy_fixtures/bad_phase_transition.py`, type-checked as a
  subprocess by `tests/test_mypy_oracle.py` against its own captured
  expected-error substring (`"IdleSession" has no attribute "send"`).
- **ISC-23/24/25** (a real handshake driven through the fault-injecting
  network bus, asserting `Err(ProtocolViolation(...))` under drop and
  `Err(MalformedMessage(...))` under corrupt, with every phase-transition
  ISC paired to a fault-injected negative control) live in
  `tests/network/test_handshake_over_bus.py` — that directory tests the
  bus, but the assertions are about this package's `Result` returns under
  real network-layer faults, not the bus's own plumbing.

## ISA cross-reference

ISC-16 through ISC-19, ISC-23 through ISC-26. See `ISA.md` at the project
root for full criteria text.
