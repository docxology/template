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
| Format renderers | `slides_renderer.py`, `web_renderer.py`, `_web_postprocess.py`, `pandoc_renderers.py`, `pptx_deck.py`, `slide_deck.py`, `mermaid_figure.py` | Slides, HTML orchestration and deterministic HTML post-processing, DOCX, EPUB, PPTX deck rendering, slide deck helpers, and Mermaid figure rendering. |
| Pandoc filters | `_pandoc_filters.py`, `formalism.lua`, `convert_latex_images.lua`, `_beamer_allowframebreaks.lua` | `_pandoc_filters.py` resolves the repo-shipped Lua filters for every writer; `formalism.lua` numbers Definition/Proposition/Theorem blocks and resolves `[@def:...]`. |
| Manuscript source | `manuscript_discovery.py`, `manuscript_injection.py`, `_manuscript_source.py`, `manuscript_composition.py` | Section ordering, substitutions, resolved manuscript trees, and render-boundary composition evidence (`manuscript_composition.py` writes the ordered-input/combined-output digest receipt at `output/reports/manuscript_composition.json`, derived from the exact ordered inputs each combined writer just consumed). |
| LaTeX support | `latex_utils.py`, `latex_package_validator.py`, `preflight.py` | Compilation and package checks. |
| LaTeX checks | `latex_discovery.py`, `latex_validation.py`, `latex_log_quality.py`, `latex_texttt.py` | `kpsewhich`/per-package discovery, required/optional package `ValidationReport`, render-log findings for overfull/underfull boxes and undefined references, and rewriting long `\texttt{}` spans into a breakable monospace macro. |
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
- `pptx_deck.render_pptx()` normalizes OOXML ZIP-member timestamps after
  `python-pptx` saves the package. Do not remove that pass: identical decks
  must remain byte-identical, not merely content-equivalent.
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
