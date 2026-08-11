# AutoResearch Project TODO

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

## Current scope

This exemplar remains an offline, deterministic starter for bounded ML-loop
orchestration. The active contract is review readiness without publication
approval, source-ledger traceability, benchmark-boundary honesty, and local
security evidence. New adapters or review schema versions require a separately
scoped Minor or Medium row with its own fixture and negative control.

## Invariants to keep

These are the load-bearing guardrails of the exemplar. Keep each one true; use
git history for how they were established.

| Surface | Behavior | Guardrail to keep |
| --- | --- | --- |
| Manual approval | `human_review.yaml` is the human-authored approval source; generated files can report readiness but cannot self-approve publication | default `publication_approved: false`; generated code must not mutate the human review file |
| Review readiness | `autoresearch_review_packet.json` and `review_decisions.json` distinguish review readiness from publication approval | validators fail on generated self-approval |
| Source ledger | `manuscript/source_ledger.yaml` is parsed through reusable project helpers and checked offline | citekeys stay present in ledger, BibTeX, and numbered manuscript prose |
| ML loop | bounded deterministic ML execution records baseline, candidate selection, metric improvement, and budget evidence | no runtime downloads, no generated-code execution, no network calls |
| Evidence reports | compact evidence registry, phase ledger, figure-quality report, rank stability, and calibration diagnostics are generated from shared data | report-size guard remains in place unless explicitly enabled |
| Evidence overview | `autoresearch_evidence_overview.json` and `.md` summarize readiness versus approval, claim evidence rows, source-ledger tier/age status, benchmark boundaries, and security/integrity status | overview must keep generated readiness separate from human publication approval |
| Benchmark boundary | `benchmark_boundary.json` records fixture scope, metric direction, baseline, candidate families, budget, and explicit non-claims | benchmark-adjacent prose must not imply broad empirical or leaderboard claims |
| Module shape | ML, figure, diagnostics, manuscript table, and source-ledger responsibilities have been split below drift thresholds | future additions go into the right leaf modules, not back into large hubs |

## Non-negotiable invariants

- Default execution performs no network calls, no LLM calls, no runtime dataset
  downloads, no generated-code execution, and no autonomous publication approval.
- Numbered manuscript prose keeps run-derived facts tokenized through
  `{{TOKEN}}` hydration and registry-backed figure blocks.
- Generated review artifacts may become ready for review while publication
  remains unapproved.
- Security artifacts remain local integrity evidence only: no external signing,
  no production SLSA claim, and no runtime monitoring claim.
- `scripts/regenerate_mnist_fixture.py` remains manual maintenance tooling only;
  default pipeline scripts and loop execution must not import or call it.

## Integrity and template-status gaps

Keep the exemplar forkable as an offline starter. Future hardening should
improve maintainability, schema compatibility, and review-boundary clarity
without changing the default no-network, no-LLM, no-autonomous-approval
contract.

## Configurable-surface gaps

New configurable behavior belongs in `manuscript/config.yaml`, the loop
configuration helpers, source ledgers, review-boundary files, or explicit task
adapters. Keep `manuscript/config.yaml.example` in top-level parity and scrubbed
of project-specific release values whenever config sections change.

## Documentation and signposting gaps

When adding an adapter, review artifact, publication field, or report surface,
update the nearest README/AGENTS signpost with when to use it, how to run it
through the monorepo, what validates it, and which claims remain deliberately
out of scope.

## Test and validator gaps

Every new research-loop surface needs a deterministic fixture, a positive test,
and a negative-control gate for hollow evidence, self-approval, stale source
ledger entries, or benchmark-boundary overclaiming. Avoid mocks for core loop
behavior; use tiny local fixtures instead.

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
