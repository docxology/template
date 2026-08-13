# template_storybook TODO

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

- Keep story text in `content/story.yaml` and rendering behavior in `src/storybook/`.
- Keep every story page as a full-page illustration; no manuscript-style partial
  figures for the primary artifact.
- Page-level accessibility alt text is generated in
  `output/data/storybook_manifest.json`; keep it descriptive when page content
  changes.
- Keep script, test, documentation, and `.agents/` catalog listings generated
  or checked against disk so future forks cannot silently omit a surface.

## Current configurable-surface contract

- `trim_size` supports the current configured and custom page dimensions; a
  future trim variant must add a schema value and a rendering/negative-control
  test in one scoped row.
- Per-page caption placement supports the current top and bottom zones; future
  zones require a schema, accessibility, and raster-contrast contract.

## Documentation and signposting gaps

- Keep README examples clear that Stage 02 renders the storybook PDF, while
  Stage 03 renders the descriptive manuscript PDF.
- The deterministic contact sheet is generated at
  `output/figures/storybook_contact_sheet.png` for every Stage-02 render.

## Test and validator gaps

- Keep a raster contrast audit for direct text overlays, using real pixel math
  and recording per-page results in the manifest; extend the palette contract
  before adding new overlay modes.

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
