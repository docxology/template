# Rendering Package

## Purpose

Rendering turns manuscript sources and project outputs into publication formats:
combined PDFs, slides, web HTML, DOCX, and EPUB. It coordinates format-specific
renderers without owning validation policy or project analysis.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Facade | `core.py`, `config.py` | `RenderManager` and rendering configuration. |
| PDF pipeline | `pdf_renderer.py`, `_pdf_combined_*.py`, `_pdf_title_page.py`, `_pdf_latex_helpers.py` | Combined PDF assembly, title/publishing pages, LaTeX helpers. |
| Format renderers | `slides_renderer.py`, `web_renderer.py`, `pandoc_renderers.py` | Slides, HTML, DOCX, EPUB. |
| Manuscript source | `manuscript_discovery.py`, `manuscript_injection.py`, `_manuscript_source.py` | Section ordering, substitutions, resolved manuscript trees. |
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
- Raw-LaTeX theorem-like environments (`\begin{theorem|lemma|proposition|`
  `corollary|definition}`) render in the PDF via the manuscript preamble's
  `\newtheorem` definitions. Pandoc's HTML writer cannot, so `web_renderer.py`
  rewrites them **web-only** (`_html_theorem_blocks`) into numbered, shared-counter
  `.theorem-box` Divs styled by the embedded CSS; the PDF/slides paths are
  untouched. Authors keep writing `\begin{theorem}` — no portable-Div syntax needed.

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
