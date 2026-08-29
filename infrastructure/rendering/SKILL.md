---
name: infrastructure-rendering
description: Skill for the rendering infrastructure module providing multi-format output generation including PDF manuscripts, HTML web pages, and Beamer/Reveal.js slides. Use when rendering research outputs, converting markdown to PDF, generating slides, or configuring LaTeX rendering.
---

# Rendering Module

Multi-format output generation for research manuscripts. Converts markdown source into professional PDFs, HTML, and slides.

## RenderManager (`core.py`)

The primary entry point for all rendering operations:

```python
from pathlib import Path
from infrastructure.rendering import RenderManager, RenderingConfig

# Default configuration (loaded from environment)
renderer = RenderManager()

# Custom configuration
config = RenderingConfig()  # configure attributes as needed
renderer = RenderManager(
    config=config,
    manuscript_dir=Path("projects/my_project/manuscript"),
    figures_dir=Path("projects/my_project/output/figures"),
)

# Render a single source file (.md or .tex)
renderer.render_pdf(source_file)
renderer.render_web(source_file)        # standalone HTML
renderer.render_slides(source_file)     # beamer (PDF) by default
renderer.render_all(source_file)        # archive md → Beamer + web; tex → PDF

# Render combined manuscript from multiple ordered source files
renderer.render_combined_pdf(source_files, manuscript_dir, project_name="my_project")
```

## Rendering Configuration (`config.py`)

```python
from infrastructure.rendering import RenderingConfig

config = RenderingConfig()
# Configure PDF, HTML, slides options
```

For projection-scale slides, explicitly select the accessible profile. The
archive profile remains the default for backwards compatibility:

```python
config = RenderingConfig(
    slides_profile="accessible",
    slides_max_prose_words=80,
    slides_max_table_rows=8,
    slides_min_figure_area_percent=70,
    slides_title_font_pt=28,
    slides_body_font_pt=20,
    slides_figure_label_font_pt=16,
    slides_reader_href="../web/index.html",
)
```

Accessible mode splits only at Pandoc semantic block boundaries, isolates
figures/tables/equations/code/evidence, and fails with a coded `slides.*`
diagnostic when an indivisible block cannot fit. Treat Reveal.js and the linked
manuscript HTML as the accessibility-enhanced reader surfaces. Beamer output is
an untagged presentation derivative; successful rendering is not a WCAG or
PDF/UA conformance verdict.

With `slides_profile="accessible"`, the canonical `render_all()` path emits a
transactional Beamer/Reveal pair for each eligible Markdown source. Both files
consume one composed Pandoc AST; any pair-member failure removes both outputs.
Use `render_accessible_slide_pair()` for the same explicit programmatic
contract. Archive mode keeps the historical Beamer-required behavior.

## Manuscript Discovery

```python
from infrastructure.rendering import discover_manuscript_files, verify_figures_exist

# Find all manuscript markdown (and .tex) files in canonical order
files = discover_manuscript_files(manuscript_dir)

# Verify expected figures exist (returns dict with figures_dir_exists,
# found_figures, missing_figures, total_expected)
status = verify_figures_exist(project_root, manuscript_dir)
```

## PDF Rendering (`pdf_renderer.py`)

The main PDF rendering engine using Pandoc and LaTeX. Not re-exported via `__init__.py` — use direct import:

```python
from infrastructure.rendering.pdf_renderer import PDFRenderer

renderer = PDFRenderer(config)
renderer.render(source_file)
renderer.render_markdown(source_file)
renderer.render_combined(source_files, manuscript_dir, project_name="my_project")
```

**CLI:**

```bash
uv run python -m infrastructure.rendering.cli pdf manuscript.tex
# Subcommands: pdf | all | slides | web — each takes a positional source file (TeX or Markdown)
uv run python -m infrastructure.rendering.cli all manuscript.tex
uv run python -m infrastructure.rendering.render_all_cli
```

## Slides Rendering (`slides_renderer.py`)

Direct import required (not in `__init__.py`):

```python
from infrastructure.rendering.slides_renderer import SlidesRenderer

renderer = SlidesRenderer(config)
renderer.render(source_file, output_format="beamer")    # PDF slides
renderer.render(source_file, output_format="revealjs")  # HTML slides
```

