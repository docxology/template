# template_advanced_literature_review TODO

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

- Keep the offline corpus clearly marked as synthetic; live DOI sources require source-tier provenance and attribution in README, manuscript, and generated-output prose.
- Keep `output/data/phase_artifact_manifest.json` phase-aware for every corpus,
  metadata, and validation artifact; extend it before adding a new artifact
  family.
- Keep cross-phase conflict and knowledge-graph calibration validators explicit;
  structural evidence must never be presented as an empirical result.
- Keep `data/subfield_defaults_exoplanet.yaml` tied to project-local configuration, not borrowed from sibling exemplars.

## Configurable-surface gaps

- Retargeting should remain config-owned through `manuscript/config.yaml` phase definitions; avoid hard-coded domain terms in multi-phase `src/` modules.
- Keep phase temporal boundaries, filtering criteria, and LLM prompts explicit and configurable.
- New domains remain config-defined through phase records; a future phase shape
  must be accepted without code changes and covered by a scoped contract row.

## Documentation and signposting gaps

- Keep README, AGENTS, and `docs/_generated/exemplar_roster.md` synchronized through the generator.
- Keep multi-phase architecture guidance distinct from single-term capabilities and bind it to current execution.
- Keep troubleshooting examples specific to multi-phase scenarios (phase filtering failures, cross-phase validation conflicts).

## Multi-Phase Specific Considerations

- **Phase Definition Discipline**: New phases should have clear temporal boundaries, distinct methodological focus, and appropriate filtering criteria.
- **Cross-Phase Validation**: Later phases should validate, not merely supplement, earlier phase findings.
- **LLM Filter Calibration**: Abstract content filtering requires domain-specific calibration datasets for reliable precision/recall.
- **Temporal Coherence**: Phase-aware statistics must handle temporal overlaps and methodological transitions gracefully.

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
| `P4-ARL-DOMAIN-1` | partial | Medium | ARL-CROSS-PHASE-1; ARL-PHASE-PROVENANCE-1; genuine Meta provider | Execute enabled unpaid retrieval phases, deduplication, screening calibration and local-model classification with licensed fulltext custody; verify phase outputs and cross-phase assertions independently. | real retrieval/classification/calibration receipts and licensed phase manifests | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | missing licenses, unbound cross-phase assertions, invalid screening decisions or forged model responses must fail |
| `P4-ARL-MANUSCRIPT-1` | open | Medium | P4-ARL-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate phase diagrams, evidence tables, bibliography and hydrated manuscript from actual phase outputs; retain explicitly unpublished metadata until genuine first-publication receipts exist. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_advanced_literature_review`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-ARL-PORTABILITY-1` | open | Medium | P4-ARL-DOMAIN-1; P4-ARL-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_advanced_literature_review --python "3.12=$P4_PYTHON312" --python "3.13=$P4_PYTHON313" --python "3.14=$P4_PYTHON314"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `ARL-CROSS-PHASE-1` | blocked-external | Medium | Domain assertion provenance and retrieval/source revision receipt | Obtain a domain-calibration or live-retrieval receipt that binds each cross-phase assertion to a source revision; retain the deterministic conflict gate as the local prerequisite. | source-bound cross-phase calibration receipt | `uv run pytest projects/templates/template_advanced_literature_review/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | structural overlap or an assertion without source provenance must not count as causal support |
| `ARL-PHASE-PROVENANCE-1` | blocked-external | Medium | Live retrieval/full-output provenance inputs | Run the full opt-in retrieval/output-tree audit with current source and provider evidence, then attach a phase manifest with verified hashes and producer revision. | source-bound full-output phase manifest | `uv run pytest projects/templates/template_advanced_literature_review/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | an unlisted artifact, stale hash, or missing phase owner must fail |

| `P4-ARL-REMOTE-1` | open | Medium | P4-ARL-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
