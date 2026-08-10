# template_literature_meta_analysis TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Integrity and template-status gaps

- Keep the fixture corpus clearly marked as synthetic in README, manuscript, and generated-output prose.
- Keep `data/claim_ledger.yaml` tied to project-local sources, not sibling exemplar paths.

## Configurable-surface gaps

- Retargeting should remain config-owned through `manuscript/config.yaml`; avoid hard-coded domain terms in `src/`.
- Keep live retrieval knobs explicit for engines, relevance keywords, subfields, and hypotheses.

## Documentation and signposting gaps

- Keep README, AGENTS, and `docs/_generated/exemplar_roster.md` synchronized through the generator.
- Keep troubleshooting examples on `template_literature_meta_analysis`, not sibling exemplars.

## Test and validator gaps

The open work below should add tests or validators before promoting new claim surfaces.

## Minor upcoming

No active rows are currently scoped at this size.

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `LIT-ENGINE-POLITENESS-1` | Medium | Retrieval engine adapters | `output/data/retrieval_run_manifest.json` | live-run smoke with skipped/limited engine rows | retry storm or missing rate-limit receipt must fail |
| `LIT-KG-CALIBRATION-1` | Medium | Knowledge-graph extraction schema | calibration fixture bundle | KG parser/scorer tests preserve score direction | inverted score direction must fail |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
