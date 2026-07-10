# `tests/mypy_fixtures/` — the mypy-as-oracle fixture corpus

Every claim in this template's `ISA.md` of the form "mypy --strict rejects
X" is worthless until something in this session actually invokes
`mypy --strict` and watches it reject `X`. That proof-of-detection harness
lives in [`../test_mypy_oracle.py`](../test_mypy_oracle.py); this directory
holds the fixtures it type-checks. Nothing here is ever imported or
executed by pytest — every fixture is a standalone `.py` file that only
ever passes through `mypy --strict --explicit-package-bases
--namespace-packages` as a subprocess target.

## Naming convention

`test_mypy_oracle.py` auto-discovers fixtures by glob, not by an explicit
list — adding a correctly-named file is enough to bring it under test:

| Pattern | Discovered by | Must... |
| --- | --- | --- |
| `bad_*.py` | `_bad_fixtures()` (`glob("bad_*.py")`) | make `mypy --strict` **exit non-zero**, with stdout containing a specific, hand-captured error substring |
| `good_*.py` | `_good_fixtures()` (`glob("good_*.py")`) | make `mypy --strict` **exit 0** (positive-control regression guard) |

A `bad_*.py` fixture with no entry in `test_mypy_oracle.py`'s
`_EXPECTED_BAD_FIXTURE_SUBSTRINGS` dict is deliberately **not** a silent
pass — the test raises `KeyError` the moment mypy runs, forcing whoever
added the fixture to capture its real error text and bind it into the dict
(see that file's module docstring for why a generic `"error:" in stdout`
check would be a hollow gate).

## Current fixtures and their bound invariant

| File | ISC | Claim it proves | Bound error substring (from `_EXPECTED_BAD_FIXTURE_SUBSTRINGS`) |
| --- | --- | --- | --- |
| `bad_id_mixing.py` | ISC-2 | An `AgentId` cannot be passed where a `MessageId` is expected — distinct `NewType`s over the same runtime `UUID` are not interchangeable to mypy. | `Argument 1 to "wants_a_message_id" has incompatible type "AgentId"; expected "MessageId"` |
| `bad_result_nonexhaustive.py` | ISC-4 | A `match` over `Result[int, str]` that handles only `Ok` and falls through to `assert_never` is rejected — the un-narrowed `Err[str]` possibility still reaches the call site. | `Argument 1 to "assert_never" has incompatible type "Err[str]"; expected "Never"` |
| `bad_isolation_level.py` | ISC-15 | `open_database(..., isolation_level=...)` rejects an arbitrary `str`; only the three-member `Literal` is accepted. | `Argument "isolation_level" to "open_database" has incompatible type "str"; expected "Literal['deferred', 'immediate', 'exclusive']"` |
| `bad_phase_transition.py` | ISC-18 | `IdleSession` has no `send` method at all — it is genuinely absent from the class, not merely guarded — so calling it is a static, not a runtime, error. | `"IdleSession" has no attribute "send"` |
| `bad_pheromone_protocol_violation.py` | ISC-32 | A class whose `deposit` requires an extra non-default `note` argument does not structurally satisfy the `PheromoneField` `Protocol`, because a caller holding the narrow `PheromoneField` type could never supply it. | `Incompatible types in assignment (expression has type "_BrokenPheromoneField", variable has type "PheromoneField")` |
| `bad_agent_id_construction.py` | ISC-31 | `Agent(...)` rejects a bare `uuid4()` return value; only an `AgentId`-wrapped `UUID` type-checks, even though both are `UUID` at runtime. | `Argument 1 to "Agent" has incompatible type "UUID"; expected "AgentId"` |
| `good_agent_belief_instantiation.py` | (regression guard) | `Agent[BeliefState]` — and a `list[Agent[BeliefState]]` — must keep type-checking. Added after a prior revision broke this and a `src/`-only mypy run stayed blind to it, because `src/` itself never instantiates `Agent[StateT]` with a concrete type argument (Forge cross-vendor audit, CRITICAL-1; see `ISA.md` Changelog). | n/a (must exit 0) |
| `good_bus_wire_message_instantiation.py` | ISC-20 / ISC-26 | `InProcessBus[WireMessage]`, bound to `encode_wire_message`/`decode_wire_message`, must keep type-checking. `src/` never instantiates `InProcessBus[MsgT]` concretely either — every real binding lives in `tests/network/`, which the mypy oracle never scans — so this is the permanent guard against the same class of blind spot recurring here. | n/a (must exit 0) |
| `good_pheromone_conformance.py` | ISC-32 | `InMemoryPheromoneField` assigned to a `PheromoneField`-typed variable must keep type-checking — the positive control paired with `bad_pheromone_protocol_violation.py`, covering the same `src/`-blind-spot class (real assignment only lives in `tests/colony/`). | n/a (must exit 0) |

## Why paired positive controls exist at all

The three `good_*.py` fixtures are not decorative symmetry. Each one binds
a generic instantiation or structural-conformance shape that `src/` itself
never exercises concretely — `Agent[StateT]`, `InProcessBus[MsgT]`, and
`PheromoneField`'s structural `Protocol` are all only ever bound to a
concrete type argument inside `tests/`. A `src/`-only mypy gate
(`test_real_src_tree_passes_mypy_strict_clean`) is structurally blind to a
break in any of those bindings; the `good_*.py` fixtures are the permanent
regression guard closing that gap. `good_agent_belief_instantiation.py`
exists because exactly this blind spot broke once already (a prior
revision of the belief-state type wasn't frozen-dataclass-compatible) and
went undetected until a cross-vendor audit caught it.

## What the harness does not claim

Passing this suite proves mypy currently rejects each `bad_*.py` shape and
currently accepts each `good_*.py` shape, on the mypy version pinned in
this workspace. It does not prove runtime enforcement — Python has no
compiler to stop a caller from bypassing the type checker entirely (an
untyped boundary, a `# type: ignore`, `**kwargs`, ...). Where that matters,
the corresponding runtime guard is tested elsewhere and cross-referenced —
e.g. `bad_isolation_level.py`'s static claim is paired with
`tests/storage/test_storage_db.py::test_open_database_rejects_invalid_isolation_level_at_runtime`,
and `bad_agent_id_construction.py`'s with
`tests/agent/test_agent_isolation.py::test_agent_construction_rejects_non_uuid_agent_id_at_runtime`.

## Running it

```bash
uv run pytest projects/templates/template_formal/tests/test_mypy_oracle.py -v
```

Each fixture spawns its own `mypy --strict` subprocess (one per
parametrized test id), plus one run against the whole `src/` tree — this
is the slowest file per-test in the suite by subprocess-spawn overhead, but
each individual `mypy` invocation completes in well under a second on a
single small file.
