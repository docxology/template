# Rendering Package

## Purpose

Rendering turns manuscript sources and project outputs into publication formats:
combined PDFs, slides, web HTML, DOCX, and EPUB. It coordinates format-specific
renderers without owning validation policy or project analysis.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Facade | `core.py`, `config.py` | `RenderManager` and rendering configuration. |
| Security profile | `security.py` | Trusted-local and isolated untrusted subprocess options, credential-free environments, and bounded output roots. |
| PDF pipeline | `pdf_renderer.py`, `_pdf_combined_*.py`, `_pdf_title_page.py`, `_pdf_latex_helpers.py` | Combined PDF assembly, title/publishing pages, LaTeX helpers. |
| Format renderers | `slides_renderer.py`, `_slides_accessibility.py`, `_slides_accessibility_ast.py`, `_slides_accessibility_composition.py`, `_slides_accessibility_contracts.py`, `_slides_accessibility_tables.py`, `_slides_accessibility_text_geometry.py`, `_slides_math_header.py`, `_slides_tex_figures.py`, `_slides_codelisting.py`, `_slides_framebreaks.py`, `web_renderer.py`, `_web_markdown_preprocess.py`, `_web_postprocess.py`, `_web_figure_details.py`, `docx_renderer.py`, `epub_renderer.py`, `pptx_deck.py`, `slide_deck.py`, `_slide_draw.py`, `mermaid_figure.py` | Slides, opt-in semantic accessible-slide composition and fail-closed geometry, Beamer math-header and figure-path helpers, profile-aware captioned listings and archive frame splitting, HTML orchestration, web-only Markdown preprocessing (citations/theorems), deterministic HTML post-processing and structured figure-detail association, dedicated DOCX and EPUB rendering, PPTX deck rendering, slide deck helpers, and Mermaid figure rendering. |
| Pandoc filters | `_pandoc_filters.py`, `formalism.lua`, `convert_latex_images.lua`, `_beamer_allowframebreaks.lua` | `_pandoc_filters.py` resolves the repo-shipped Lua filters for every writer; `formalism.lua` numbers Definition/Proposition/Theorem blocks and resolves `[@def:...]`. |
| Bibliographies | `_bibliography.py`, `_pdf_combined_bibliography.py` | Shared sorted `manuscript/*.bib` discovery, repeated/symlink-path deduplication, duplicate-key rejection, Pandoc arguments, and PDF bibliography injection. |
| Manuscript source | `manuscript_discovery.py`, `manuscript_injection.py`, `_manuscript_source.py`, `manuscript_composition.py`, `render_cache.py` | Section ordering, substitutions, resolved manuscript trees, render-boundary composition evidence (`manuscript_composition.py`), and modular section caching (`render_cache.py`). |
| LaTeX support | `latex_utils.py`, `latex_package_validator.py`, `preflight.py` | Compilation and package checks. |
| LaTeX checks | `latex_discovery.py`, `latex_validation.py`, `latex_log_quality.py`, `latex_texttt.py` | `kpsewhich`/per-package discovery, required/optional package `ValidationReport`, render-log findings for overfull/underfull boxes and undefined references, and rewriting long `\texttt{}` spans into a breakable monospace macro. |
| docxplus export (opt-in) | `docxplus_export.py`, `docxplus_stage.py` | Exports a project as a conforming `.docx` that also carries its own source tree in a signed manifest. The container format is imported from upstream ([docxology/docxplus](https://github.com/docxology/docxplus)), never vendored; both modules skip cleanly when the optional `docxplus` extra is absent. |
| Ebook formats | `ebook_bundle.py`, `ebook_stage.py`, `mobi_renderer.py` | `EbookBundleManager.generate_all` ties EPUB/MOBI/DOCX plus metadata together; `ebook_stage.py` is the opt-in ebook stage orchestrator; `mobi_renderer.py` renders MOBI via a pandoc EPUB intermediate and calibre `ebook-convert`. |
| Executable bundle | `dockerfile_gen.py`, `manifest.py` | Deterministic reproducible-build Dockerfile generation (pinned base image and `uv` version) and the Stage-10 `manifest.json` of pinned numerical claims, git metadata, and build environment. |
| CLI | `cli.py`, `render_all_cli.py` | Module commands and legacy all-format entrypoint. |

## Boundaries

- Project analysis outputs are inputs; rendering must not compute project
  results.
- Rendering may call narrow validation preflight leaves, but must not import
  broad validation orchestrators.
- Fix manuscript syntax or artifact producers upstream; do not patch generated
  LaTeX/PDF output by hand.
- `FIGURE_WIDTH_*` values must stay bare fractions, and figure alt-text comments
  belong before `\begin{figure}`.
- PDF metadata and publishing information come from
  `projects/{name}/manuscript/config.yaml`.
- Configured title-page artwork uses `paper.cover.image`/`paper.cover.alt` or
  the parallel `book.cover.*` fields. With `metadata.tagged_pdf: true`, the
  selected cover's `alt` must be a non-empty string; validation fails before a
  prior combined PDF is replaced. The renderer requests PDF 2.0 tagging and
  catalog language through LuaLaTeX while deliberately omitting a PDF/UA
  conformance identifier. Tagged structure is not PDF/UA certification.
- Combined EPUB uses the same selected cover/alt pair and rejects a cover with
  missing or blank alt text before Pandoc runs. After Pandoc emits its SVG
  cover, `_epub_cover_accessibility.py` names the SVG graphic from the source
  alt, hides the nested bitmap from duplicate announcement, and the bounded
  package validator verifies XHTML/SVG image references and accessible names
  before the renderer retains the EPUB.
- EPUB package identity and container metadata are deterministic. The renderer
  gives Pandoc a placeholder, validates archive bounds before payload reads,
  then derives UUIDv5 from canonical member names and uncompressed bytes with
  only the OPF/NCX identifier values normalized out. Bibliography, body-media,
  filter, metadata, and tool changes therefore affect identity when they affect
  the effective package; identifier overrides are rejected. OPF
  `dc:identifier` and NCX `dtb:uid` agree. A valid caller
  `SOURCE_DATE_EPOCH` controls `dcterms:modified` and therefore participates in
  identity; absent or invalid values use `1980-01-01T00:00:00Z`. Ambient Git and
  wall-clock state are not consulted. Pandoc writes a fresh temporary target,
  and the final atomic ZIP rewrite preserves order, compression, comments,
  permissions, and EPUB's first uncompressed `mimetype` member while
  normalizing member timestamps.
- Body-figure alternatives come from `output/figures/figure_registry.json`,
  using either top-level `alt` or `metadata.alt_text`. Combined and per-section
  HTML replace Pandoc's caption-derived image alternative only when the
  rendered label and figure path exactly match the registry; blank metadata or
  a present label/path disagreement fails the render. Non-empty authored alt
  remains valid for unregistered figures and is never overwritten from the
  visible caption. The same exact registry text replaces body-image `alt`
  options only on the opt-in `metadata.tagged_pdf: true` LuaLaTeX path.
  Untagged PDFs are unchanged, and neither tagged rendering nor metadata
  injection is a claim of PDF/UA certification.
- Figure-registry 1.2 records may add a structured `long_description` and an
  `exact_value_fallback`. The renderer associates long descriptions through
  `aria-details`, validates the exact-value identifier inventory and its safe
  `output/figures` companion paths, and emits contextual links without merging
  the concise alt, visible caption, detailed description, or numerical table.
  Older label-keyed and project-versioned registry shapes remain supported.
- Publication HTML confines wide tables, code, and displayed mathematics to
  their own keyboard-scrollable regions. The document body cannot scroll
  horizontally at reflow zoom, and full-resolution figure links have
  contextual accessible names. This is an accessibility-enhanced reader
  contract, not a WCAG conformance claim.
- Local-audit-only figures may be authored under the sibling
  `output/audit_figures/` directory and referenced as `../audit_figures/...`
  from the hydrated manuscript. PDF path normalization preserves that
  directory instead of silently mapping the asset into public
  `output/figures/`; authored alternatives remain required for unregistered
  non-decorative audit figures. Audit assets are not added to the public
  figure registry or release bundle merely because they render successfully.
- Combined PDF and HTML, Beamer and Reveal.js slides, DOCX, EPUB, and the opt-in
  ebook stage consume the same filename-sorted union of top-level
  `manuscript/*.bib` files. Repeated or symlinked paths are passed once;
  duplicate and case-only variant citation keys within or across databases
  raise before BibTeX and citeproc can choose different definitions. Do not
  concatenate or rewrite manuscript bibliography sources during rendering.
  Section-level slide decks resolve
  inline citations but suppress repeated reference lists.
- `render.slides.profile: accessible` is opt-in; `archive` remains the default
  and retains the historical renderer. Accessible mode composes both Reveal.js
  and Beamer from one Pandoc JSON AST, splits only between semantic blocks,
  bounds prose at 80 words and displayed tables at eight body rows, allocates
  at least 70% of a figure-led frame to the figure, and enforces native
  title/body/figure-label floors of 28/20/16 points on an explicit 16:9 Beamer
  projection canvas. A source block that cannot
  satisfy those bounds fails with a stable `slides.*` diagnostic instead of
  shrinking or character-count splitting. Dense tables retain a contiguous
  whole-row excerpt when geometry permits. Before line-height pricing, ordinary
  prose tokens receive wide-glyph-aware physical-column minima at real TeX
  whitespace/hyphen break points. Long inline code is discounted only when its
  source serializes to the simple brace-free `texttt` body the downstream
  `breaktt` pass rewrites; braced literal encodings stay indivisible. Overlapping
  contiguous spans are solved jointly. If those minima exceed the frame,
  `slides.density.indivisible-table-width` fails before LaTeX with the first
  offending token and exact required/available width units. When even one
  complete row cannot fit vertically, `slides.density.indivisible-table` stops
  the paired render with exact geometry instead of publishing a diagnostic
  frame, shrinking, clipping, or fragmenting a row. Persistent frame navigation
  links the complete table and caption in canonical HTML.
  The accessible parse resolves bibliography citations before geometry is
  priced, retains citation prefixes/suffixes, and leaves cross-reference
  citations intact; a resolved mixed citation substitutes each unresolved
  cross-reference placeholder once rather than appending a duplicate debit.
  Complete prose and title packing uses the same proportional glyph/space
  metric, including section dividers. Hard line breaks, rich
  list/definition/quote structure, code-block physical lines, and supported
  `aligned`/`substack` mathematical rows contribute to horizontal and vertical
  demand. Unknown layout-affecting math, projected
  footnotes, arbitrary raw TeX outside the theorem/reference allowlist, optional
  physical math-row spacing, or unmodelled rich table-cell blocks fail with
  stable diagnostics. Notes and geometry checks apply to headings as well as
  body blocks. Loose-list paragraphs and definition-entry block boundaries are
  priced explicitly; omitted complete-table footers never consume excerpt rows.
  Projected captioned listings retain an empty caption, counter, and label while
  canonical HTML retains the complete source caption. Width diagnostics prefer
  an individually impossible column over an unrelated active span, then report
  exact span provenance when the joint constraint is the cause.
  Long-code discounts additionally require an installed `seqsplit.sty`; archive
  mode retains its historical graceful fallback, including Pandoc's brace-free
  `\ ` control-space rewrite. The 20-point accessible body
  floor applies to nested lists, quotes, code listings, and algorithm stand-ins,
  not only top-level prose.
  Reveal.js is the keyboard-operable,
  long-description-bearing presentation reader; dense captions and complete
  tables link to the canonical manuscript HTML. Beamer remains an explicitly
  labelled untagged presentation derivative. Neither a successful render nor
  these design constraints establish WCAG or PDF/UA conformance.
- Canonical Stage 03 rendering emits one exact `*_slides.pdf` and
  `*_slides.html` pair per eligible source only in `accessible` mode. The pair
  is transactional: both derivatives consume the same composed AST, and a
  failure in either renderer removes both public outputs. `archive` mode keeps
  its historical Beamer-required, Reveal-optional behavior. Stage 03, Stage 04,
  and Stage 05 validation must carry the effective profile and enforce that
  distinction.
- `pptx_deck.render_pptx()` normalizes OOXML ZIP-member timestamps after
  `python-pptx` saves the package. Do not remove that pass: identical decks
  must remain byte-identical, not merely content-equivalent.
- Generic PDF/PPTX decks share the exact ReportLab Helvetica title metric and
  one explicit content-line plan from `slide_deck.py`. Both renderers must
  validate fitted titles, unbreakable words, and the protected footer/QR band
  before creating or replacing a target; do not reintroduce format-local
  character-count or text-box-height estimates. Diagram figures likewise use
  one aspect-preserving fit inside the shared header/footer-safe content box;
  section-divider title and rule bands must remain structurally disjoint in
Bands that overlap produce invalid geometry and are detected during layout validation, which then fails.
  both formats; rendering fails when title fit is missing or slide text enters
  the protected footer band, raising `RenderingError` before any deck is
  written. Overlapping divider bands are the known-wrong layout the slide
  layout tests assert neither format can emit.
- `formalism.lua` must be applied by **every** writer that applies
  `pandoc-crossref`, and always **before** it and before `--citeproc`: the
  combined PDF (`_pdf_combined_pandoc.py`), combined DOCX and EPUB
  (`_combined_exports.py`), combined HTML (`web_renderer.py`), and the opt-in
  ebook stage (`ebook_stage.py`). Numbering must be identical across editions,
  and the filter has to consume its `[@def:...]` citations before `--natbib`
  turns them into `\citep` and ships "[?]". Add it through
  `_pandoc_filters.formalism_filter_args()`, never by hand-writing the path;
  `tests/infra_tests/rendering/test_formalism_wiring.py` reads the constructed
  command line of each writer and fails if one drops it.
- `pandoc-crossref` is an optional external binary, so a missing one warns and
  continues. `formalism.lua` ships with the repo, so a missing one **raises**
  `FormalismFilterMissingError` — degrading to unnumbered output while exiting
  zero is the failure mode that policy exists to prevent. The error is
  deliberately a `RuntimeError` so the DOCX/EPUB warning handlers cannot
  swallow it.
- `render_cache.py` is a local acceleration cache, never publication evidence.
  Its entries use path-aware keys rather than basenames, require an exact list
  of regular-file outputs, and reject malformed or unwritable cache state with
  a `RenderCacheError`. Callers must regenerate a render when the cache is
  missing or invalid.
- The per-section HTML path (`WebRenderer.render`) intentionally gets neither
  filter: it pre-converts citations and renders sections standalone, where
  restarted numbering would be misleading.
- Raw-LaTeX theorem-like environments (`\begin{theorem|lemma|proposition|`
  `corollary|definition}`) render in the PDF via the manuscript preamble's
  `\newtheorem` definitions. Pandoc's HTML writer cannot, so `web_renderer.py`
  rewrites them **web-only** (`_html_theorem_blocks`) into numbered, shared-counter
  `.theorem-box` Divs styled by the embedded CSS; the PDF/slides paths are
  untouched. That path still works, but it numbers PDF and web independently and
  supports no `[@label]` resolution, so the portable `::: {.definition #def:x}`
  form handled by `formalism.lua` is the preferred authoring syntax — it is the
  only one whose numbering is identical across every edition.

## Public Commands

```bash
uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project
uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .
uv run python -m infrastructure.rendering.latex_package_validator
uv run python -m infrastructure.rendering.cli pdf manuscript.tex
uv run python -m infrastructure.rendering.cli slides presentation.md --format beamer
uv run python -m infrastructure.rendering.cli web manuscript.md
```

## Tests

```bash
uv run pytest tests/infra_tests/rendering -q
uv run pytest tests/infra_tests/rendering/test_slides_accessibility.py -q -m slow
uv run pytest projects/templates/template_textbook/tests/test_mermaid.py -q
```

Use `-m 'not requires_latex'` only when verifying code paths that do not need a
local TeX engine. If rendering behavior changes, run at least one real
`scripts/pipeline/stage_03_render.py` command for a public exemplar.

## Failure Triage

- Missing `*.sty`: run package validator and install the named TeX package.
- Mermaid failures: check comment syntax, stadium node closing, and Chrome/mmdc
  availability before changing fallback behavior.
- Forward-reference or math errors: inspect the first LaTeX pass and keep
  multi-pass continuation behavior unless the output file is absent.
- Missing figures: fix artifact paths or analysis producers, then rerender.

## See Also

- [`README.md`](README.md)
- [`References/README.md`](References/README.md)
- [`../validation/AGENTS.md`](../validation/AGENTS.md)
