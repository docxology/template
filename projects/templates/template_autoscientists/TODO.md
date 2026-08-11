# template_autoscientists TODO

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

- The single-stage rendered-provenance bridge remains sensitive to `git check-ignore` under concurrent repo churn; full `PipelineExecutor` runs are the manifest-authoritative path. Any further hardening belongs in shared infrastructure, not this exemplar.
- Keep deterministic fixture replay green under the project coverage gate so the exemplar never ships a red baseline.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned when `SearchConfig` or `SyntheticObjective` defaults change.
- A script-level config summary is unnecessary while analysis scripts remain
  config-free; if that boundary changes, add the summary and a scoped row first.

## Documentation and signposting gaps

- None outstanding beyond keeping `tests/AGENTS.md` file listings and manuscript notation (`$p^{\ast}$`) in lockstep with source as gates evolve.

## Test and validator gaps

- Keep deterministic fixture replay covered by the project coverage gate.
- The live agent path remains opt-in; promotion requires offline transcript
  fixtures, stale-transcript detection, and no-network default validation.

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
