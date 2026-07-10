# `src/template_formal/types/` — nominal IDs, the Result ADT, phantom phase markers

The shared type vocabulary every other module (`storage/`, `protocol/`,
`network/`, `agent/`, `colony/`) imports from. Nothing here touches SQLite,
sockets, or the filesystem — this package is pure typed data, at zero
runtime cost beyond what `uuid.UUID`/`dataclasses` already pay.

## Modules

| File | Responsibility |
| --- | --- |
| `ids.py` | `AgentId`, `MessageId`, `TxnId` — three `typing.NewType` wrappers over `uuid.UUID`, plus their `new_*_id()` constructors. |
| `result.py` | `Ok[T]`/`Err[E]` frozen dataclasses (the `Result[T, E]` tagged union) with a `Literal["ok","err"]` tag field, plus `is_ok`, `map_result`, `and_then`, `unwrap_or`. |
| `phase.py` | `Idle`, `Handshaking`, `Established`, `Closed` — zero-field phantom marker classes, plus the shared `PhaseT = TypeVar("PhaseT", ...)` bound to exactly those four. |

## Public API (`__init__.py`)

```python
from template_formal.types import (
    AgentId, MessageId, TxnId, new_agent_id, new_message_id, new_txn_id,
    Idle, Handshaking, Established, Closed, PhaseT,
    Ok, Err, Result, is_ok, map_result, and_then, unwrap_or,
)
```

## Core invariant

**Nominal IDs are a compile-time-only distinction.** `AgentId`, `MessageId`,
and `TxnId` are all `UUID` at runtime — `NewType` buys mypy --strict a
distinct nominal type it can reject mismatches against (ISC-1, ISC-2), but
`isinstance(agent_id, UUID)` is `True` for all three and nothing in this
module stops one from being handed where another is expected outside a
type-checked call site. See `ids.py`'s module docstring for the exact scope
of that claim, and `agent/agent.py`'s use of a `NewType`-wrapped `AgentId`
constructor argument (ISC-31) for the pattern extended one level further.

**`Result` recovers checked-exhaustiveness, not exceptions.** `Ok`/`Err` are
`frozen(slots=True)` dataclasses distinguished by a `Literal` tag; a
`match`/`case` that only handles `Ok` and falls through to
`typing.assert_never` is a real mypy --strict error (ISC-4), because the
un-narrowed `Err[...]` possibility still reaches the `Never`-typed argument.
This is Python's closest structural analogue to Haskell/OCaml sum-type
exhaustiveness — see `result.py`'s module docstring for what it does *not*
claim.

**Phase markers are phantom — never instantiated, zero runtime footprint.**
`Idle`/`Handshaking`/`Established`/`Closed` carry no fields; they exist
purely so a `Generic[PhaseT]` container (`protocol/session.py`'s
`SessionEndpoint[PhaseT]`) can bind to exactly one of them per concrete
class (ISC-6). **Only `protocol/session.py` currently binds `PhaseT`** —
`storage/transaction.py`'s `TransactionHandle` uses a structurally similar
but independent affine discipline (frozen + `__slots__` + a private
`_consumed` flag) that does **not** parameterize on `PhaseT`; the two
modules converge on the same *pattern* (typed handle + runtime consumed-flag
guard) without sharing this class hierarchy. Don't infer a `PhaseT` import
in `storage/` from ISC-6's phrasing — read `transaction.py` itself.

## Tests

Behavioral tests for this package live **flat at `tests/` root**, not under
a `tests/types/` subdirectory:

| Test file | Covers |
| --- | --- |
| `tests/test_types_ids.py` | `new_agent_id`/`new_message_id`/`new_txn_id` are real, unique `UUID` values (ISC-1). |
| `tests/test_types_result.py` | `Ok`/`Err` tag + payload, `is_ok`, `map_result` on both arms, `and_then` Kleisli composition, `unwrap_or` (ISC-3, ISC-5). |

`phase.py` has **no dedicated behavioral test file** — phantom markers carry
no runtime behavior to assert against. Its guarantee is proven instead via
`tests/mypy_fixtures/bad_phase_transition.py`, type-checked as a subprocess
by `tests/test_mypy_oracle.py` (ISC-18), and exercised indirectly by every
real phase transition in `tests/protocol/test_session.py`.

The nominal-ID distinction's negative control —
`tests/mypy_fixtures/bad_id_mixing.py` (ISC-2) — and the `Result`
exhaustiveness negative control — `tests/mypy_fixtures/bad_result_nonexhaustive.py`
(ISC-4) — are both type-checked by `tests/test_mypy_oracle.py`, which binds
each fixture to its own captured expected-error substring (ISC-72), not a
generic `"error:"` check.

## ISA cross-reference

ISC-1 through ISC-7. See `ISA.md` at the project root for full criteria text.
