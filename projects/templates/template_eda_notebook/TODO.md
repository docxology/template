# template_eda_notebook TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

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
  a test binding the script's output to the committed CSV, to strengthen the
  dataset's reproducibility story beyond a static fixture.

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `EDA-STATISTICS-1` | Minor | Existing deterministic fixture | exact-statistic assertion matrix | `uv run pytest projects/templates/template_eda_notebook/tests -q` | one altered source statistic must fail |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `EDA-NOTEBOOK-BINDING-1` | Medium | Notebook extraction contract | notebook-to-source binding receipt | notebook binding gate and project coverage | changed notebook cell without source update must fail |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
