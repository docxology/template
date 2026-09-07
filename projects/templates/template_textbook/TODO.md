# template_textbook TODO

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

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters,
  appendices, labs, and question banks.
- Keep finished chapters clearly separated from fillable stubs.
- Keep the structured scaffold audit (`textbook.audit.run_manuscript_audit`)
  covering orphan part markdown, unit intros, and strict-CLI failures.

## Configurable-surface gaps

- `manuscript/config.yaml.example` is checked against the live shape by
  `tests/test_contracts.py::test_live_and_example_config_shapes_are_lockstep`;
  extend that contract when `units:` or appendix keys change.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript docs clear about worked exemplars versus
  stubs.
- Link any new structural config keys from the README, AGENTS, and the
  visualization guide.

## Current test and validator contract

- Negative controls for orphan chapter files, missing labs or questions, and
  stale Mermaid diagrams are covered by the library and real CLI paths through
  `--require-complete`.
- Generated cover art and diagrams have deterministic checks; extend those
  checks with any future visual-style change.
- Textbook worked-example numbers, percentages, and appendix-gallery constants
  are either configured facts or explicitly documentation-only examples before
  Stage 04 is treated as warning-free.
- Use `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  for single-stage analysis, render, and copy checks. It writes a
  `current-output-snapshot` manifest without requiring a full
  `PipelineExecutor` run.
- Keep the optional external Mermaid `mmdc` boundary bounded by timeout,
  isolated process group, descendant cleanup, and deterministic `.mmd` fallback;
  synchronize its policy with infrastructure Mermaid renderers.

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
