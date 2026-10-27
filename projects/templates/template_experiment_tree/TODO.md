# TODO — template_experiment_tree (future-only)

Future work is scoped below. Existing contract observations and completed signposting
notes were moved to [`exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md).

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
| `TREE-NODE-REUSE-1` | open | Minor | Tree-store identity contract | Reject reuse of a node ID across independently identified trees. | cross-tree identity validator and cases | `uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ -q --no-cov --timeout=120` | reusing a frozen tree's node ID in another tree must fail |
| `TREE-RENDER-ADMISSION-1` | open | Minor | Source-bound PDF contract | Add render-stage admission for the tracked PDF and its current hydrated source. | render/source admission receipt | `uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ -q --no-cov --timeout=120` | stale or wrong-tree PDF/source evidence must fail |

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P4-TREE-DOMAIN-1` | partial | Medium | TREE-NODE-REUSE-1; TREE-DIFF-1; TREE-PRUNING-1; TREE-POLICY-CONFIG-1 | Verify provisional/frozen/answered transitions, frozen-node immutability, cross-tree identity, retained negative results and coherent explicit policy; complete independently identified snapshot/diff/pruning controls. | transition/freeze/negative-result and independently recomputed tree-state receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | cross-tree ID reuse, changed frozen commands, lost negatives or omitted changed nodes must fail |
| `P4-TREE-MANUSCRIPT-1` | open | Medium | P4-TREE-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate tree diagrams and state summaries with TREE-RENDER-ADMISSION-1; retain unpublished status and create actual first-release metadata only after real publication. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_experiment_tree`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-TREE-PORTABILITY-1` | open | Medium | P4-TREE-DOMAIN-1; P4-TREE-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_experiment_tree --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `TREE-DIFF-1` | open | Medium | Source-bound before/after tree snapshots | Implement a tree-state diff report with explicit snapshot identities. | tree diff report | `uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ -q --no-cov --timeout=120` | a changed node absent from the report must fail |
| `TREE-PRUNING-1` | open | Medium | Frozen-node preservation contract | Scope round-based pruning for unfrozen branches and retain frozen ancestry. | pruning contract receipt | `uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ -q --no-cov --timeout=120` | attempted deletion or mutation of a frozen node must fail |
| `TREE-POLICY-CONFIG-1` | open | Medium | Frozen-node preservation; current engine schema | Scope explicit configuration for status vocabulary and run-command policy while preserving frozen registrations. | versioned policy schema and migration cases | `uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ -q --no-cov --timeout=120` | an invalid transition or changed frozen run command must fail |

| `P4-TREE-REMOTE-1` | open | Medium | P4-TREE-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
