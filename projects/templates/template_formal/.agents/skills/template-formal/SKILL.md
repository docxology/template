---
name: template-formal
description: Strongly-typed multiagent ant-robot colony exemplar — ADTs, session-typed protocols, affine-discipline resource handles, storage-as-functor framing, Active-Inference-flavored decision loop, mypy-as-oracle negative controls.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, types, session-types, category-theory, active-inference, thin-orchestrator]
---

# template-formal

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_formal/`. Load this when working inside the
project.

## When to Use

- Working inside the `template_formal` exemplar — running scripts, editing
  `src/template_formal/`, or adding a new typed invariant.
- Forking this exemplar as the starting scaffold for a project whose research
  subject is illegal-state-unrepresentable design or a decentralized
  multiagent simulation.
- Adding a new strong-typing claim and needing the paired-proof pattern:
  every ADT/session-type/affine-handle claim needs both a
  `tests/mypy_fixtures/` negative-control fixture (mypy rejects the bad
  program) and a runtime unit test (the discipline actually raises).
- Validating that the exemplar's contracts (thin-orchestrator, zero-mock
  testing, no compile-time linear/dependent-type claims) still hold after
  changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_formal/tests --cov=projects/templates/template_formal/src --cov-fail-under=90
MYPYPATH=projects/templates/template_formal/src \
  uv run mypy --strict --explicit-package-bases --namespace-packages \
  projects/templates/template_formal/src
uv run python projects/templates/template_formal/scripts/02_run_analysis.py
uv run python scripts/pipeline/stage_03_render.py --project templates/template_formal
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_formal
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_formal

# Optional formal side-specs (non-default; require lake/elan + a Java runtime)
projects/templates/template_formal/scripts/check_formal_specs.sh
```

## Pitfalls

- **Never claim compile-time linear or dependent type guarantees.** Python
  has neither. Affine handles (`TransactionHandle`, protocol-phase objects)
  are a *runtime-guarded discipline* — they raise on reuse, they are not
  type-checked against reuse. Grep for `"dependent type"` and
  `"linear type"` outside the manuscript's explicit limitations/scoping
  section must return zero matches.
- **Every strong typing claim needs a paired proof.** A mypy-oracle
  negative-control fixture under `tests/mypy_fixtures/` proves what mypy
  --strict rejects; a runtime unit test proves what actually raises. One
  without the other is an unfalsifiable claim.
- **Keep scripts thin.** Business logic belongs in `src/template_formal/`,
  not in `scripts/`.
- **No mocks.** All tests use real on-disk SQLite files (`tmp_path`), a real
  in-process fault-injectable bus, and real `mypy --strict` subprocess
  invocations — never `MagicMock`/`unittest.mock`/`mocker.patch`.
- **No shared global state.** Each `Agent` owns exactly one on-disk database
  and one protocol endpoint; the colony coordinator only ever holds the
  public `Agent`/`PheromoneField` interfaces.
- **Formal side-specs are optional and must stay wired.** If `formal/lean/`
  or `formal/tla/` ship, they must be reachable from
  `scripts/check_formal_specs.sh` — never a vestigial, unwired file.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
