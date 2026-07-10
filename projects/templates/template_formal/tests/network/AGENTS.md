# `tests/network/` — Agent Guide

Tests `src/template_formal/network/bus.py`. See [`README.md`](README.md)
for the full test breakdown.

## Contract

- **Speed:** fast. Everything is in-process and seeded — no sockets, no
  files, bounded message counts and `max_ticks`. Should stay well under a
  second for the whole directory. If a change makes this directory slow,
  something has leaked real I/O or an unbounded loop into what's supposed
  to be a pure in-process bus.
- **No real sockets, ever.** Per `../../ISA.md`'s Out of Scope, this
  directory (and the module it tests) must never import `socket`,
  `asyncio` networking primitives, or any message-broker client. The bus
  is an in-process, fault-injectable substitute; keep it that way.
- **A new fault mode needs the ISC-68 anti-vacuity pairing.** Don't just
  add a config flag and a test that it "runs" — prove the fault actually
  fires at `probability=1.0` (or equivalent), and prove it's a no-op when
  disabled by default, mirroring the existing drop/duplicate/corrupt/
  reorder tests in `test_bus.py`.
- **Every ISC-16..26 phase-transition invariant needs a fault-injected
  pairing here, not just a clean-path test in `../protocol/`.** ISC-25 is
  explicit: no phase transition may be proven only on the happy path.
  `test_handshake_over_bus.py`'s `_drive_handshake` is the shared driver —
  extend it rather than writing a second, divergent handshake driver.
- **Determinism claims must include an anti-vacuity check.** If you assert
  "same seed → same sequence," also assert the sequence isn't a trivial
  constant (see `test_fault_injector_determinism_same_seed_same_sequence`'s
  `True in flattened` / `False in flattened` check) — otherwise an
  injector that always returns `False` would pass the determinism
  assertion for the wrong reason.

## Running just this directory

```bash
uv run pytest projects/templates/template_formal/tests/network/ -v
```
