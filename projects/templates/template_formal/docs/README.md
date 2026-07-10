# `template_formal` Documentation

A strongly-typed, decentralized multiagent ant-robot colony exemplar:
algebraic data types, nominal `NewType` identifiers, session-typed protocol
state machines, and affine-discipline resource handles, applied to a
genuinely decentralized domain — each agent owns its own on-disk SQLite
database and its own in-process, fault-injectable network endpoint, no
shared global state. The colony layer on top adds a real, falsifiable
scientific claim: a stigmergic (pheromone-mediated) consensus mechanism,
statistically validated against a random-choice null model and three
pre-registered experiments.

If you are new here, read these in order.

## Guides

| Guide | Read it to learn |
| --- | --- |
| [`architecture.md`](architecture.md) | The two-layer + thin-orchestrator design as applied here: `types → {storage, protocol, network} → agent → colony`, the `colony/` subpackage's internal breakdown, and the manuscript/scripts/tests relationship. |
| [`type_system_guide.md`](type_system_guide.md) | The concrete strong-typing vocabulary (ADTs, nominal IDs, session types, affine handles), the honesty line between what `mypy --strict` proves and what is a runtime discipline, and the mypy-oracle fixture convention. |
| [`formal_methods_guide.md`](formal_methods_guide.md) | What the optional Lean 4 + TLA+ side-specs actually prove/check, how to run `scripts/check_formal_specs.sh`, and the near-vacuity lesson this template learned twice. |
| [`statistics_methodology_guide.md`](statistics_methodology_guide.md) | The stdlib-only statistics in `colony/stats.py` and the pre-registered-hypothesis discipline the three real experiments follow — with a recipe for adding a fourth. |
| [`security_guide.md`](security_guide.md) | The checksum-pinned `tla2tools.jar` fetch, construction-time SQL-identifier validation, and the numeric-boundary-consistency fixes — with real file:line citations and a checklist for a new validated field. |
| [`testing_guide.md`](testing_guide.md) | The test suite structure, the no-mocks policy, the 90% coverage gate, the mypy-oracle harness, and honest `pytest-xdist` parallelization notes. |

## Source-of-truth files

These are the artifacts the guides keep pointing back to:

- [`src/template_formal/`](../src/template_formal) — the typed domain code
  (`types/`, `storage/`, `protocol/`, `network/`, `agent/`, `colony/`). No
  `infrastructure` imports anywhere in this package (see
  [`AGENTS.md`](../AGENTS.md)'s Layer contract).
- [`formal/`](../formal) — the optional Lean 4 + TLA+ side-specs, wired to
  [`scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh).
- [`manuscript/`](../manuscript) — the prose argument, citing real ISC
  numbers and real numbers from pinned regression tests.
- [`tests/`](../tests), including
  [`test_mypy_oracle.py`](../tests/test_mypy_oracle.py) and
  [`mypy_fixtures/`](../tests/mypy_fixtures) — the full suite, zero mocks.
- [`ISA.md`](../ISA.md) — the full Ideal-State Artifact: every ISC, the
  adversarial-round Decisions/Changelog history, and the Verification
  trail this documentation cites from.

## Honesty line in one screen

`mypy --strict` proves an `AgentId` cannot be passed where a `MessageId`
is expected, that a non-exhaustive `Result` match is rejected, that an
`Established`-only method cannot be called on an `Idle`-phase handle, and
that a bare `str`/`UUID` cannot construct an `Agent` — each backed by a
real `mypy --strict` subprocess run against a fixture in
`tests/mypy_fixtures/`. Reusing a consumed `TransactionHandle` or protocol
phase, and detecting malformed wire bytes, are **runtime disciplines**,
not compiler guarantees — Python has no linear/affine type system, and no
line in this template's source or manuscript claims otherwise. The full,
claim-by-claim scoping lives in
[`manuscript/02_type_architecture.md`](../manuscript/02_type_architecture.md)'s
"What mypy --strict proves vs. what is a runtime discipline" section and
is restated practically in the [type system guide](type_system_guide.md).

## Tooling

All commands use `uv` (never `pip`/`npm`). From the repository root:
`uv run python scripts/pipeline/stage_01_test.py --project
templates/template_formal --project-only` is the authoritative test +
coverage gate (see the [testing guide](testing_guide.md) for why a bare
root-venv `pytest` is not equivalent). The optional formal side-specs run
via `uv run bash projects/templates/template_formal/scripts/check_formal_specs.sh`
— see the [formal methods guide](formal_methods_guide.md).
