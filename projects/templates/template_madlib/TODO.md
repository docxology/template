# template_madlib TODO

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

- Keep the lexicon, conditional section plan, token provenance, and authoring contract as generated evidence, not prose-only claims.
- Keep digest invariants, claim-ledger alignment, review-packet assembly, and fork-migration obligations config-owned and test-covered.
- Split any oversized source module before adding new visualization or report builders.
- Preserve public imports for artifact generation and figure writers when refactoring internals.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` placeholder-safe while retaining every required schema block a fork needs.
Forking with a stripped schema block is the known-wrong starting point the required-block rule exists to prevent.
- Schema-level validation is required before any new optional madlib section or generated figure enters the public contract; a malformed or unknown section block must fail composition (negative control: an invented token key is flagged by the QA probes rather than hydrated silently).

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript Methods aligned on the same source-owned generation contract.
- Keep fork guidance explicit: replacing toy lexicon categories with domain lexicons also requires config rows, source changes where behavior changes, validators, tests, Stage 04/05 review-packet checks, claim-ledger evidence, and conservative metadata.
- Keep review-packet guidance explicit that PDF/HTML alone are not enough; data, reports, figures, validation results, and copy statistics travel with the manuscript.

## Test and validator gaps

- Keep the project-local output validator and declared artifact inventory
  synchronized with any new token, figure, data, or report surface.
- Preserve review-packet assertions if future copied-output layout changes make output statistics, validation reports, or copied data/report/figure categories optional.
- Require actual seed/lexicon digest invariant controls for schema changes; scope additional property-based checks only when they prove a distinct failure mode.

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
| `P4-MADLIB-DOMAIN-1` | partial | Medium | P4-CLI-SCHEMA-RETIREMENT-1; current authoring schema | Verify current-schema admission, deterministic selection, conditional/default branches, injection traces and authoring/runtime contract parity for every configured template. | schema/branch/selection/injection parity receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | retired shapes, invalid conditions, missing required slots or silent authoring/runtime divergence must fail |
| `P4-MADLIB-MANUSCRIPT-1` | open | Medium | P4-MADLIB-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate configured manuscript variants and their injection provenance; audit token escaping, captions and output determinism in declared formats. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-MADLIB-PORTABILITY-1` | open | Medium | P4-MADLIB-DOMAIN-1; P4-MADLIB-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_madlib --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-MADLIB-REMOTE-1` | open | Medium | P4-MADLIB-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
