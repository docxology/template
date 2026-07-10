# `template_formal/docs/` — Agent Guide

Documentation set for the **strongly-typed multiagent ant-robot colony**
exemplar. `src/template_formal/` is pure typed domain code (no
`infrastructure` imports); the colony layer adds a real, falsifiable
scientific claim on top of the type architecture.

## Read order

| Doc | Purpose |
| --- | --- |
| [`README.md`](README.md) | Human entry point + guide index |
| [`architecture.md`](architecture.md) | Two-layer + thin-orchestrator design as applied here: `types → {storage, protocol, network} → agent → colony` |
| [`type_system_guide.md`](type_system_guide.md) | The strong-typing vocabulary; the mypy-proves-vs-runtime-discipline line; the mypy-oracle fixture convention |
| [`formal_methods_guide.md`](formal_methods_guide.md) | Lean 4 + TLA+ side-specs: what they check, how to run them, the near-vacuity lesson |
| [`statistics_methodology_guide.md`](statistics_methodology_guide.md) | `colony/stats.py`; the pre-registered-hypothesis discipline; adding a fourth experiment |
| [`security_guide.md`](security_guide.md) | Checksum-pinned jar fetch, SQL-identifier validation, numeric-boundary-consistency fixes; checklist for a new validated field |
| [`testing_guide.md`](testing_guide.md) | Suite structure, no-mocks policy, 90% coverage gate, mypy-oracle harness, `pytest-xdist` notes |

## Contracts agents must honor

- **`src/template_formal/` imports no `infrastructure`.** The typed domain
  code is forkable standalone — see the [project `AGENTS.md`](../AGENTS.md)'s
  Layer contract table. `scripts/` and `formal/`'s wiring script may import
  `infrastructure`/`src`; the domain package itself never does.
- **Every strong typing claim needs a paired proof**, not just a docstring:
  a `mypy --strict` negative-control fixture (`tests/mypy_fixtures/bad_*.py`)
  where the type system can genuinely reject it, and/or a runtime-raise
  unit test where it's an affine/runtime discipline instead. See the
  [type system guide](type_system_guide.md)'s paired-proof pattern.
- **No compile-time linear/affine/dependent-type claim anywhere.** Python
  has neither. A grep for `"dependent type"`/`"linear type"` outside the
  manuscript's explicit non-claim paragraph must return zero matches
  (ISC-44).
- **Zero mocks; real everything.** Real on-disk SQLite (`tmp_path`), real
  in-process fault injection, real `mypy --strict` subprocess calls — never
  `MagicMock`/`mocker.patch`/`unittest.mock`.
- **Every new ISC goes into `ISA.md` before the code that satisfies it** —
  the manuscript cites specific ISC numbers, so a change without one has
  no stable identifier to point at. Append, never renumber.
- **A statistical claim needs its falsification criterion stated before
  the result**, and a Wilson interval (or Fisher's exact test near a 0%/100%
  boundary) alongside every rate — see the
  [statistics methodology guide](statistics_methodology_guide.md).
- **A new validated numeric/string field mirrors the existing
  `__post_init__` pattern** (`Column`/`TableSchema`, `IsolationLevel`,
  `ColonyTrialConfig`, `BeliefState`) and checks every other constructor of
  the same underlying value for a boundary mismatch — see the
  [security guide](security_guide.md)'s checklist.

## Status

This exemplar is a **tracked public canonical project** (see
[`docs/_generated/active_projects.md`](../../../../docs/_generated/active_projects.md)).

## See also

- [`../AGENTS.md`](../AGENTS.md) — project map, Layer contract, mypy-oracle
  fixture protocol, anti-patterns
- [`../ISA.md`](../ISA.md) — the full Ideal-State Artifact: every ISC, the
  adversarial-round Decisions/Changelog history, and Verification trail
- [`../manuscript/`](../manuscript) — the rendered argument these guides
  summarize practically for an extending agent
