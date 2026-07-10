# Type System Guide

This template's research subject *is* its type architecture. This guide is
for someone extending it with a new typed invariant — it restates the
vocabulary practically and pins down the one distinction the whole
manuscript is built on: what `mypy --strict` actually proves versus what is
a runtime-guarded discipline that only looks similar in prose.

## The vocabulary, by file

| Pattern | File | What it demonstrates |
| --- | --- | --- |
| Nominal IDs | [`types/ids.py`](../src/template_formal/types/ids.py) | `AgentId`/`MessageId`/`TxnId` as distinct `NewType` wrappers over `uuid.UUID` — identical at runtime, distinct to `mypy --strict`. |
| ADT / tagged union | [`types/result.py`](../src/template_formal/types/result.py) | `Result[T, E]` as `Ok[T]`/`Err[E]` frozen dataclasses with a `Literal["ok"\|"err"]` tag; `match`-exhaustiveness enforced via `typing.assert_never` in the default arm. |
| Phantom phase markers | [`types/phase.py`](../src/template_formal/types/phase.py) | `Idle`/`Handshaking`/`Established`/`Closed`, zero-field classes that exist only in type position (`Generic[PhaseT]`), never instantiated. |
| Session types | [`protocol/session.py`](../src/template_formal/protocol/session.py) | Four separate classes, one per phase; phase-specific methods (`send`/`receive`) exist **only** on `EstablishedSession` — calling them on the wrong phase is `AttributeError` under mypy, not a caught exception. |
| Affine-discipline handles | [`storage/transaction.py`](../src/template_formal/storage/transaction.py) | `TransactionHandle` — frozen + `__slots__`, a private `_consumed` flag checked and raised (`ConsumedHandleError`) on every consuming call. |
| Storage-as-functor framing | [`storage/schema.py`](../src/template_formal/storage/schema.py) | `Column`/`TableSchema` framed as a functor `Schema -> Set` (Fong & Spivak) — an explicitly-stated design lens, not a machine-checked proof. |
| Structural `Protocol` conformance | [`colony/pheromone.py`](../src/template_formal/colony/pheromone.py) | `PheromoneField` as a narrow three-method `Protocol`; `InMemoryPheromoneField` satisfies it structurally, not by inheritance. |

## The honesty line: what mypy --strict proves vs. what is a runtime discipline

This is [`manuscript/02_type_architecture.md`](../manuscript/02_type_architecture.md)'s
central claim, restated as a practical checklist. Before you add a new
"illegal state unrepresentable" claim to this template, work out which
column it belongs in — both require a paired test, but a different kind.

**Proved by mypy --strict (edit-time/CI-time only — never a runtime
guarantee):**

- An `AgentId` cannot be passed where a `MessageId` is expected
  (`tests/mypy_fixtures/bad_id_mixing.py`).
- A `match` over `Result` that omits the `Err` arm is rejected via
  `assert_never` (`tests/mypy_fixtures/bad_result_nonexhaustive.py`).
- An `Established`-only method cannot be called on an `Idle`-phase handle
  (`tests/mypy_fixtures/bad_phase_transition.py`).
- A `TransactionHandle`'s isolation level cannot be constructed from an
  arbitrary string outside `Literal["deferred", "immediate", "exclusive"]`
  (`tests/mypy_fixtures/bad_isolation_level.py`).
- An `Agent` cannot be constructed from a bare `str`/`UUID` in place of an
  `AgentId` (`tests/mypy_fixtures/bad_agent_id_construction.py`).
- An object that almost, but not quite, conforms to `PheromoneField`
  cannot be assigned to a `PheromoneField`-typed variable
  (`tests/mypy_fixtures/bad_pheromone_protocol_violation.py`).

**Runtime disciplines only — not type-checker guarantees:**

- Reusing a consumed `TransactionHandle` (`.commit()` twice, or after
  `.rollback()`) is not ill-typed; a private `_consumed` flag raises
  `ConsumedHandleError`.
