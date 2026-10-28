# template_pitch_deck TODO

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

- Keep PPTX ZIP-member timestamps normalized and require two-run PDF/PPTX
  digest equality in the deterministic artifact gate.
- Keep all three lengths in the raster QA matrix and fail on clipping or overlap
  when the configured raster toolchain is available.
- Keep Mermaid rendering fail-closed: the repository-pinned `mmdc` plus
  Chrome/Chromium must regenerate every declared diagram, and an unavailable
  tool must fail Stage 02 rather than leave tracked diagram bytes stale.
- Keep publication DOI/repository metadata source-bound and distinguish an
  unavailable deposit from a real owner-authorized publication receipt.
- Content-slide figures flow below their bullet body in both output formats, and `_preflight_all_lengths` audits every configured length before writing any artifact.
- QR annotations are structurally checked against the configured standalone target. A real publication or device-scan check remains an external release concern and must not be inferred from local raster output.

## Configurable-surface gaps

- The `deck.pitch_subject` and `deck.subjects` configuration selects the
  authored subject and content prefix; a fork may add another subject without
  changing the renderer or token path-safety contract.
- Theme is currently monochrome-red (black + white + 3× the same highlight, `manuscript/config.yaml`'s `deck.theme` block); `config.yaml.example` demonstrates a distinct 3-accent palette as a starting point for forks.
- `SlideBudget` (short/medium/long max-slide counts, currently 11/38/58) lives in `infrastructure/rendering/slide_deck.py`, not per-project config — a fork wanting different length budgets currently edits the shared infrastructure constant.

## Documentation and signposting gaps

- `manuscript/README.md` and `src/README.md` are new, minimal — expand with worked examples if this exemplar gains a second pitch subject.
- No architecture diagram doc yet beyond the in-deck Mermaid figure itself; consider a `docs/architecture.md` mirroring `template_newspaper`'s.

## Test and validator gaps

- Keep deterministic generated-sequence tests proving budget filtering is
  prefix-preserving and non-mutating across boundary and oversized decks.
- `mermaid_figure.py`'s real-render tests are skipped when `mmdc` is absent; CI coverage of that path depends on the runner having mermaid-cli installed.
- Keep adversarial token sequences in the regression suite so generated decks
  cannot leak unresolved braces.

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
| `P4-PITCH-DOMAIN-1` | partial | Medium | P4-PUBLIC-REFERENCE-1; native slide/PDF/PPTX tools | Verify every configured short/medium/long PDF-PPTX pair, diagrams, citations, QR targets, native format parity and deterministic archive metadata; recompute infrastructure facts from admitted Root content. | native paired-slide/content/QR/archive and source-count receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | missing pairs, content drift, wrong QR URLs, nondeterministic archive metadata or ambient forged Git counts must fail |
| `P4-PITCH-MANUSCRIPT-1` | open | Medium | P4-PITCH-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate every deck length, chart, diagram and archive; inspect actual projected/print typography and layout with matching configuration/citation provenance. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_pitch_deck`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-PITCH-PORTABILITY-1` | open | Medium | P4-PITCH-DOMAIN-1; P4-PITCH-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_pitch_deck --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-PITCH-REMOTE-1` | open | Medium | P4-PITCH-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
