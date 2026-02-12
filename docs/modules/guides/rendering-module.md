# Rendering System Module

> **Multi-format output generation from single source**

**Location:** `infrastructure/rendering/core.py`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **PDF Rendering**: Professional LaTeX-based PDFs
- **Presentation Slides**: Beamer (PDF) and reveal.js (HTML) slides
- **Web Output**: Interactive HTML with MathJax
- **Scientific Posters**: Large-format poster generation
- **Format-Agnostic**: Single source, multiple outputs
- **Quality Validation**: Automated output checking

---

## Usage Examples

### Render All Formats

```python
from infrastructure.rendering import RenderManager
from pathlib import Path

manager = RenderManager()

# Render all formats from markdown
outputs = manager.render_all(Path("manuscript/main.md"))

# Outputs include:
# - PDF: output/pdf/main.pdf
# - Slides: output/slides/main_beamer.pdf, output/slides/main_revealjs.html
# - Web: output/web/main.html
# - Poster: output/posters/main_poster.pdf
```

### Render Specific Format

```python
# PDF only
pdf_path = manager.render_pdf(Path("manuscript/main.tex"))

# Beamer slides
slides_pdf = manager.render_slides(
    Path("presentation.md"),
    format="beamer"
)

# Reveal.js HTML slides
slides_html = manager.render_slides(
    Path("presentation.md"),
    format="revealjs"
)

# Web version
html_path = manager.render_web(Path("manuscript/main.md"))
```

### Combined PDF with Title Page

```python
# Render combined PDF with automatic title page generation
markdown_files = [
    Path("manuscript/01_abstract.md"),
    Path("manuscript/02_introduction.md"),
    # ... more sections
]

pdf_path = manager.render_combined_pdf(
    markdown_files,
    manuscript_dir=Path("manuscript/")
)
# Title page automatically generated from project/manuscript/config.yaml
```

---

## CLI Integration

```bash
# Render all formats
python3 -m infrastructure.rendering.cli all manuscript.tex

# Render PDF only
python3 -m infrastructure.rendering.cli pdf manuscript.tex

# Generate slides
python3 -m infrastructure.rendering.cli slides presentation.md --format beamer
python3 -m infrastructure.rendering.cli slides presentation.md --format revealjs

# Generate web version
python3 -m infrastructure.rendering.cli web manuscript.md
```

---

**Related:** [Reporting Module](reporting-module.md) | [Publishing Module](publishing-module.md)
