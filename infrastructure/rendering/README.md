# Rendering Module - Quick Reference

Multi-format output generation for research manuscripts.

## Features

```mermaid
graph TD
    subgraph Input["Input Sources"]
        MANUSCRIPT[Manuscript Files<br/>Markdown sections<br/>project/manuscript/*.md]
        CONFIG[Configuration<br/>config.yaml<br/>Title page & metadata]
        FIGURES[Figures<br/>Generated figures<br/>output/figures/*.png]
        BIBLIOGRAPHY[Bibliography<br/>references.bib<br/>Academic citations]
    end

    subgraph Rendering["Rendering Engine"]
        MANAGER[RenderManager<br/>Orchestrates all formats<br/>Single entry point]
        PDF[pdf_renderer.py<br/>LaTeX compilation<br/>Professional PDFs]
        SLIDES[slides_renderer.py<br/>Beamer & reveal.js<br/>Presentation slides]
        WEB[web_renderer.py<br/>HTML with MathJax<br/>Web-compatible output]
    end

    subgraph Processing["Processing Steps"]
        COMBINE[Combine Sections<br/>Single LaTeX document<br/>Cross-references]
        TITLE[Title Page<br/>Auto-generated<br/>From config.yaml]
        FIGURES_PROC[Figure Integration<br/>Path resolution<br/>Verification]
        BIB_PROC[Bibliography<br/>BibTeX processing<br/>Citation resolution]
    end

    subgraph Output["Output Formats"]
        PDF_OUT[PDF Document<br/>Professional typesetting<br/>output/pdf/*.pdf]
        SLIDES_OUT[Slides<br/>PDF & HTML formats<br/>output/slides/]
        WEB_OUT[Web HTML<br/>Interactive with MathJax<br/>output/web/*.html]
        POSTER_OUT[Posters<br/>Large format<br/>output/posters/]
    end

    MANUSCRIPT --> MANAGER
    CONFIG --> MANAGER
    FIGURES --> MANAGER
    BIBLIOGRAPHY --> MANAGER

    MANAGER --> PDF
    MANAGER --> SLIDES
    MANAGER --> WEB

    PDF --> COMBINE
    SLIDES --> COMBINE
    WEB --> COMBINE

    COMBINE --> TITLE
    COMBINE --> FIGURES_PROC
    COMBINE --> BIB_PROC

    TITLE --> PDF_OUT
    FIGURES_PROC --> PDF_OUT
    BIB_PROC --> PDF_OUT
    COMBINE --> SLIDES_OUT
    COMBINE --> WEB_OUT
    COMBINE --> POSTER_OUT

    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef rendering fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef processing fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef output fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class Input input
    class Rendering rendering
    class Processing processing
    class Output output
```

- **Consolidated Pipeline**: Single entry point for all formats.
- **Multiple Outputs**: PDF, Slides (Beamer/HTML), Web, Posters.
- **Title Page Generation**: Automatic title page from `config.yaml`.
- **Figure Integration**: Automatic figure path resolution and verification.
- **Quality Control**: Automated compilation checks and comprehensive logging.
- **Package Validation**: Pre-flight checks for LaTeX packages.

## LaTeX Package Requirements

### BasicTeX (Minimal Installation)

This rendering system supports **BasicTeX**, a minimal TeX distribution (~100 MB instead of full MacTeX's ~4 GB).

**Required packages** (some require installation):
```bash
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar
```

**Already included in BasicTeX**:
- Core packages: `amsmath`, `graphicx`, `hyperref`, `natbib`
- Table enhancement: `bm` (part of `tools`), `subcaption` (part of `caption`)

**Pre-flight validation**:
```bash
# Validate packages before rendering
python3 -m infrastructure.rendering.latex_package_validator

# Or run as part of pipeline (automatic)
python3 scripts/03_render_pdf.py
```

**Common issues**:
- **"File *.sty not found"**: Install missing package via `tlmgr`
- **No kpsewhich found**: Install BasicTeX or MacTeX
- **Permission denied**: Use `sudo` for tlmgr commands

### Full MacTeX (Complete Installation)

For a complete installation with all packages, install **MacTeX**:
```bash
brew install --cask mactex
```

MacTeX includes all packages and tools but requires ~4 GB disk space.

## Quick Start

### Render Combined PDF

```python
from infrastructure.rendering import RenderManager
from pathlib import Path

manager = RenderManager()
manager.render_combined_pdf(
    [Path("01_abstract.md"), Path("02_intro.md"), ...],
    manuscript_dir=Path("manuscript/")
)
```

### Configure Title Page

Edit `project/manuscript/config.yaml`:

```yaml
paper:
  title: "Your Research Title"
  subtitle: "Optional Subtitle"

authors:
  - name: "Dr. Your Name"
    email: "your@email.edu"
    affiliation: "Your Institution"
    corresponding: true
```

### Add Bibliography and Citations

Place bibliography in `manuscript/references.bib`:

```bibtex
@article{author2024,
  title={Article Title},
  author={Author, First},
  journal={Journal Name},
  year={2024}
}
```

Cite in markdown using LaTeX syntax:

```latex
According to recent work \cite{author2024}, we demonstrate...
```

**Note**: Bibliography is automatically processed during PDF rendering. The system runs `bibtex` after LaTeX generation to resolve all citations.

### Add Figures

Place figures in `project/output/figures/` and reference in markdown:

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/your_figure.png}
\caption{Figure caption}
\label{fig:your_figure}
\end{figure}

