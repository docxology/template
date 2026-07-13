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
