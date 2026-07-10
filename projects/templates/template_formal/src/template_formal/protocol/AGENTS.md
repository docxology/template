# `src/template_formal/protocol/` — Agent Guide

The session-typed handshake/data-transfer state machine and its real-bytes
wire format. No transport of its own — the network bus (`network/bus.py`)
carries the `bytes` this package encodes/decodes. See `README.md` for the
full contract.

**Contents.** `session.py` — `SessionEndpoint[PhaseT]` +
`IdleSession`/`HandshakingSession`/`EstablishedSession`/`ClosedSession`,
`WireMessage`, `encode_wire_message`/`decode_wire_message`,
`SessionConsumedError`. `errors.py` — `ProtocolViolation`,
`MalformedMessage`.

**Contract.** A phase-specific method must be defined **only** on the phase
class it's legal for — never add `send`/`receive` to `IdleSession` or
`HandshakingSession` as a no-op/raising stub; the whole point is that mypy
--strict rejects the call because the method doesn't exist there (ISC-18).
Every transition method (`open`, `accept_hello`, `complete`, `close`) must
check its private `_consumed` flag and raise `SessionConsumedError` before
doing anything else, and must set the flag before, not after, its side
effect. Expected protocol/wire failures (wrong kind, wrong sender, malformed
bytes) return `Result.Err` — never raise; `SessionConsumedError` is the one
reserved exception, for genuine affine-reuse misuse only. Wire encode/decode
must stay a real `bytes` round trip with an integrity check over the whole
frame — don't pass `WireMessage` objects by reference anywhere fault
injection needs to corrupt them; the CRC32 trailer is what makes corruption
detectable rather than merely typed. Every new happy-path protocol test
needs a paired fault-injected negative control (ISC-25) — add it to
`tests/network/test_handshake_over_bus.py`, not just `tests/protocol/`.

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
