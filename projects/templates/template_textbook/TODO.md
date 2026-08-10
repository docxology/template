# template_textbook TODO

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

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters,
  appendices, labs, and question banks.
- Keep finished chapters clearly separated from fillable stubs.
- Keep the structured scaffold audit (`textbook.audit.run_manuscript_audit`)
  covering orphan part markdown, unit intros, and strict-CLI failures.

## Configurable-surface gaps

- `manuscript/config.yaml.example` now mirrors the live shape; add migration
  tests if `units:` or appendix keys change (the example is currently
  shape-checked by hand, not by a test).
- Add a test that pins the example config's key shape to the live config so a
  future divergence is caught automatically.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript docs clear about worked exemplars versus
  stubs.
- Link any new structural config keys from the README, AGENTS, and the
  visualization guide.

## Test and validator gaps

- Add negative controls for orphan chapter files, missing labs or questions,
  and stale Mermaid diagrams. Zero-stub completeness now has library and real
  CLI negative controls through `--require-complete`.
- Add deterministic checks for generated cover art and diagrams when visual
  styles change.
- Register textbook worked-example numbers, percentages, and appendix-gallery
  constants as configured facts, or mark them as documentation-only examples,
  before treating Stage 04 as warning-free.
- Add or document a stable final artifact-manifest refresh path for
  single-stage analysis, render, and copy checks. **Documented:**
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  serves this role — it writes a current-output snapshot manifest labeled
  `current-output-snapshot` without requiring a full `PipelineExecutor` run.
- Keep the optional external Mermaid `mmdc` boundary bounded by timeout,
  isolated process group, descendant cleanup, and deterministic `.mmd` fallback;
  synchronize its policy with infrastructure Mermaid renderers.

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `TEXTBOOK-CONFIG-MIGRATION-1` | Minor | Live/example config shape | compatibility key-set receipt | textbook config tests | orphaned or dropped config key must fail |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `TEXTBOOK-STALE-DIAGRAM-1` | Medium | Diagram inventory | stale/orphan diagram report | audit and render gates | unreferenced diagram must fail |
| `TEXTBOOK-FACT-REGISTRY-1` | Medium | Worked-example source data | numeric-fact registry | manuscript evidence gate | changed numeric fact without registry update must fail |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
