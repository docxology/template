# template_methods_paper TODO

Forward-only integrity backlog for the methods-paper control-positive
exemplar. Keep this file focused on template status, not general feature
ideas.

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_methods_paper/tests --cov=projects/templates/template_methods_paper/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_methods_paper/src/` and `uv run mypy projects/templates/template_methods_paper/src/` must both pass clean.
- Determinism: `tests/test_compiler.py::test_compile_method_is_deterministic` recompiles the same `Method` five times and asserts a single `plan_hash`.
- Coverage floor: ≥90% on `src/`; live test count and achieved coverage are tracked in `docs/_generated/COUNTS.md` (not hardcoded here).

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
