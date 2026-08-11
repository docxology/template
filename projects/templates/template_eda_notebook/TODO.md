# template_eda_notebook TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
next action, proving artifact, acceptance command, and negative control; absence of an owner or external receipt
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
- Any future EDA parameters (e.g. correlation method, imputation strategy) must
  enter through typed source loaders rather than ad hoc YAML reads in scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name
  `templates/template_eda_notebook`.
- Link any new public artifacts from README, AGENTS, and the generated exemplar
  roster rather than hardcoding paths.

## Current test and validator contract

- EDA claims remain bounded by the bundled deterministic dataset and its negative
  controls; any future claim expansion requires a scoped row and new evidence.
- Exact-value assertions cover the current figure-data preparers and statistics;
  extend them with any future surface change.
- The notebook-binding test is the current source-to-notebook contract and must
  remain synchronized as the public `src` surface grows.
- Byte-exact regeneration of `data/measurements.csv` remains intentionally out
  of scope: the original fixture's random draw order is not recoverable, and
  the generator (`src/eda/generate.py`) deliberately reproduces the fixture's
  documented contract (schema, size, missingness, correlation signs) rather
  than claiming a false byte-exact clone. If the dataset is ever regenerated
  from scratch, check in the new CSV and keep `DatasetSchema` in sync.
- A future byte-exact fixture replacement would require a fixed-seed generator,
  a committed replacement CSV, and a binding test; no historical fixture
  reconstruction is claimed by this exemplar.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