## Web Rendering (`web_renderer.py`)

Direct import required (not in `__init__.py`):

```python
from infrastructure.rendering.web_renderer import WebRenderer

renderer = WebRenderer(config)
renderer.render(source_file)
renderer.render_combined(source_files, manuscript_dir, project_name="my_project")
```

## LaTeX Utilities (`latex_utils.py`)

```python
from infrastructure.rendering.latex_utils import compile_latex
# Core LaTeX compilation function used by PDF and slides renderers
```

## LaTeX Package Validation (`latex_package_validator.py`)

Module-level CLI entry point — run as a module to validate the host LaTeX install:

```bash
uv run python -m infrastructure.rendering.latex_package_validator
```

**Troubleshooting:**

```bash
# Install missing LaTeX packages
sudo tlmgr install multirow cleveref doi newunicodechar
```

## DOCX / EPUB Rendering (`docx_renderer.py`, `epub_renderer.py`)

Re-exported at package level — render Microsoft Word and e-reader outputs from a combined Markdown file (both via pandoc):

```python
from pathlib import Path
from infrastructure.rendering import render_docx, render_epub

docx_result = render_docx(Path("combined.md"), Path("output.docx"), bibliography=None)
epub_result = render_epub(Path("combined.md"), Path("output.epub"), cover_image=None)
```

Signatures:

```python
render_docx(combined_md: Path, output_path: Path, *, bibliography: Path | None = None,
            reference_doc: Path | None = None, pandoc_path: str = "pandoc",
            extra_args: list[str] | None = None) -> DocxRenderResult
render_epub(combined_md: Path, output_path: Path, *, bibliography: Path | None = None,
            cover_image: Path | None = None, cover_alt: str | None = None,
            title: str | None = None, author: str | None = None, language: str = "en",
            pandoc_path: str = "pandoc",
            extra_args: list[str] | None = None) -> EpubRenderResult
```

EPUB rendering supplies Pandoc with a stable placeholder, preflights archive
bounds before payload reads, then derives UUIDv5 from canonical package member
names and uncompressed bytes with the OPF/NCX identifier fields normalized out.
Effective bibliography, body-media, filter, metadata, and tool changes are thus
bound when they change package content; identifier overrides are rejected. A
valid caller `SOURCE_DATE_EPOCH` controls packaged `dcterms:modified` and hence
participates in identity. Missing or invalid values use the fixed ZIP-safe epoch
`1980-01-01T00:00:00Z`; ambient Git and wall-clock state are not consulted. A
fresh temporary Pandoc target prevents stale-output acceptance, and atomic ZIP
normalization retains the required first/uncompressed `mimetype` member, order,
compression, comments, and permissions while fixing member timestamps.

## docxplus Export (`docxplus_export.py`, `docxplus_stage.py`)

Optional export: produces a conforming `.docx` and `.docxplus` document carrying the project's source tree under a signed manifest. Requires the `docxplus` optional extra (`uv sync --extra docxplus`):

```python
from pathlib import Path
from infrastructure.rendering import export_project, is_docxplus_available, run_docxplus_export

# Programmatic project export
if is_docxplus_available():
    res = export_project(
        Path("projects/templates/template_code_project"),
        Path("projects/templates/template_code_project/output/docxplus"),
        project="template_code_project",
    )
```

## Supporting Files

- `convert_latex_images.lua` — Pandoc Lua filter for LaTeX image conversion
- `ide_style.css` — CSS stylesheet for IDE-style rendering

## Public API Summary (`__init__.py`)

Only these are re-exported at package level:

| Export | Type |
| --- | --- |
| `RenderManager` | Class |
| `RenderingConfig` | Class |
| `DocxRenderResult` | Class |
| `EpubRenderResult` | Class |
| `ExportResult` | Class |
| `discover_manuscript_files` | Function |
| `export_project` | Function |
| `is_docxplus_available` | Function |
| `verify_figures_exist` | Function |
| `render_docx` | Function |
| `render_epub` | Function |
| `run_docxplus_export` | Function |
| `substitute_manuscript_text` | Function |
| `write_resolved_manuscript_tree` | Function |
| `EXCLUDED_DOC_FILENAMES` | Constant |
