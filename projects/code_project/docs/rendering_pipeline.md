# Rendering Pipeline: Manuscript to PDF

The `manuscript/` directory contains the narrative components of the research. It is compiled into a publication-ready PDF automatically by the template's rendering infrastructure.

## The Self-Referential Flow

1. **`z_generate_manuscript_variables.py`**: Executes first after analysis is complete. It pulls metrics from `output/data/` and injects them into the manuscript markdown files using `{{VARIABLE}}` tags.
2. **`references.bib`**: Parsed by `infrastructure.rendering.pdf_renderer.py` for BibTeX citation management.
3. **`config.yaml`**: Contains metadata (title, authors) ingested by the renderer to automate Title Page creation.
4. **`preamble.md`**: Contains LaTeX injections parsed by `infrastructure.rendering.latex_utils.py`.

The manuscript explicitly cites its own code files (`src/optimizer.py`, `tests/test_optimizer.py`) to demonstrate the "Show, Not Tell" principle. When `scripts/optimization_analysis.py` runs, it generates plots directly into `output/figures/`, which the renderer organically weaves into `03_results.md` after variable substitution.
