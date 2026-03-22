# Reproducibility

## Commands

From the repository root (with `uv` managing the environment):

```bash
uv sync
uv run python scripts/01_run_tests.py --project density_bioscales
uv run python scripts/02_run_analysis.py --project density_bioscales
uv run python scripts/03_render_pdf.py --project density_bioscales
```

`02_run_analysis.py` executes every `*.py` in `projects/density_bioscales/scripts/` in sorted order, regenerating JSON, CSV, and both PNG figures. `03_render_pdf.py` combines manuscript sections (discovered in lexicographic order by stem), applies `preamble.md`, and compiles the combined PDF.

## Dependencies

Project logic uses **NumPy** and **Matplotlib** in scripts; `src/` modules use only the Python standard library for numerics. Physical constants and anchors are **fixed literals** in `constants.py`, `ideal_gas.py`, `fluid_reference.py`, and `insect_composition.py`. Changing a preset or component density propagates through tests—there are no hidden defaults in the markdown layer.

## Figures and paths

Manuscript figure paths are relative to each section file (`../output/figures/...`). After a clean clone, figures appear only after running analysis scripts; the pipeline is expected to regenerate them. For byte-identical PNGs across machines, pin Matplotlib and use the same `dpi` (200) in the scripts; font availability may still cause sub-pixel differences.

## HTML output

When web rendering is enabled in the pipeline, an HTML bundle under `projects/density_bioscales/output/web/` (and copied to `output/density_bioscales/web/` after copy stage) provides the same structure with MathJax-friendly markup for in-browser review.
