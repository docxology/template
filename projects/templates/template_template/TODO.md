# template_template TODO

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

- Keep this exemplar as the template-about-template reference for architecture,
  metrics, and confidentiality invariants.
- Keep every generated metric derived from the live tree and generated-doc
  sources rather than copied literals.
- Add a compatibility note when the public roster or confidentiality policy
  changes.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize metadata
  starting point (shape-synced with the live config: split DOIs,
  `repository_url`, `published_artifacts`, `transmission_bookends`).
- Add explicit config keys before any new manuscript metric becomes
  user-tunable.

## Documentation and signposting gaps

- Keep README and AGENTS linked to generated public-scope docs instead of
  duplicating the rotating project list.
- Add a short "how to fork the meta-template" note if downstream users copy this
  exemplar for repository-method papers.

## Test and validator gaps

- Add negative controls for stale generated metrics and accidental inclusion of
  local-only project paths; keep `tests/test_stale_metrics_control.py` bound to
  the generated metric schema and live public-scope paths.
- Add schema tests before changing the metrics JSON consumed by the manuscript.
- Keep the manuscript evidence-contract test green as new generated metrics or
  cited empirical values are introduced; live counts remain token-injected, and
  policy percentages remain bound to executable configuration.
- Add or document a stable final artifact-manifest refresh path for
  single-stage analysis, render, and copy checks. **Documented:**
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  serves this role — it writes a current-output snapshot manifest labeled
  `current-output-snapshot` without requiring a full `PipelineExecutor` run.
- Document the structurally unreachable introspection branches (the `dir()`
  fallback, the redundant `is_dir()` re-check, and the `ImportError` version
  fallback) in `tests/AGENTS.md` rather than covering them with mocks.

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `META-MATRIX-1` | Minor | Public roster generator | matrix lockstep report | generated-doc and roster gates | roster drift must fail |
| `META-STEG-1` | Minor | Steganography config producer | deterministic metadata revalidation | metadata/visual tests | changed default must invalidate stale evidence |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `META-SCHEMA-1` | Medium | Generated metric schema | schema-versioned metrics receipt | meta-template tests | stale metric key must fail |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
