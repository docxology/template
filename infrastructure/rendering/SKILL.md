---
name: infrastructure-rendering
description: Skill for the rendering infrastructure module providing multi-format output generation including PDF manuscripts, HTML web pages, Beamer/Reveal.js slides, and posters. Use when rendering research outputs, converting markdown to PDF, generating slides, or configuring LaTeX rendering.
---

# Rendering Module

Multi-format output generation for research manuscripts. Converts markdown source into professional PDFs, HTML, slides, and posters.

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
renderer.render_all(source_file)        # md → slides + web; tex → PDF

# Render combined manuscript from multiple ordered source files
renderer.render_combined_pdf(source_files, manuscript_dir, project_name="my_project")
```

## Rendering Configuration (`config.py`)

```python
from infrastructure.rendering import RenderingConfig

config = RenderingConfig()
# Configure PDF, HTML, slides options
```

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
python3 -m infrastructure.rendering.cli render --project {name}
python3 -m infrastructure.rendering.render_all_cli
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

## Poster Rendering (`poster_renderer.py`)

```python
from infrastructure.rendering.poster_renderer import render_poster

render_poster(source_file, config)
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

## Supporting Files

- `convert_latex_images.lua` — Pandoc Lua filter for LaTeX image conversion
- `ide_style.css` — CSS stylesheet for IDE-style rendering

## Public API Summary (`__init__.py`)

Only these are re-exported at package level:

| Export | Type |
| --- | --- |
| `RenderManager` | Class |
| `RenderingConfig` | Class |
| `discover_manuscript_files` | Function |
| `verify_figures_exist` | Function |
