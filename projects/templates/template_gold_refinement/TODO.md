# template_gold_refinement TODO

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

- Keep the refinery pipeline (ore → smelting → assaying → cupellation →
  nine-nines certification) as the gated default path, with purity monotonic
  across stages.
- Keep mega-madlib token injection deterministic, seeded, and config-owned
  (lexicon in config, no hardcoded selections).
- Keep `src/template_gold_refinement/evidence.py` cross-checking every manuscript contribution claim
  against its evidence source, including dotted Python member paths.
- Transmission bookends (`transmission_begin` / `transmission_end`) frame the
  certified output and remain validated as a pair.
- Preserve the no-mocks / deterministic-seed policy for any new refinery stage
  or assay probe.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the declared config blocks
  (`contribution_claims`, `pipeline_phases`, `audit_rules`, `steganography`,
  `evaluation`, `authoring_contract`, and explicit LLM-review gates) when code
  defaults change.
- The prefix-constrained reverse assay uses the config-selected target and
  generated report surface; forks must preserve ordered-prefix semantics.
- The noncompensatory `PurityVector` remains domain-selectable only when a fork
  supplies evidence for the added dimensions.

## Documentation and signposting gaps

- Keep README and AGENTS clear that Stage 02 generates figures and the
  evidence/figure registries while Stage 03 renders the certified manuscript.
- Keep `docs/domain_fork_guide.md` and `src/template_gold_refinement/domain_adapter.py` cross-linked so
  forkers can remap stages (clinical evidence, legal citation, engineering spec).
- Keep the analogy-break boundary documented: where gold-refining fails as a
  model for manuscript composition.

## Test and validator gaps

- Platform references remain an external-evidence concern; do not promote the
  publishing-status block without source-bound records for each platform.
- The analogy-boundary theorem is a local design predicate, not evidence of
  manuscript quality or a substitute for domain validation infrastructure.
- Integration with real manuscript validation and real-paper measurement is
  outside this deterministic toy exemplar until a licensed, owner-approved
  source and claim ledger are supplied.

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
| `P4-GOLD-DOMAIN-1` | partial | Medium | P4-EXEMPLAR-OWN-COVERAGE-1; prepared local provider for explicit reviews | Independently recompute refinement calculations, token/claim support and figure inputs; execute local reviews only when enabled and bind actual reviewed source and transcripts. | independent refinement/claim/token calculations and real optional-review receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | unsupported claims, changed token accounting, incorrect refinement results or forged review bytes must fail |
| `P4-GOLD-MANUSCRIPT-1` | open | Medium | P4-GOLD-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate every refinement figure and evidence table; bind manuscript variables, citations and review labels to supported outputs and configuration. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_gold_refinement`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-GOLD-PORTABILITY-1` | open | Medium | P4-GOLD-DOMAIN-1; P4-GOLD-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_gold_refinement --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-GOLD-REMOTE-1` | open | Medium | P4-GOLD-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
