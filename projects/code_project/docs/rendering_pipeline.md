# Rendering Pipeline: Manuscript to PDF

The `manuscript/` directory contains the narrative components of the research. It is compiled into a publication-ready PDF automatically by the template's rendering infrastructure.

## The Self-Referential Flow

1. **`references.bib`**: Parsed by `infrastructure.rendering.pdf_renderer.py`.
2. **`config.yaml`**: Contains metadata (title, authors) ingested by the renderer.
3. **`preamble.md`**: Contains LaTeX injections parsed by `infrastructure.rendering.latex_utils.py`.

The manuscript explicitly cites its own code files (`src/optimizer.py`, `tests/test_optimizer.py`) to demonstrate the "Show, Not Tell" principle. When `scripts/optimization_analysis.py` runs, it generates plots directly into `output/figures/`, which the renderer organically weaves into `03_results.md`.
