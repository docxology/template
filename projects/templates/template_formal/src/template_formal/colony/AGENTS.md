# `src/template_formal/colony/` — Agent Guide

Seven files, one distinct responsibility each — see `README.md`'s module
table before touching any of them; this package has grown across three
adversarial rounds and it is easy to put new logic in the wrong file.

**Contents.** `pheromone.py` (shared substrate + `Protocol`), `experiment.py`
(real-mechanism trial harness + the shared `find_sustained_consensus_tick`
consensus definition), `stats.py` (stdlib-only closed-form statistics),
`demo.py` (real simulation runners), `visualization.py` (optional matplotlib
figures), `nullmodel.py` (structurally-isolated random-choice baseline),
`sweep.py` (generic parameter-sweep runner).

**Contract.**

- New numeric config fields on `ColonyTrialConfig`/`NullModelTrialConfig` need
  a `__post_init__` guard at construction, matching the strictness of
  whatever they ultimately feed (e.g. `preference_variance` must be `> 0.0`,
  not `>= 0.0`, because `BeliefState.__post_init__` in `agent/agent.py`
  enforces the stricter bound — ISC-84 exists because these two guards once
  disagreed).
- `nullmodel.py` must never import `pheromone.py`, `agent/agent.py`, or
  `BeliefState` — that structural isolation is regression-tested by a
  source-grep + AST-import-allowlist pair (ISC-85), not just a docstring
  promise. If you need the null model to reference real colony machinery,
  that is a design change requiring a new ISC, not a quiet import.
- `sweep.py`'s `param_name` validation must stay bound to
  `ColonyTrialConfig`'s real dataclass field names (via `dataclasses.fields`),
  never a hardcoded string list — a typo'd or renamed field must fail loudly
  at sweep-construction time, not silently produce a `TypeError` deep inside
  `ColonyTrialConfig(**kwargs)`.
- Any new statistic in `stats.py` must be closed-form/stdlib-only (no
  numpy/scipy dependency) and pinned against a hand-computed expectation in
  `tests/colony/test_colony_stats_unit.py` — this package's whole statistical
  claim depends on every number being independently re-derivable by a reader
  with a calculator, not merely "matches what `scipy` would say."
- `demo.py`/`visualization.py` hold real simulation-runner and figure logic
  precisely *because* the thin-orchestrator rule forbids it in `scripts/` —
  do not migrate logic back into a `scripts/02_run_analysis.py`-style
  orchestrator (ISC-78).
- Any new pre-registered experiment quoting a rate must report its Wilson
  interval alongside the point estimate, unrounded, and pin the exact
  `successes` count in a regression test — see `test_colony_experiments_extended.py`
  for the pattern the pre-registered analyses already follow (ISC-87–ISC-113).

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
