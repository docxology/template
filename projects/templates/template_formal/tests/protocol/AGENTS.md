# `tests/protocol/` — Agent Guide

Tests `src/template_formal/protocol/{session,errors}.py`. See
[`README.md`](README.md) for the full test breakdown.

## Contract

- **Speed:** fast. Pure in-process objects and `bytes` — no I/O. Should
  stay well under a second for the whole directory.
- **A new phase or phase-transition method needs three things, not one:**
  1. A test proving the happy-path transition returns the correct next
     phase (and, where applicable, the correct outgoing `WireMessage`).
  2. A test proving the runtime `SessionConsumedError` fires on a second
     call to the same instance (ISC-19's dynamic half).
  3. A static negative-control fixture in `../mypy_fixtures/bad_*.py`
     proving mypy rejects calling a *different* phase's method on this
     one (ISC-19's static half) — add its expected error substring to
     `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` in `../test_mypy_oracle.py`.
- **No happy-path-only phase invariant.** ISC-25 is an anti-criterion: a
  new phase-transition test that only exercises success, with no paired
  rejection test proving a `ProtocolViolation` (wrong kind, wrong sender,
  or otherwise), is an incomplete pair, not a finished one.
- **The wire format is real bytes, not object identity.** If you touch
  `encode_wire_message`/`decode_wire_message`, keep every existing
  corruption test's isolation property: each corruption test recomputes
  the CRC32 trailer over its own corrupted body so it only fires the one
  check it's named for (magic bytes, kind code, length field) — don't let
  a new "combined" corruption slip past this isolation.
- **End-to-end, fault-injected exercises of this state machine live in
  `../network/`, not here.** This directory tests the state machine in
  isolation (no bus, no fault injection); `../network/test_handshake_over_bus.py`
  is where the same phase transitions get driven through a real,
  fault-injectable `InProcessBus`. Don't duplicate bus-level concerns here.

## Running just this directory

```bash
uv run pytest projects/templates/template_formal/tests/protocol/ -v
```
