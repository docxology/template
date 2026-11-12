# template_redacted_report TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[monorepo review history](https://github.com/docxology/template/blob/main/docs/maintenance/exemplar-backlog-history.md#bounded-workflowz-reviews--2026-11-10) (not bundled in standalone exports)
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

- Keep rendered sanitized report outputs and development visual-proof outputs regenerated after style, steganography, or Kmyth build changes.

## Configurable-surface gaps

- Organization-specific marking taxonomies and review-role policies are intentionally limited to cleared, invented fixtures; a real policy needs a separately scoped owner-approved row.

## Documentation and signposting gaps

- Keep public safety boundaries visible in README, AGENTS, and manuscript prose.

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
| `P4-REDACTED-DOMAIN-1` | partial | Medium | REDACTED-VISUAL-1; pinned verified raster tools | Regenerate redaction raster evidence using invented public fixtures; verify redaction/mosaic/residual-risk/pixel controls against exact tool versions and source bytes. | native raster/pixel/region/residual-risk receipts with tool identities | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | visible residual text, changed pixels outside allowed regions, stale raster tools or actual private fixtures must fail |
| `P4-REDACTED-MANUSCRIPT-1` | open | Medium | P4-REDACTED-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate safe invented-fixture manuscript figures and final outputs; inspect print/raster accessibility and avoid unsupported guarantees of zero disclosure risk. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_redacted_report`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-REDACTED-PORTABILITY-1` | open | Medium | P4-REDACTED-DOMAIN-1; P4-REDACTED-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_redacted_report --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `REDACTED-VISUAL-1` | blocked-tool | Medium | Stable raster toolchain | Install or pin the required tool, or record its unavailable status; run the explicit visual gate only when tooling is pinned and attach a pixel regression manifest. | pixel regression manifest | `uv run pytest projects/templates/template_redacted_report/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | missing raster tool must report unavailable, not pass |

| `P4-REDACTED-REMOTE-1` | open | Medium | P4-REDACTED-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.

## Workflowz review — 2026-11-10: retained open request

The [immutable owner request](https://github.com/docxology/template_redacted_report/blob/669131e7b962a21ba5d85c2483dcd2d05566ccc0/TODO.md#L61-L65)
remains unchecked. Generic P4 proof-matrix or coverage acceptance does not prove
byline provenance for malformed configuration.

- [ ] `WFZ-RR-001` · ready · Minor · Make neutral-byline fallback explicit.
  - Outcome: an intentionally absent configuration may take a documented neutral-byline path, but present unreadable/malformed YAML or missing/invalid author fields must fail clearly rather than silently stamp `("Template Author", "")` into proof PDFs.
  - Evidence: `src/redacted_report/publication_meta.py::publication_author_and_date` catches every exception at lines 27–28; the module's own purpose is to source proof-page and steganography authorship from `manuscript/config.yaml`. The immutable review preserves the original complete evidence and probe.
  - Acceptance from the prepared standalone project root:
    ```bash
    python -I - <<'PY'
    import tempfile
    from pathlib import Path
    import redacted_report.publication_meta as publication
    original = publication._CONFIG_PATH
    try:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            publication._CONFIG_PATH = config
            config.write_text('authors: [{name: "Fixture Author"}]\npaper: {date: "2026-01-01"}\n')
            assert publication.publication_author_and_date() == ("Fixture Author", "2026-01-01")
            config.write_text("authors: [broken\n")
            try:
                publication.publication_author_and_date()
            except Exception as exc:
                assert str(exc), "configuration failure must be actionable"
            else:
                raise AssertionError("present malformed config silently produced a byline")
    finally:
        publication._CONFIG_PATH = original
    PY
    python -I -m pytest tests/test_visuals_proofs.py -q --no-cov
    ```
  - Negative controls: distinguish the malformed present file, present invalid/missing author fields, and deliberately absent configuration; the valid fixture must retain its exact configured author/date. Add focused behavioral coverage and regenerated proof metadata showing either that byline or the explicit configuration failure.
  - Dependencies/constraints: no new dependency; retain deterministic defaults and the fixed proof-matrix byte contract. Document any intentional standalone fallback; generic exception swallowing is not provenance evidence.
