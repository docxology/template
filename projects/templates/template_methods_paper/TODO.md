# template_methods_paper TODO

Forward-only integrity backlog for the methods-paper control-positive
exemplar. Keep this file focused on template status, not general feature
ideas.

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_methods_paper/tests --cov=projects/templates/template_methods_paper/src --cov-fail-under=90`
  — last full run: **90 passed, 0 failed, 99.01% coverage** (2026-08-02).
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_methods_paper --strict`
  — last run: **no drift detected** for this exemplar (2026-08-02). A
  repo-level `repo_docs_hardcoded_test_count` warning currently fires for
  `template_storybook/tests/AGENTS.md` (hardcoded '12 tests' from a prior
  commit); it is outside this exemplar's subtree and is tracked by the
  storybook lane.
- Code quality: `uv run ruff check projects/templates/template_methods_paper/src/` and `uv run mypy projects/templates/template_methods_paper/src/` must both pass clean — last run: **ruff clean, mypy clean (14 source files)** (2026-08-02).
- Prerender: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_methods_paper/manuscript --repo-root .`
  — last run: **no render-blocking pitfalls or undefined citations** (2026-08-02).
- Full pipeline (analysis → variables → render → validate → copy):
  **stage 02 3/3 scripts, stage 03 1/1 PDF (14 pages), stage 04 clean,
  stage 05 clean**; render log `^! ` count **0**, `??` count **0**
  (2026-08-02).
- Determinism: `tests/test_compiler.py::test_compile_method_is_deterministic` recompiles the same `Method` five times and asserts a single `plan_hash`.
- Coverage floor: ≥90% on `src/`; live test count and achieved coverage are tracked in `docs/_generated/COUNTS.md` (not hardcoded here).

## Pass log

- **2026-08-02 — publication pass (accuracy + full re-render).** Deep
  semantic review of manuscript prose vs `src/methods_dsl/` code and live
  outputs, doc-completeness sweep (all eight directory levels carry
  AGENTS.md + README.md; `.agents/` catalog matches the sibling
  `template-*` hyphenated convention), version-marker agreement
  (pyproject / config.yaml / CITATION.cff all 1.0.0; figure registry
  schema matches `src/figure_specs.py`), and a full canonical pipeline
  re-run. Fixed one prose inaccuracy: `04_conclusion.md` insight #3
  overclaimed that `SensorCalibrationSweep` "reuses every StepKind and
  Target" that `PBSPreparation` uses (the only shared kind is VALIDATE);
  rewrote it to the measured claim (no new StepKind/Target introduced for
  the second domain). All output artifacts regenerated from source; no
  `output/` files hand-edited.

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for
  methods-specification / controlled-procedure research projects.
- Keep every export and report artifact generated from
  `scripts/methods_analysis.py`, not hand-maintained `output/` snapshots.
- Keep `src/methods_dsl/` free of plotting and `infrastructure.*` imports
  except the one declared exception (`_logging.py`).

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize template
  with the same top-level sections as `config.yaml`, including the `project_config.dsl`
  block.
- Add any future controlled vocabulary (units, step kinds, targets) under
  `src/methods_dsl/units.py` / `vocabulary.py`, never as ad hoc YAML read
  from scripts — the vocabulary is the DSL's contract, not configuration.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name
  `templates/template_methods_paper`.
- Link any new public artifacts from README, AGENTS, and the generated
  exemplar roster rather than hardcoding paths.

## Test and validator gaps

- Add a negative control before widening claims beyond the two bundled
  worked examples (`PBSPreparation`, `SensorCalibrationSweep`).
- Add an exact-value assertion whenever a new step kind, unit, or gate is
  introduced.
- Keep `tests/conftest.py`'s invalid-method fixtures (dangling dependency,
  duplicate step id, unknown unit, cycle, target mismatch) in sync as the
  staged-gate surface grows.

## Ordered improvement ladder

1. Preserve the staged-gate-then-deterministic-compile contract (no gate
   reordering, no unhashed nondeterminism reaching `plan_hash`).
2. Add focused tests + a thin script export for any new step kind or
   exporter format.
3. Expand the worked examples or controlled vocabulary only with
   deterministic fixtures, exact-value tests, and documented claim
   boundaries.
4. Refresh generated docs after any public-surface change.
