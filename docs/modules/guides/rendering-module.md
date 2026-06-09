# Rendering System Module

> **Multi-format output generation from single source**

**Location:** `infrastructure/rendering/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **PDF Rendering**: Professional LaTeX-based PDFs
- **Presentation Slides**: Beamer (PDF) and reveal.js (HTML) slides
- **Web Output**: Interactive HTML with MathJax
- **DOCX Output**: Microsoft Word document via pandoc (opt-in)
- **EPUB Output**: e-reader bundle via pandoc (opt-in)
- **Scientific Posters**: Large-format poster generation
- **Format-Agnostic**: Single source, multiple outputs — per-format on/off toggle via [`render.formats`](../../usage/output-formats.md)
- **Quality Validation**: Automated output checking

## DOCX & EPUB Rendering

Both formats are emitted by thin pandoc-backed renderer modules; the
pandoc engine that already drives HTML and combined-PDF preprocessing.

| File | Public API |
| --- | --- |
| `infrastructure/rendering/docx_renderer.py` | `render_docx(combined_md, output_path, *, bibliography=None, reference_doc=None, pandoc_path="pandoc", extra_args=None) -> DocxRenderResult` |
| `infrastructure/rendering/epub_renderer.py` | `render_epub(combined_md, output_path, *, bibliography=None, cover_image=None, pandoc_path="pandoc", extra_args=None) -> EpubRenderResult` |

Both functions return a frozen dataclass (`DocxRenderResult` /
`EpubRenderResult`) carrying `output_path`, `size_bytes`, and
`duration_seconds`. Errors raise `infrastructure.core.exceptions.RenderingError`
on non-zero pandoc exit; `FileNotFoundError` when the combined-markdown
input is absent.

DOCX/EPUB are **opt-in** by default. Enable in the project's
`manuscript/config.yaml`:

```yaml
render:
  formats:
    pdf: true
    html: true
    slides: true
    docx: true
    epub: false
```

Both renderers reuse the preprocessed `_combined_manuscript.md` produced
by the PDF stage. If PDF rendering is disabled, DOCX and EPUB cascade-skip
with a `[skip] DOCX rendering: no combined markdown found` log line.

See also: [`../../usage/output-formats.md`](../../usage/output-formats.md),
[`../../architecture/adrs/003-multi-format-rendering-and-toggles.md`](../../architecture/adrs/003-multi-format-rendering-and-toggles.md).

## Configuration

`RenderingConfig` (`infrastructure/rendering/config.py`) exposes five
on/off booleans plus output-path overrides:

| Field | Default | Effect |
| --- | --- | --- |
| `enable_pdf` | `True` | gate combined-PDF stage |
| `enable_html` | `True` | gate combined-HTML stage |
| `enable_slides` | `True` | gate per-section Beamer stage |
| `enable_docx` | `False` | gate combined-DOCX stage |
| `enable_epub` | `False` | gate combined-EPUB stage |
| `docx_dir` | `output/docx` | output directory for DOCX |
| `epub_dir` | `output/epub` | output directory for EPUB |

Factory: `RenderingConfig.from_project_config(yaml_mapping, *, env=None)`
reads the `render.formats` block from a parsed `manuscript/config.yaml`
mapping; env vars (`ENABLE_PDF`, `ENABLE_HTML`, `ENABLE_SLIDES`,
`ENABLE_DOCX`, `ENABLE_EPUB`) override yaml.

---

## Usage Examples

### Render All Formats

```python
from infrastructure.rendering import RenderManager
from pathlib import Path

manager = RenderManager()

# Render all formats from markdown
outputs = manager.render_all(Path("manuscript/main.md"))

# Outputs are written under the project output tree, e.g.:
# - PDF: projects/{name}/output/pdf/
# - Slides: projects/{name}/output/slides/
# - Web: projects/{name}/output/web/
# Final copy stage may mirror to output/{name}/ (see RUN_GUIDE)
```

### Render Specific Format

```python
# PDF only
pdf_path = manager.render_pdf(Path("manuscript/main.tex"))

# Beamer slides
slides_pdf = manager.render_slides(
    Path("presentation.md"),
    output_format="beamer"
)

# Reveal.js HTML slides
slides_html = manager.render_slides(
    Path("presentation.md"),
    output_format="revealjs"
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
# Title page automatically generated from projects/{name}/manuscript/config.yaml
```

---

## CLI Integration

```bash
# Render all formats
uv run python -m infrastructure.rendering.cli all manuscript.tex

# Render PDF only
uv run python -m infrastructure.rendering.cli pdf manuscript.tex

# Generate slides
uv run python -m infrastructure.rendering.cli slides presentation.md --format beamer
uv run python -m infrastructure.rendering.cli slides presentation.md --format revealjs

# Generate web version
uv run python -m infrastructure.rendering.cli web manuscript.md
```

---

## Template Variable Injection

The renderer natively supports dynamic parameter injection for your manuscripts using Jinja-like placeholders (`{{variable_name}}`).

### How It Works

If a `manuscript_vars.yaml` file is placed in your project's `manuscript/` directory, the engine parses it mapping any primitive keys into strings dynamically injected into markdown headers, lists, code, and body text.

For example, given `projects/{name}/manuscript/manuscript_vars.yaml`:

```yaml
areas:
  ActiveInference: 11
  FEP: 14
maturity:
  real: 8
  partial: 35
```

The rendering hooks resolve any nested structures using flatten techniques:

- `{{maturity.real}}` -> `8`
- `{{areas.FEP}}` -> `14`

### Synthetic Pipeline Agnosticism

For structural project topologies resembling `fep_lean`—but completely backward-compatible with generalized architectures (`template_code_project`, `template`)—the module automatically evaluates synthetic parameters to simplify front-end syntax:

- Synthesizes `total_topics` and `total_areas` aggregations based on count metrics if relevant keys exist.
- Emits derived representations like dynamically scaled `maturity_icon` semantics (`✅`, `⚠️`, `○`) and string metric transformations like `lean_chars` based on codebase properties.
- **Robust Schema Binding:** Deep type inspections guarantee that the generalized rendering layer skips variable derivations exclusively relying on arrays or absent dictionary structures on minimalist or newer templates running within the `projects/` subdirectories.

---

**Related:** [Reporting Module](reporting-module.md) | [Publishing Module](publishing-module.md)
