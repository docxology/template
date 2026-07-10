# `src/template_formal/network/` — Agent Guide

The in-process, seeded-fault-injectable message bus. No real sockets — see
`README.md` for the full contract.

**Contents.** `bus.py` — `InProcessBus[MsgT]`, `FaultConfig`, `FaultInjector`,
`UnknownEndpointError`.

**Contract.** `send()`/`try_recv()` always round-trip through `encode`/`decode`
to real `bytes` — never hand a message across as a bare Python object
reference. Fault injection is deterministic: build `FaultInjector` from a
`FaultConfig(seed=...)` and the exact same `seed` reproduces the exact same
drop/duplicate/corrupt/reorder sequence. Do not add a fault mode that isn't
independently toggleable via its own `FaultConfig` field, and do not enable a
mode by default in a way that would make the paired negative-control test
(`tests/network/test_handshake_over_bus.py`) vacuously pass on an all-happy
path (ISC-68).

`UnknownEndpointError` is reserved for wiring bugs (unregistered `AgentId`) —
never repurpose it for an expected network fault; expected faults are always
either silent (drop) or a decode-side `Result.Err`.

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
