# `tests/colony/` — Agent Guide

Tests `src/template_formal/colony/{pheromone,experiment,nullmodel,sweep,
stats,demo,visualization}.py`. See [`README.md`](README.md) for the full,
per-file test breakdown.

## Speed profile — read this before running the whole suite locally

**Nine of eleven files here are fast** (unit tests, or fixed-scale
integration with at most a few dozen real trials). **Two are slow:**
`test_colony_convergence_statistics.py` (~9s locally, 220 real trials) and
`test_colony_experiments_extended.py` (~49s locally, 900 real trials across
three `scope="module"` fixtures). These two are the largest single
contributors to this project's total test wall-clock time — see
`../AGENTS.md` for the repo's parallel test-execution guidance and factor
these two files in explicitly when deciding worker counts or which subset
to run for a fast local iteration loop (`pytest tests/colony/ -k "not
experiments_extended and not convergence_statistics"` is the quick way to
skip both while iterating on the fast eight).

## Contract

- **Pre-registered means pre-registered.** `test_colony_experiments_extended.py`'s
  three hypotheses and falsification criteria are documented *before* the
  numeric result, both in the module docstring and in
  `manuscript/05_results_discussion.md`. If you change the mechanism in a
  way that changes these numbers, update the hypothesis's stated
  falsification criterion and the manuscript prose together with the
  pinned counts — do not silently re-pin the numbers without revisiting
  whether the original claim still holds.
- **Every pinned success count is fully deterministic, not
  "statistically similar."** These tests use fixed seed sequences; a
  changed count here means the mechanism actually changed, not that the
  test is flaky. Do not loosen a pinned-count assertion to a tolerance
  range to make a real regression pass.
- **New experiments need all three honesty guards
  `test_colony_convergence_statistics.py` already sets the bar for:** a
  heterogeneity/non-vacuity check that the varied input actually varies,
  a negative control reproducing a known-deterministic baseline through
  the same harness, and a positive-control-that-can-fail proving the gate
  isn't vacuously satisfiable. A new statistical claim without an
  accompanying "what would make this claim false, and did we check"
  guard is incomplete.
- **`scope="module"` fixtures exist to avoid re-running expensive trial
  batches per test.** If you add a test that needs the same batch another
  test in the file already computed, consume the existing fixture — don't
  add a second, near-duplicate trial run.
- **`Agent`'s and `PheromoneField`'s public surfaces are pinned as exact
  sets** in `test_colony_integration.py`. Adding or removing a public
  method on either class requires updating that set here as well as in
  `../agent/AGENTS.md`'s cross-referenced isolation tests.
- **`nullmodel.py` must stay structurally incapable of reading the
  pheromone field or the free-energy decision loop** — not merely avoid
  doing so in the current implementation. `test_nullmodel.py` enforces
  this via a real source-text grep and a real AST import walk, not a
  docstring promise; if you need the null model to reference something
  new, update the `allowed` import set in that test deliberately, with a
  comment explaining why the isolation boundary still holds.
- **`_SWEEPABLE_FIELD_NAMES` in `colony/sweep.py` must track
  `ColonyTrialConfig`'s real dataclass fields minus `seed`.**
  `test_sweep.py::test_sweepable_field_names_matches_colonytrialconfig_fields_minus_seed`
  derives this from `dataclasses.fields()` directly — a new config field
  is automatically sweepable unless explicitly excluded; don't hand-list
  field names anywhere that could drift from the real dataclass.

## Running

```bash
# Everything (includes the two slow files)
uv run pytest projects/templates/template_formal/tests/colony/ -v

# Fast subset only, for a quick local iteration loop
uv run pytest projects/templates/template_formal/tests/colony/ -v \
  -k "not experiments_extended and not convergence_statistics"
```
