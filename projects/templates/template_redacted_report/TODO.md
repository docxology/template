# template_redacted_report TODO

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

- Keep rendered sanitized report outputs and development visual-proof outputs regenerated after style, steganography, or Kmyth build changes.

## Configurable-surface gaps

- Organization-specific marking taxonomies and review-role policies are intentionally limited to cleared, invented fixtures; a real policy needs a separately scoped owner-approved row.

## Documentation and signposting gaps

- Keep public safety boundaries visible in README, AGENTS, and manuscript prose.

## Current test and validator contract

- Bind manuscript tables to the canonical audit JSON only if rendering can preserve the text-free projection and fails closed when the audit schema changes.
- Pixel-level visual regression remains the explicit blocked-tool row below until the repo adopts stable screenshot/PDF raster tooling for exemplar outputs.
- Keep year-stable ISO-date residual detection and complete collection-platform
  span coverage under negative controls; contextual labels in explicitly public
  explanatory prose must remain distinct from source-segment residuals.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `REDACTED-VISUAL-1` | blocked-tool | Medium | Stable raster toolchain | Install or pin the required tool, or record its unavailable status; run the explicit visual gate only when tooling is pinned and attach a pixel regression manifest. | pixel regression manifest | `uv run pytest projects/templates/template_redacted_report/tests -q --no-cov --timeout=120` | missing raster tool must report unavailable, not pass |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