Reference in text: Figure \ref{fig:your_figure}
```

**Important**: The rendering system automatically ensures `\usepackage{graphicx}` is included in the LaTeX preamble. This package is required for `\includegraphics` commands. If not in your custom preamble (`manuscript/preamble.md`), it will be added automatically during compilation.

**Note**: Figure paths are automatically corrected during rendering. The system handles:
- Path normalization for various formats (`../output/figures/`, `output/figures/`, etc.)
- Unicode characters in filenames
- Missing figure warnings (compilation continues gracefully, but logs the issue)

## Common Tasks

### Render to All Formats

```bash
python3 -m infrastructure.rendering.cli all manuscript.tex
```

### Render PDF Only

```bash
python3 -m infrastructure.rendering.cli pdf manuscript.tex
```

### Generate Slides

```bash
python3 -m infrastructure.rendering.cli slides presentation.md --format beamer
python3 -m infrastructure.rendering.cli slides presentation.md --format revealjs
```

## Supported Formats

| Format | Command | Output |
|--------|---------|--------|
| PDF | `render_pdf()` | Professional PDF document |
| Beamer Slides | `render_slides(..., format="beamer")` | PDF presentation slides |
| Reveal.js | `render_slides(..., format="revealjs")` | HTML presentation slides |
| HTML | `render_web()` | Web-ready HTML with MathJax |
| Posters | `render_poster()` | Large-format PDF poster |

## Documentation

For complete documentation, see [`AGENTS.md`](AGENTS.md).

Key sections:
- Title Page Configuration
- Figure Handling and Path Resolution
- Troubleshooting
- Testing

## Troubleshooting

### Citations showing as "?" in PDF

**Cause**: Bibliography not processed or citation keys don't match.

**Solutions**:
1. Verify `references.bib` file exists in `manuscript/` directory
2. Check citation keys in markdown match `@` entries in `.bib` file
3. Ensure bibliography is formatted correctly:
   ```bibtex
   @article{smith2024,
     title={Title},
     author={Smith, Jane},
     year={2024}
   }
   ```
4. Run full build: `python3 scripts/run_all.py`

### Figures not appearing in PDF

**Cause**: Missing `graphicx` package, incorrect file paths, or missing figure files.

**Solutions**:
1. **Verify graphicx package is loaded** (the system should add it automatically):
   ```bash
   grep "usepackage{graphicx}" project/output/pdf/_combined_manuscript.tex
   ```
   If missing, ensure `manuscript/preamble.md` contains `\usepackage{graphicx}` or check build logs.

2. **Generate missing figures**:
   ```bash
   python3 scripts/02_run_analysis.py
   ```

3. **Verify figures are in correct location**:
   ```bash
   ls -la project/output/figures/ | grep -E "\.png|\.pdf|\.jpg"
   ```

4. **Check figure paths in markdown** are correct:
   ```bash
   grep -r "includegraphics" project/manuscript/ | head -5
   ```
   Should be: `\includegraphics{../output/figures/name.png}`

5. **Check filename matches exactly** (case-sensitive):
   ```bash
   ls project/output/figures/ | grep "your_figure"
   ```

6. **Check LaTeX compilation log** for graphics-specific errors:
   ```bash
   tail -150 project/output/pdf/_combined_manuscript.log | grep -i "graphic\|Error"
   ```
   Look for:
   - "File not found" (figure file doesn't exist)
   - "Undefined control sequence" (graphicx package missing)
   - "Cannot find" (file path problem)

7. **For Unicode filenames**, ensure proper encoding:
   ```bash
   file project/output/figures/your_figure.png
   ```

### LaTeX Compilation Errors

**Cause**: Missing LaTeX packages or invalid markup.

**Solutions**:
1. Check preamble in `manuscript/preamble.md` for required packages
2. Verify all LaTeX commands are valid (use `\ref{}`, not `\ref {}`)
3. Ensure all `\label{}` commands exist for referenced items
4. Run validation: `python3 -m infrastructure.validation.cli markdown project/manuscript/`

## Testing

```bash
# Run all rendering tests
pytest tests/infrastructure/rendering/ -v

# Run combined PDF tests specifically
pytest tests/infrastructure/rendering/test_pdf_renderer_combined.py -v

# Run bibliography and figure fix tests
pytest tests/infrastructure/rendering/test_pdf_renderer_fixes.py -v

# Run with coverage
pytest tests/infrastructure/rendering/ --cov=infrastructure.rendering
```

