# template_sia TODO

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

- Keep fixture replay as the default validated behavior.
- Keep `run_summary.json` explicit about fixture replay versus live subprocess
  execution and whether later-generation feedback was applied or only recorded.
- Keep Stage 04's rendered-provenance bind over the whole stable output tree
  (PDF, web, hydrated manuscript, release, and composition). Rebaseline with
  `uv run python scripts/maintenance/refresh_artifact_manifests.py --project templates/template_sia`
  or `scripts/maintenance/refresh_rendered_provenance.py --project templates/template_sia`
  after manual stage-by-stage runs.
- Keep target-agent mutation out of the public exemplar until sandboxing, diff review, and rollback contracts exist.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the `project_config.sia` block and safe defaults.
- New loop controls must enter through the typed config loader before they are exposed in README commands.

## Documentation and signposting gaps

- Keep README, AGENTS, and docs explicit that the live mode is illustrative and non-mutating.
- Keep `tests/AGENTS.md`, `.agents/README.md`, and `.agents/skills/README.md`
  synchronized with the on-disk catalog and test files.
- The fork checklist for a real improvement loop is the documented sandbox, diff-review, rollback, and approval boundary; a future fork must retain each control.

## Test and validator gaps

- Keep negative controls (invalid run_summary payload, empty train CSV, all
  `validate_task_dir` failure modes) and metric edge cases as the suite grows.
- Keep claim-ledger artifact paths source-bound and fail-closed, including the
  public training-row fact and its committed CSV producer.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SIA-APPROVAL-FORK-1` | blocked-external | Medium | Sandbox, diff, rollback, human approval | The typed approval contract and fork guidance are ready; obtain the required owner receipt and a real disposable fork before enabling `live_apply`, then attach the approval receipt. | `src/approval.py` contract + fork guidance + owner receipt | `uv run pytest projects/templates/template_sia/tests -q --no-cov --timeout=120` | mutation without approval must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
