# template_template TODO

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

- Keep this exemplar as the template-about-template reference for architecture,
  metrics, and confidentiality invariants.
- Keep every generated metric derived from the live tree and generated-doc
  sources rather than copied literals.
- Public-roster and confidentiality-policy changes require a compatibility note
  in the same revision as the generated roster update.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize metadata
  starting point (shape-synced with the live config: split DOIs,
  `repository_url`, `published_artifacts`, `transmission_bookends`).
- Explicit config keys are required before any new manuscript metric becomes
  user-tunable.

## Documentation and signposting gaps

- Keep README and AGENTS linked to generated public-scope docs instead of
  duplicating the rotating project list.
- The fork guidance is a documentation requirement for any downstream copy of
  this exemplar; it is not a claim that a downstream fork exists here.

## Test and validator gaps

- Negative controls for stale generated metrics and accidental inclusion of
  local-only project paths are bound by `tests/metrics/test_stale_metrics_control.py` to
  the generated metric schema and live public-scope paths.
- Schema tests are required before changing the metrics JSON consumed by the
  manuscript.
- Keep the manuscript evidence-contract test green as new generated metrics or
  cited empirical values are introduced; live counts remain token-injected, and
  policy percentages remain bound to executable configuration.
- Use `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  for single-stage analysis, render, and copy checks. It writes a
  `current-output-snapshot` manifest without requiring a full
  `PipelineExecutor` run.
- Validate actual introspection branch reachability before adding coverage;
  preserve honest limitations and use real inputs/environments rather than mocks.

## Platform 4 acceptance scope

The rows below describe remaining acceptance and repairs, not a claim that
existing implementations are missing. Inspect current source and the dated
[program record](../../../docs/maintenance/platform-4-upgrade.md) first.
Set `P4_PROJECT_ROOT` to this project's absolute canonical checkout and prepare
its locked environment using the [runtime matrix guide](../../../docs/development/public-runtime-matrix.md).
Run one project per pytest process under the producer's declared finite outer
deadline and source-owned per-case limits. The whole-selection domain command
is an explicit acceptance opt-in: prepare its declared unpaid tool/model
prerequisites, disable test model pulls, and override default marker exclusions
with `-m ""`. Own-source acceptance requires nonempty complete collection, real
behavior and at least 90% branch coverage; a focused test or previous revision's
result does not close the row. Missing preparation remains blocked.

Native and live lanes additionally require actual producers, independent
content/visual/domain checks and current source/tool/model identities; ordinary
unit tests do not replace them. Apply the root `P4-RUNTIME-MATRIX`,
`P4-INSTALLED-MATRIX`, `P4-UNPAID-CAPABILITIES` and publication contracts.
Unavailable required tools/providers remain blocked. Independent intended
versions come from the program record and package metadata, and remain separate
from genuinely published versions.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P4-TEMPLATE-DOMAIN-1` | partial | Medium | All other exemplar and source/documentation integration; P4-PUBLIC-REFERENCE-1 | Regenerate this exemplar last and independently recount final public source, architecture, DAG and manuscript metrics using the admitted Root source rather than ambient Git/PATH or stale snapshots. | independent final metrics, source/DAG and confidentiality receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | private same-leaf aliases, forged PATH counts, stale source identities or copied literal metrics must fail |
| `P4-TEMPLATE-MANUSCRIPT-1` | open | Medium | P4-TEMPLATE-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate final architecture diagrams, manuscript tables, source metrics and figures after all other changes; bind every claim to generator-owned current evidence. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_template`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-TEMPLATE-PORTABILITY-1` | open | Medium | P4-TEMPLATE-DOMAIN-1; P4-TEMPLATE-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_template --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-TEMPLATE-REMOTE-1` | open | Medium | P4-TEMPLATE-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
