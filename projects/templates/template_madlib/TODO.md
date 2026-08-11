# template_madlib TODO

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

- Keep the lexicon, conditional section plan, token provenance, and authoring contract as generated evidence, not prose-only claims.
- Keep digest invariants, claim-ledger alignment, review-packet assembly, and fork-migration obligations config-owned and test-covered.
- Split any oversized source module before adding new visualization or report builders.
- Preserve public imports for artifact generation and figure writers when refactoring internals.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` placeholder-safe while retaining every required schema block a fork needs.
- Schema-level validation is required before any new optional madlib section or generated figure enters the public contract.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript Methods aligned on the same source-owned generation contract.
- Keep fork guidance explicit: replacing toy lexicon categories with domain lexicons also requires config rows, source changes where behavior changes, validators, tests, Stage 04/05 review-packet checks, claim-ledger evidence, and conservative metadata.
- Keep review-packet guidance explicit that PDF/HTML alone are not enough; data, reports, figures, validation results, and copy statistics travel with the manuscript.

## Test and validator gaps

- Keep the project-local output validator and declared artifact inventory
  synchronized with any new token, figure, data, or report surface.
- Preserve review-packet assertions if future copied-output layout changes make output statistics, validation reports, or copied data/report/figure categories optional.
- The SHA-256 digest invariant is currently covered by parametric seed/lexicon tests; property-based tests are an optional future strengthening only if the lexicon format changes and must then be scoped as a row.

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
