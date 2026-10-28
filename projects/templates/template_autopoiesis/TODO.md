# template_autopoiesis TODO

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

- Keep the grammar the single source of truth in `manuscript/config.yaml` (`autopoiesis:` block) and all generation logic in `src/` (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- Keep materialization routed through `src/template_autopoiesis/manuscript/emit_templates.py::emit_all` for
  every child-facing analysis, test, project, and manuscript file so standalone
  emitters and generated children cannot drift silently.
- Keep provenance recompute-based: verification must re-derive the tree hash from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Keep the placeholder-safe `manuscript/config.yaml.example` synchronized with the live config shape, including the list-form slot and dependency syntax.
- The optional `archetype_filters` mapping is the fork-owned selector for materializing a subset of the combinatoric product space; keep its values schema-validated and included in the grammar digest.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and materializes/verifies children, while Stage 03 renders the descriptive manuscript PDF.
- `SPEC.md` Phase 10 and `manuscript/preamble.md` are source-owned inputs to the deterministic manuscript contract; keep the checklist, explicit fences, and renderer-qualified receipt synchronized.

## Dependency-mode gaps

- `dep_mode="template"` remains intentionally loud (`NotImplementedError`) until a seam contract is defined that does not require parent infrastructure at child runtime.

## Test and validator gaps

- Keep figure fallback handling explicit for empty arrays, and require
  malformed or under-specified grammar shapes to fail before expansion with real
  negative controls.
- Keep mutation coverage per domain and permit an explicit skip only when a domain has no negative-control primitive; a second primitive must be used when available so the meta-gate cannot become green-by-construction.

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
behavior and at least 90% branch-aware combined statement and branch coverage; a focused test or previous revision's
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
| `P4-AUTO-MANUSCRIPT-1` | open | Medium | reviewed per-project render/native producer contracts and prepared tools | Regenerate grammar/child summaries, figures and hydrated manuscript; reconcile SPEC and preamble fences with actual renderer-qualified output and deterministic child artifacts. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_autopoiesis`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-AUTO-PORTABILITY-1` | open | Medium | P4-AUTO-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_autopoiesis --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `AUTOPOIESIS-SPEC-1` | blocked-tool | Medium | Pinned renderer and visual QA toolchain | Install or pin the renderer, or record its unavailable receipt; run the explicit Phase 10 visual gate and attach the tool-qualified receipt. | `SPEC.md` Phase 10 checklist + renderer receipt | `uv run pytest projects/templates/template_autopoiesis/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | missing renderer must report blocked-tool; fenced preamble/spec mismatch must fail |

| `P4-AUTO-REMOTE-1` | open | Medium | P4-AUTO-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
