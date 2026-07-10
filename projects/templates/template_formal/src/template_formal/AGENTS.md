# `template_formal` — Agent Guide

The package root. Six subpackages — [`types/`](types/), [`storage/`](storage/),
[`protocol/`](protocol/), [`network/`](network/), [`agent/`](agent/),
[`colony/`](colony/) — each own exactly one concern the manuscript argues for.
See [`README.md`](README.md) for the responsibility table and the module-layout
diagram (reproduced from
[`manuscript/02_type_architecture.md`](../../manuscript/02_type_architecture.md)).

## Layer-dependency contract (enforce, don't just document)

```
types/    <- no internal deps
storage/  <- types/
protocol/ <- types/
network/  <- types/, protocol/ (errors only)
agent/    <- storage/, protocol/, types/
colony/   <- agent/, types/
```

Before adding an import between two subpackages, check this table. A new
edge not listed here (e.g. `colony/` importing `storage/` directly, bypassing
`Agent`) breaks the "every layer is exercised by the colony loop, never
bypassed" claim `manuscript/02_type_architecture.md`'s module-layout section
makes — that claim is a real dependency-graph fact this diagram encodes, not
decoration. `colony/nullmodel.py` is the one module that goes further and is
*tested* to avoid a dependency (see
`tests/colony/test_nullmodel.py::test_nullmodel_module_never_references_pheromone_field_or_agent_machinery`,
which greps the module's own source for `agent`/`pheromone` symbol names) —
that is a structural-isolation requirement for a null-model baseline to be a
valid comparison, not an accident of the table above.

## Where business logic may live

Per the repo's thin-orchestrator rule, **all** business logic for this
project lives under this package — `scripts/*.py` (see
[`../../scripts/AGENTS.md`](../../scripts/AGENTS.md)) only wires paths, I/O,
and printing. Notably `colony/demo.py` and `colony/visualization.py` were
*moved into* `src/` from `scripts/` specifically because figure construction,
empty-distribution guards, and simulation orchestration are business logic
(see both modules' docstrings) — don't reintroduce that logic into a script.

## Honesty-line discipline

Every subpackage's module docstring states, explicitly, which of its claims
`mypy --strict` proves (edit-time/CI-time only) versus which are
runtime-checked disciplines (a raised exception or a returned `Err`). When
adding a new type-safety claim to any module here, add the equivalent
sentence and, if the claim is checkable, a `tests/mypy_fixtures/bad_*.py` or
`good_*.py` fixture wired into `tests/test_mypy_oracle.py`'s
`_EXPECTED_BAD_FIXTURE_SUBSTRINGS` map — an unbound claim is not verified,
per this repo's Proof-of-Detection discipline. See
[`../../manuscript/02_type_architecture.md#sec:honesty-line`](../../manuscript/02_type_architecture.md)
for the canonical statement of every current claim's scope.

## See also

- [`../README.md`](../README.md) / [`../AGENTS.md`](../AGENTS.md) — the `src/`
  layer this package sits inside (src-layout rationale).
- [`../../tests/AGENTS.md`](../../tests/AGENTS.md) — how each subpackage is
  exercised (no-mocks policy, mypy-oracle harness, coverage gate).
- [`../../ISA.md`](../../ISA.md) — the full 92-ISC build history this
  package's docstrings cite by number (ISC-1..92).
