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
- Keep host-source promotion blocked until the exact diff receives owner approval; bound opt-in numeric candidates to disposable Docker execution and proved rollback.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the `project_config.sia` block and safe defaults.
- New loop controls must enter through the typed config loader before they are exposed in README commands.

## Documentation and signposting gaps

- Keep documentation explicit about fixture replay, unchanged reference diagnostics, and opt-in local numeric proposals evaluated in disposable containers.
- Keep `tests/AGENTS.md`, `.agents/README.md`, and `.agents/skills/README.md`
  synchronized with the on-disk catalog and test files.
- The fork checklist for a real improvement loop is the documented sandbox, diff-review, rollback, and approval boundary; a future fork must retain each control.

## Test and validator gaps

- Keep negative controls (invalid run_summary payload, empty train CSV, all
  `validate_task_dir` failure modes) and metric edge cases as the suite grows.
- Keep claim-ledger artifact paths source-bound and fail-closed, including the
  public training-row fact and its committed CSV producer.

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
| `P4-SIA-DOMAIN-1` | partial | Medium | local sandbox/approval contract; prepared container and explicit local model | Execute actual local proposals and mutations in a disposable network-disabled restricted container; verify frozen holdout evaluation, exact diff/source custody, approval binding and proved rollback within the configured generation/time bounds. | actual sandbox/resource/holdout/diff/approval/rollback receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | host credentials or network exposure, holdout leakage, mutation without exact approval or unproved rollback must fail |
| `P4-SIA-MANUSCRIPT-1` | open | Medium | P4-SIA-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate generation/score/diff/rollback figures and manuscript outputs; distinguish sandbox candidate execution from approved host-source promotion and retain honest null results. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_sia`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-SIA-PORTABILITY-1` | open | Medium | P4-SIA-DOMAIN-1; P4-SIA-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_sia --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `SIA-APPROVAL-FORK-1` | blocked-external | Medium | Sandbox, diff, rollback, human approval | Obtain the required owner receipt and a real disposable fork before enabling host `live_apply`; bind the exact diff and rollback to approval. Local disposable-sandbox/domain verification can proceed separately. | `src/template_sia/loop/approval.py` contract + fork guidance + owner receipt | `uv run pytest projects/templates/template_sia/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | mutation without approval must fail |

| `P4-SIA-REMOTE-1` | open | Medium | P4-SIA-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
