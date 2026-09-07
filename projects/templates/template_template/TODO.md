# template_template TODO

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

- Keep this exemplar as the template-about-template reference for architecture,
  metrics, and confidentiality invariants.
- Keep every generated metric derived from the live tree and generated-doc
  sources rather than copied literals.
- Public-roster and confidentiality-policy changes require a compatibility note
  in the same revision as the generated roster update.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize metadata
  starting point (shape-synced with the live config: split DOIs,
  `repository_url`, `published_artifacts`, `transmission_bookends`).
- Explicit config keys are required before any new manuscript metric becomes
  user-tunable.

## Documentation and signposting gaps

- Keep README and AGENTS linked to generated public-scope docs instead of
  duplicating the rotating project list.
- The fork guidance is a documentation requirement for any downstream copy of
  this exemplar; it is not a claim that a downstream fork exists here.

## Test and validator gaps

- Negative controls for stale generated metrics and accidental inclusion of
  local-only project paths are bound by `tests/test_stale_metrics_control.py` to
  the generated metric schema and live public-scope paths.
- Schema tests are required before changing the metrics JSON consumed by the
  manuscript.
- Keep the manuscript evidence-contract test green as new generated metrics or
  cited empirical values are introduced; live counts remain token-injected, and
  policy percentages remain bound to executable configuration.
- Use `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  for single-stage analysis, render, and copy checks. It writes a
  `current-output-snapshot` manifest without requiring a full
  `PipelineExecutor` run.
- The structurally unreachable introspection branches (the `dir()` fallback,
  redundant `is_dir()` re-check, and `ImportError` version fallback) are
  documented in the exemplar `tests/AGENTS.md`, rather than covered with mocks.

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
