# template_methods_paper TODO

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
  methods-specification / controlled-procedure research projects.
- Keep every export and report artifact generated from
  `scripts/methods_analysis.py`, not hand-maintained `output/` snapshots.
- Keep `src/methods_dsl/` free of plotting and `infrastructure.*` imports
  except the one declared exception (`_logging.py`).

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize template
  with the same top-level sections as `config.yaml`, including the `project_config.dsl`
  block.
- Any future controlled vocabulary (units, step kinds, targets) must enter under
  `src/methods_dsl/units.py` / `vocabulary.py`, never as ad hoc YAML read from
  scripts — the vocabulary is the DSL's contract, not configuration.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name
  `templates/template_methods_paper`.
- Link any new public artifacts from README, AGENTS, and the generated
  exemplar roster rather than hardcoding paths.

## Current test and validator contract

- Claims remain bounded by the two bundled worked examples
  (`PBSPreparation`, `SensorCalibrationSweep`) and their negative controls.
- Exact-value assertions cover the current step kinds, units, and gates; extend
  them with any future DSL surface change.
- `tests/conftest.py`'s invalid-method fixtures (dangling dependency, duplicate
  step id, unknown unit, cycle, target mismatch) define the staged-gate contract
  and must evolve with that contract.

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