- Reusing a consumed protocol-phase instance (`.open()` twice on the same
  `IdleSession` without reassignment) is not ill-typed either; a runtime
  consumed-flag check raises `SessionConsumedError`.
- Malformed bytes arriving at the wire boundary
  (`decode_wire_message`/`network/bus.py`'s corrupt fault mode) are
  detected only at runtime, returning `Result.Err(MalformedMessage(...))`
  — no static type system can characterize the well-formedness of bytes
  from outside the type-checked program.

No sentence in this template's source or manuscript should ever claim
Python enforces compile-time linear/affine or dependent-type discipline.
`ISC-44`'s anti-criterion is a literal grep for the strings `"dependent
type"`/`"linear type"` outside the explicitly-scoped limitations section —
keep it that way.

## Adding a new typed invariant: the paired-proof pattern

Every strong claim in this template follows the same shape. To add one:

1. **Static half, if the type system can actually enforce it.** Write the
   illegal-state-triggering code as a new `tests/mypy_fixtures/bad_<name>.py`
   fixture with a one-line docstring naming the exact `mypy --strict` error
   you expect. Add its exact expected substring to
   `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` in
   [`tests/test_mypy_oracle.py`](../tests/test_mypy_oracle.py) — this is
   the one part of adding a bad fixture that is **not** auto-discovered
   (see below); a missing entry fails loudly with `KeyError` rather than
   silently passing under a generic `"error:"` check.
2. **Dynamic half, if the invariant also needs a runtime guard** (anything
   affine — a handle or phase object that can be reused after
   consumption). Add the `_consumed`/similar flag to the frozen dataclass,
   raise a dedicated exception (not a bare `RuntimeError`) on reuse, and
   write a unit test that actually triggers the raise via `pytest.raises`.
3. **If the invariant is a generic/`Protocol` binding `src/` never
   instantiates concretely** — e.g. a new `Generic[StateT]` class, or a
   new `Protocol` some concrete class is supposed to satisfy — add a
   `tests/mypy_fixtures/good_<name>.py` positive-control fixture that
   actually performs that concrete instantiation/assignment. This category
   exists because a `src/`-only mypy gate is structurally blind to a
   binding that only ever happens in `tests/`: an earlier revision of
   `GaussianBelief` declared `mean`/`variance` as plain mutable attributes,
   which a `frozen=True` dataclass can never satisfy, and the `src/`-only
   gate reported zero errors the whole time because `src/` itself never
   instantiates `Agent` with a concrete type argument (see
   [`manuscript/05_results_discussion.md`](../manuscript/05_results_discussion.md)'s
   "mypy-as-oracle proof-of-detection" section for the full story). Fixed
   by `tests/mypy_fixtures/good_agent_belief_instantiation.py`, which
   type-checks `Agent[BeliefState]` itself as a permanent regression
   guard.

## The mypy-oracle harness's auto-discovery convention

[`tests/test_mypy_oracle.py`](../tests/test_mypy_oracle.py) discovers
fixtures by filename glob, not a hardcoded list, but the two prefixes are
**not** symmetric:

- `good_*.py` is fully zero-edit: drop the file under
  `tests/mypy_fixtures/`, and `_good_fixtures()`'s glob picks it up on the
  next run, asserting `mypy --strict` exits zero.
- `bad_*.py` is discovered the same way but is **not** zero-edit: you must
  also add its filename → expected-error-substring entry to
  `_EXPECTED_BAD_FIXTURE_SUBSTRINGS`. This is deliberate: a generic
  `"error:" in result.stdout` check is a hollow gate — if a fixture's
  intended illegal state stopped triggering (an unrelated edit to the
  fixture, or a `src/` refactor that changes which line fails first) but
  mypy still emitted *some* unrelated error, a substring-free check would
  keep reporting green for the wrong reason.

Name the file `bad_<invariant>.py` or `good_<invariant>.py`, one file per
invariant — the prefix is what the two globs in `test_mypy_oracle.py` key
on. See the [testing guide](testing_guide.md) for how this harness fits
into the rest of the suite.
