# template_eda_notebook TODO

Forward-only integrity backlog for the exploratory-data-analysis
control-positive exemplar. Keep this file focused on template status, not
general feature ideas.

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_eda_notebook/tests --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_eda_notebook/src/` and `uv run mypy projects/templates/template_eda_notebook/src/` must both pass clean.
- Notebook binding: `tests/test_notebook.py` checks the walkthrough is valid nbformat, binds to `src.__all__`, and carries no logic in cells.
- Coverage floor: ≥90% on `src/`; live test count and achieved coverage are tracked in `docs/_generated/COUNTS.md` (not hardcoded here).

### 2026-08-02 publication pass (measured, as observed)

- Project suite: **66 passed, 0 failed, 0 skipped**; coverage **99.02%** on
  `src/` (`--cov-fail-under=90` gate satisfied).
- Pre-render validation: clean; no render-blocking pitfalls or undefined citations.
- Template drift (`--project templates/template_eda_notebook --strict`): **no drift detected**.
- Pipeline stages 02 (analysis), 03 (render), 04 (validate), and 05 (copy): all green.
- Render quality: **0** `^! ` LaTeX error lines in `output/pdf/*.log`; **0** unresolved `??`; combined PDF = **14 pages**.
- Accuracy: 120 rows → 4 dropped → 116 complete-case; group counts 38/34/44; 10 histogram bins summing to 116; correlations height–weight ≈ +0.72, height–resting ≈ −0.12, weight–resting ≈ −0.08; ranking order matches Results prose.
- Version drift: all five version-bearing metadata files declare **1.0.0**; repository URL is consistently `docxology/template_eda_notebook`; figure registry labels/schema match `src/eda/figures.py`.
- Documentation parity: `tests/AGENTS.md` lists exactly the 8 test modules; `scripts/AGENTS.md` lists both on-disk Python files; required `.agents` README entry points were added.
- Notebook launch fix (2026-08-02): the walkthrough's path cell previously
  only resolved `src` when launched from the project directory. It now also
  locates the project from the monorepo root via the `notebooks/` marker
  (no hard-coded project name), and all 9 code cells were verified to execute
  headlessly end-to-end from BOTH launch locations (120 rows → 4 dropped →
  116; correlations +0.720 / −0.121 / −0.083, matching the Results prose).
  Stray `htmlcov/` and `dist/` build junk were removed from the tree.
- Deterministic dataset generator (2026-08-02): added
  `src/eda/generate.py::generate_measurements` (pure, fixed seed) and the thin
  `scripts/generate_measurements_data.py` orchestrator (writes
  `output/data/measurements_generated.csv`; discovered by stage 02), plus
  `tests/test_generate_measurements_data.py` binding the generated sibling to
  the shipped fixture's contract (schema, 120 rows, missingness 1/2/1, group
  labels, correlation sign structure, same-family statistics). Suite grew to
  **77 passed, 0 failed, 0 skipped**; coverage **99.16%** on `src/`. Honest
  scope note: the generator reproduces the fixture's *family*, not a byte-exact
  clone — the original fixture's random draw order is not recoverable, so
  byte-exact regeneration is recorded as intentionally out of scope (see Test
  and validator gaps).

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for
  EDA / computational-notebook research projects.
- Keep all figures and the summary table generated from `scripts/eda_analysis.py`,
  not hand-maintained `output/` snapshots.
- Keep `src/eda/` free of plotting and `infrastructure.*` imports.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize template with
  the same top-level sections as `config.yaml`, including the `project_config.dataset` block.
- Add any future EDA parameters (e.g. correlation method, imputation strategy)
  under typed source loaders rather than reading ad hoc YAML from scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name
  `templates/template_eda_notebook`.
- Link any new public artifacts from README, AGENTS, and the generated exemplar
  roster rather than hardcoding paths.

## Test and validator gaps

- Add a negative control before widening EDA claims beyond the bundled
  deterministic dataset.
- Add an exact-value assertion whenever a new figure-data preparer or statistic
  is introduced.
- Keep the notebook-binding test in sync as the public `src` surface grows.
- Byte-exact regeneration of `data/measurements.csv` remains intentionally out
  of scope: the original fixture's random draw order is not recoverable, and
  the generator (`src/eda/generate.py`) deliberately reproduces the fixture's
  documented contract (schema, size, missingness, correlation signs) rather
  than claiming a false byte-exact clone. If the dataset is ever regenerated
  from scratch, check in the new CSV and keep `DatasetSchema` in sync.
- Add a real generator script (e.g. `scripts/generate_measurements_data.py`)
  with a fixed NumPy seed that reproduces `data/measurements.csv` exactly, plus
  a test binding the script's output to the shipped CSV, to strengthen the
  dataset's reproducibility story beyond a static fixture.

## Ordered improvement ladder

1. Preserve the notebook -> tested src extraction contract (no logic in cells).
2. Add focused tests + a thin script plot for any new figure-data family.
3. Expand the dataset or cleaning strategies only with deterministic fixtures,
   exact-value tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.
