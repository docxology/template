# template_newspaper TODO

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

- Keep edition content fictional unless a fork adds real source provenance and fact-checking validators.
- Keep ReportLab layout logic in `src/`, with scripts as thin orchestration only.
- The machine-readable `layout_audit` artifact records page geometry and
  glyph-clearance findings separately from `all_pages_fit`, overset, and
  missing-image checks; keep all four signals distinct.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with publication metadata and render toggles.
- A minimal one-page fork schema example is required in the same row if
  `content/edition.yaml` ever gains required fields.

## Documentation and signposting gaps

- Keep README and docs clear that the newspaper PDF is produced by project scripts, while the manuscript PDF is produced by the monorepo renderer.
- Link any new content schema fields from `docs/syntax_guide.md` and the README quick-start.
- The platform-dependent `typography.py` `register_fonts()` fallback arc is documented in the README, architecture, and testing guide; its base-14 branch remains uncovered under the no-mocks policy.

## Current test and validator contract

- Documentation-only README numbers are excluded from empirical claims, and
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  is the stable single-stage refresh path.
- Keep the platform-only `typography.py` fallback branch documented rather than mock-covered; revisit only if the no-mocks policy or the CI font matrix changes.

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
