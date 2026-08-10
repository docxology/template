# template_data_descriptor TODO

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

- Keep rendered manuscript outputs, figures, and descriptor-review artifacts regenerated after schema or fixture changes. Recompute fixture checksums/row counts and update `data/example_descriptor.json` whenever `data/fixtures/` changes.
- Re-run `scripts/generate_figures.py` and `scripts/generate_release_artifacts.py` after any change to `src/data_descriptor/` so `output/figures/figure_registry.json` and `output/reports/*` stay in sync with the source.

## Configurable-surface gaps

- Extend `manuscript/config.yaml.example` when new descriptor fields become first-class.

## Documentation and signposting gaps

- Keep README, AGENTS, STANDALONE, and the per-directory README/AGENTS pairs aligned with the descriptor validator, verification, and figure modules.

## Test and validator gaps

- Add live checks for larger tabular files only after the fixture descriptor is stable; extend verification to non-CSV media types when a real dataset needs them.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DATA-PUBLICATION-1` | blocked-external | Medium | A real fork and owner receipt | Obtain the required owner or external receipt to unblock; run project tests and standalone export check and attach publication receipt + standalone replay. | publication receipt + standalone replay | `uv run pytest tests -q --no-cov --timeout=120` | fabricated publication receipt must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DATA-MEDIA-1` | blocked-external | Major | Real licensed non-CSV fixture | The validator now supports justified JSON Lines in addition to CSV/JSON; obtain a real licensed non-CSV fixture and attach its checksum/row manifest before promoting the media claim. | media checksum/row manifest + license receipt | `uv run pytest projects/templates/template_data_descriptor/tests -q --no-cov --timeout=120` | unsupported media, malformed rows, symlink escape, or wrong checksum must fail |

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
