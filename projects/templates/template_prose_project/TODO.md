# template_prose_project TODO

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

- Keep editorial metrics framed as diagnostics, not publication approval.
- Keep `output/evidence_summary.json` diagnostic-only and versioned, separating
  readability, citation density, bibliography consistency, structural outline
  results, and quality flags.
- Keep prose pipeline orchestration thin over `src/` and `infrastructure/prose`.
- Keep the bibliography cross-check bound to the project-owned parser and keep
  the thin script seam free of duplicated business logic.
- Keep editorial presets explicit, schema-validated, and covered by migration
  tests when threshold names or report fields change.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` stricter than the bundled exemplar config so forks see realistic editorial defaults — now **enforced by test** (`test_example_config_parses_and_is_stricter_than_bundled`).
- Add migration tests if prose threshold names or report output keys change — check-name and schema-shape assertions live in `tests/test_pipeline.py`.

## Documentation and signposting gaps

- Keep README and AGENTS clear that no LLM or Ollama dependency is required for the default review.
- Link any new report sections from `docs/architecture.md` and `docs/quickstart.md`.
- `docs/AGENTS.md` per-file line-count inventory re-verified 2026-08-02 against `wc -l` (README 118, AGENTS 169, agent_instructions 203, architecture 80, style_guide 268, syntax_guide 209, testing_philosophy 169, rendering_pipeline 258, output_conventions 66, quickstart 81, troubleshooting 191, faq 237). Re-check after any doc edit.

## Test and validator gaps

- Keep negative controls for skipped heading levels, citation-density
  regressions, and missing bibliography entries as the suite grows.
- Keep claim-ledger sources resolvable and manuscript labels/reference targets
  unique; add focused negative controls for any new report or preset field.
- Add report-schema tests before downstream docs depend on new report fields.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks. **Documented:** `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` serves this role.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PROSE-LLM-REVIEW-1` | blocked-tool | Medium | Explicit configured provider and transcript | Install or pin the required tool, or record its unavailable status to unblock; run project tests with LLM disabled by default and attach opt-in review receipt. | opt-in review receipt | `uv run pytest tests -q --no-cov --timeout=120` | enabled review without provider must fail closed |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
