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

- Keep `manuscript/config.yaml.example` stricter than the bundled exemplar config so forks see realistic editorial defaults; preserve the existing shape and threshold regression tests when the contract changes.
- Threshold-name or report-key migrations require the existing check-name and schema-shape assertions in `tests/pipeline/test_pipeline.py` plus a scoped row when the public contract changes; renaming a threshold without moving its assertion is the known-wrong migration path this contract forecloses.

## Documentation and signposting gaps

- Keep README and AGENTS clear that no LLM or Ollama dependency is required for the default review.
- Link any new report sections from `docs/architecture.md` and `docs/quickstart.md`.
- Keep the documentation inventory source-bound; re-run the repository documentation/count gates after any doc edit instead of copying line counts into this backlog.

## Test and validator gaps

- Keep negative controls for skipped heading levels, citation-density
  regressions, and missing bibliography entries as the suite grows.
- Keep claim-ledger sources resolvable and manuscript labels/reference targets
  unique; add focused negative controls for any new report or preset field.
- Report-schema tests are required before downstream docs depend on new report fields.
- Use `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` as the stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

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
| `P4-PROSE-DOMAIN-1` | partial | Medium | PROSE-LLM-REVIEW-1; prepared explicit local model | Rerun the actual local Ollama review producer on current sources and bind exact prompt/response bytes, model identity and reviewed-source hashes; verify budgets and honest review boundaries. | actual local request/response/model/source receipt and negative controls | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | forged transcript, wrong model, zero generation, source edits during review or deadline failure must fail |
| `P4-PROSE-MANUSCRIPT-1` | open | Medium | P4-PROSE-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate manuscript, review-linked outputs and declared formats; distinguish machine-generated editorial feedback from validated scientific review and preserve offline defaults. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_prose_project`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-PROSE-PORTABILITY-1` | open | Medium | P4-PROSE-DOMAIN-1; P4-PROSE-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_prose_project --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `PROSE-LLM-REVIEW-1` | blocked-tool | Medium | Explicit configured provider and transcript | Install or pin the required tool, or record its unavailable status to unblock; run project tests with LLM disabled by default and attach opt-in review receipt. | opt-in review receipt | `uv run pytest projects/templates/template_prose_project/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | enabled review without provider must fail closed |

| `P4-PROSE-REMOTE-1` | open | Medium | P4-PROSE-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
