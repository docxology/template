# `src/template_formal/types/` — Agent Guide

The shared nominal-ID / `Result` ADT / phantom-phase-marker vocabulary every
other package imports. Pure typed data, zero I/O — see `README.md` for the
full contract.

**Contents.** `ids.py` — `AgentId`/`MessageId`/`TxnId` `NewType`s + `new_*_id()`.
`result.py` — `Ok`/`Err`/`Result` + `is_ok`/`map_result`/`and_then`/`unwrap_or`.
`phase.py` — `Idle`/`Handshaking`/`Established`/`Closed` phantom markers + `PhaseT`.

**Contract.** `NewType` distinctions (`AgentId` vs `MessageId` vs `TxnId`) are
edit-time/CI-time only — never claim or rely on a runtime distinction; they
are all bare `UUID` at runtime. Never add an `Any` or an unjustified
`# type: ignore` to this package (ISC-7 anti-criterion). A `match` over
`Result` must stay exhaustive — adding a third arm to the union means
updating every `assert_never`-terminated `match` in this package and its
consumers. `phase.py`'s markers are never instantiated; if you add a fifth
marker, it must be added to `PhaseT`'s `TypeVar` bound and to every
`Generic[PhaseT]` consumer's phase-transition surface (`protocol/session.py`)
in the same change, not left to drift.

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
