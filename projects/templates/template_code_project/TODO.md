# template_code_project TODO

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

- Keep this exemplar as the smallest reliable control-positive path for code-centric research projects.
- Keep dashboard, API docs, figures, and manuscript variables generated from source, not hand-maintained output snapshots.
- The generic Stage 04 validators are the source of truth; a project-local output validator is warranted only when a future artifact contract cannot be expressed there.
- Use `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` as the stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Any future optimizer hyperparameter config must enter through typed source
  loaders rather than ad hoc YAML reads in scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_code_project`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator.

## Current test and validator contract

- Optimizer claims remain bounded by the bundled deterministic objectives and their negative controls.
- Dashboard fields and chart payloads are covered by schema assertions; extend those assertions with any future field change.
- The remaining infrastructure-path branches in `analysis/scientific_reports.py` and `analysis/workflow.py` are coverage guidance only; add subprocess-isolation tests only if a future coverage gate exposes a reproducible branch requirement.

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
