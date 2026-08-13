# template_registered_report TODO

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

- Keep rendered manuscript outputs and registered-report review artifacts regenerated after fixture, deviation, or sensitivity-analysis changes; preserve the fresh-regeneration contract when the artifact schema changes.

## Configurable-surface gaps

- Keep ethics-review and registered-report-stage metadata aligned with any future journal-specific fixtures.

## Documentation and signposting gaps

- Keep standalone fork guidance synchronized with the validator API.

## Test and validator gaps

- Keep rendered sensitivity-analysis tables bound to the frozen registration
  and deviation ledger.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `REGISTERED-PUBLICATION-1` | blocked-external | Medium | Real fork and owner receipt | Obtain the required owner or external receipt to unblock; run project artifact and preflight gates and attach publication payload receipt. | publication payload receipt | `uv run pytest projects/templates/template_registered_report/tests -q --no-cov --timeout=120` | synthetic DOI/receipt must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
