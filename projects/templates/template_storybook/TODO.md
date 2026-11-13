# template_storybook TODO

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

- Keep story text in `content/story.yaml` and rendering behavior in `src/storybook/`.
- Keep every story page as a full-page illustration; no manuscript-style partial
  figures for the primary artifact.
- Page-level accessibility alt text is generated in
  `output/data/storybook_manifest.json`; keep it descriptive when page content
  changes.
- Keep script, test, documentation, and `.agents/` catalog listings generated
  or checked against disk so future forks cannot silently omit a surface.

## Documentation and signposting gaps

- Keep README examples clear that Stage 02 renders the storybook PDF, while
  Stage 03 renders the descriptive manuscript PDF.
- The deterministic contact sheet is generated at
  `output/figures/storybook_contact_sheet.png` for every Stage-02 render.

## Test and validator gaps

- Keep a raster contrast audit for direct text overlays, using real pixel math
  and recording per-page results in the manifest; extend the palette contract
  before adding new overlay modes.

## Workflowz review — 2026-11-10

These five requests remain **open**; generic P4 rows do not replace their
individual outcomes or negative controls. Preserve the immutable
[owner review at `aae579f0c3db2b53664b5d637e525698eb60f6b6`, `TODO.md:72–112`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/TODO.md#L72-L112).
Evidence links below refer to that reviewed revision; current source paths keep
the same `src/storybook/` owners. The named regression tests are required future
additions, not claims that those tests already exist or pass. Acceptance probes
run from the prepared standalone project root (or this canonical project's root
with its checkout SDK binding), not the monorepo root. Retaining these requests
does not implement a renderer repair or close any row.

- [ ] **TSB-20261110-01 — P1 — Make the direct-text contrast audit measure the rendered artifact.** Size: Medium.
  - **Outcome:** A direct-overlay image with no readable local text/background contrast can no longer pass merely because the declared ink color occurs somewhere in the raster. The full renderer continues to emit a contrast-audit record for every page in `output/data/storybook_manifest.json`.
  - **Evidence:** [`src/storybook/text_layout.py:44–59`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/text_layout.py#L44-L59) reads pixels only into a color set, computes contrast from hard-coded ink/shadow constants, and gates on global ink membership plus that declared ratio. This does not satisfy the [owner's real-raster direct-overlay audit contract](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/TODO.md#L43-L47). The review records that a solid `LIGHT_TEXT_RGB` image with `overlay_box=False` passes despite having no contrasting text or background.
  - **Next action:** Derive direct-text and adjacent-background samples from the actual rendered text mask/artwork, calculate local raster contrast, and fail unreadable cases; retain the declared-palette check separately where useful. Add `tests/test_contrast_audit.py::test_direct_overlay_rejects_flat_ink_field`, constructing a uniform `LIGHT_TEXT_RGB` PNG and an `overlay_box=False` `PageSpec`, and asserting that `audit_rendered_text_contrast` raises instead of returning success.
  - **Proving artifact:** The focused regression plus a freshly generated manifest from the complete PDF build.
  - **Acceptance probe:** `uv run --extra dev pytest tests/test_contrast_audit.py::test_direct_overlay_rejects_flat_ink_field && uv run python scripts/90_build_storybook_pdf.py`
  - **Negative control / dependencies / constraints:** The unchanged bundled story must build with a per-page audit entry. No dependency is required. Preserve the 4.5 minimum and the manifest's per-page audit surface; if real raster auditing exposes existing page failures, correct the text/art contrast in this row rather than weakening the threshold.

- [ ] **TSB-20261110-02 — P2 — Reject an empty story before creating output artifacts.** Size: Small.
  - **Outcome:** `pages: []` produces a descriptive configuration error from `load_storybook`, before any PDF, manifest, summary, contact sheet, or page image is created or replaced.
  - **Evidence:** [`src/storybook/story.py:87–93`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/story.py#L87-L93) accepts an empty list because its numbers equal `range(0)`. [`build_storybook_pdf`, lines 105–134](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/rendering.py#L105-L134) saves the PDF before the contact-sheet call reaches the [empty-image error at lines 67–68](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/rendering.py#L67-L68).
  - **Next action:** Add a non-empty-page invariant next to the existing list and contiguous-number checks. Add `tests/test_story.py::test_empty_pages_fail_at_load_before_outputs`: copy `content/` into a temporary project, set `pages` to `[]`, assert a `ValueError` identifying `pages`, and assert that no `output/` directory was created.
  - **Proving artifact:** The focused load-validation regression and a successful unchanged-story build.
  - **Acceptance probe:** `uv run --extra dev pytest tests/test_story.py::test_empty_pages_fail_at_load_before_outputs && uv run python scripts/90_build_storybook_pdf.py`
  - **Negative control / dependencies / constraints:** The bundled cover-plus-pages configuration must still load and build with contiguous numbering from page zero. No new dependency or output-layout change is needed.

- [ ] **TSB-20261110-03 — P2 — Validate complete hexadecimal palette colors during story loading.** Size: Small.
  - **Outcome:** Every palette entry is validated as exactly six hexadecimal RGB digits before rendering, and malformed values report the page/palette configuration error rather than a later raw integer-conversion failure.
  - **Evidence:** [`src/storybook/story.py:33–40`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/story.py#L33-L40) checks only list length, string type, and a leading `#`; for example `#12zz56` passes. [`src/storybook/illustration.py:18–20`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/illustration.py#L18-L20) subsequently parses slices with base 16, so the invalid configuration fails only during illustration.
  - **Next action:** Tighten `_palette` validation and include page context in its error. Add `tests/test_story.py::test_invalid_hex_palette_fails_at_load`, copying the real story, changing one color to `#12zz56`, and asserting failure from `load_storybook`; include a valid six-digit/mixed-case color as the passing control.
  - **Proving artifact:** The focused schema regression and a successfully rendered existing story page.
  - **Acceptance probe:** `uv run --extra dev pytest tests/test_story.py::test_invalid_hex_palette_fails_at_load && uv run python scripts/20_render_page_01.py`
  - **Negative control / dependencies / constraints:** The unchanged four-color story palettes must load and render. Do not add named colors, alpha channels, or new dependencies without separately defining their rendering contract.

- [ ] **TSB-20261110-04 — P2 — Keep configured outputs and manifest paths inside the declared project boundary.** Size: Medium.
  - **Outcome:** Absolute or parent-escaping `output_pdf` values are rejected before writing, and `RenderResult.to_dict(root=...)` fails closed rather than publishing an absolute checkout path for a result outside that root.
  - **Evidence:** [`src/storybook/story.py:95`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/story.py#L95) accepts any path text, while [`src/storybook/rendering.py:106–107`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/rendering.py#L106-L107) joins it to the root and creates its parent; an absolute path discards the root and `..` can escape it. This conflicts with the [original project-relative path statement](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/README.md#L83). Independently, [`src/storybook/models.py:85–98`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/models.py#L85-L98) promises that a checkout path never becomes publication metadata but falls back to returning `str(path)` outside the root.
  - **Next action:** Enforce a relative, non-escaping output-PDF path during loading and make rooted manifest serialization reject outside-root paths explicitly. Add `tests/test_story.py::test_output_pdf_cannot_escape_project_root` for both `../escaped.pdf` and an absolute target, asserting no target is created. Add `tests/test_rendering.py::test_manifest_paths_fail_closed_outside_root`, exercising `RenderResult.to_dict(root=...)` with an outside absolute result and an inside-root passing control.
  - **Proving artifact:** Both behavioral regressions and the normal manifest generated by a complete build.
  - **Acceptance probe:** `uv run --extra dev pytest tests/test_story.py::test_output_pdf_cannot_escape_project_root tests/test_rendering.py::test_manifest_paths_fail_closed_outside_root && uv run python scripts/90_build_storybook_pdf.py`
  - **Negative control / dependencies / constraints:** Existing relative outputs and the scripts' `--project-root` override must continue working, and normal manifest paths must remain project-relative. Resolve containment without requiring the destination file to exist; no network, dependency, or board prerequisite applies.

- [ ] **TSB-20261110-05 — P3 — Reject misspelled or undeclared trim-size labels.** Size: Small.
  - **Outcome:** Only `custom` and keys declared in `TRIM_SIZES` load successfully; named sizes retain their dimensions check, while a typo fails at configuration time instead of silently behaving as custom metadata.
  - **Evidence:** [`src/storybook/story.py:98–103`](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/story.py#L98-L103) validates any non-empty string but checks dimensions only when the value occurs in [`TRIM_SIZES`, lines 44–48](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/src/storybook/story.py#L44-L48). Thus `portriat` bypasses the portrait contract. The [original configurable-surface contract](https://github.com/docxology/template_storybook/blob/aae579f0c3db2b53664b5d637e525698eb60f6b6/TODO.md#L28-L34) requires a future trim variant to add a schema value and its rendering/negative-control coverage, and limits current caption placement to top and bottom zones.
  - **Next action:** Add an explicit allowed-label check while retaining arbitrary positive dimensions for `custom`. Add `tests/test_story.py::test_unknown_trim_size_rejected` using a copied story with `trim_size: portriat`, and `tests/test_story.py::test_named_and_custom_trim_sizes_remain_valid` to exercise one matching named geometry and one custom geometry.
  - **Proving artifact:** The two focused schema regressions and a normal page render using the repository configuration.
  - **Acceptance probe:** `uv run --extra dev pytest tests/test_story.py::test_unknown_trim_size_rejected tests/test_story.py::test_named_and_custom_trim_sizes_remain_valid && uv run python scripts/20_render_page_01.py`
  - **Negative control / dependencies / constraints:** Preserve the bundled story's configured dimensions and both current operating modes (`custom` and declared named sizes). This is validation only: no new trim geometry, raster redesign, or dependency upgrade is in scope. Future caption zones likewise require a separately defined schema, accessibility, and raster-contrast contract.

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

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P4-STORYBOOK-DOMAIN-1` | partial | Medium | P4-REQUIRED-PROFILE-DEFINITION-1; native producer contract; pinned image/font/print tools | Regenerate every configured page, contact sheet, alt text, source-bound manifest and print PDF; independently check page completeness and actual print-size visual quality. | page/contact-sheet/manifest/alt-text and native print/raster receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | missing pages, wrong image sources, inaccessible artwork, incorrect trim/bleed or stale print artifacts must fail |
| `P4-STORYBOOK-MANUSCRIPT-1` | open | Medium | P4-STORYBOOK-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Inspect page composition, typography and narrative continuity at print scale; validate content/configuration/manifest parity and all declared formats. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_storybook`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-STORYBOOK-PORTABILITY-1` | open | Medium | P4-STORYBOOK-DOMAIN-1; P4-STORYBOOK-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_storybook --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-STORYBOOK-REMOTE-1` | open | Medium | P4-STORYBOOK-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
