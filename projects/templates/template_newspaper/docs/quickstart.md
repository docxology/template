# Quickstart

## Prerequisites

The workspace `.venv` (managed by `uv` at the repo root) already provides
`reportlab`, `Pillow`, `matplotlib` and `pyyaml`. No system tools are required
to produce the newspaper PDF.

## Render the paper

```bash
cd projects/templates/template_newspaper
python scripts/10_generate_figures.py     # halftone scenes + charts → output/figures/
python scripts/20_render_newspaper.py      # 12-page PDF → output/pdf/the-triplicate.pdf
open output/pdf/the-triplicate.pdf
```

Or in one call, programmatically:

```python
from pathlib import Path
from newspaper.engine import build_and_render
r = build_and_render(Path("."))           # run from the project dir
print(r.page_count, r.all_pages_fit)      # 12 True
```

## Inspect it like the engine's authors do

```bash
pdfinfo output/pdf/the-triplicate.pdf | grep -E 'Pages|Page size'
pdftoppm -png -r 100 output/pdf/the-triplicate.pdf /tmp/triplicate
open /tmp/triplicate-01.png
```

## Run via the repository orchestrator

```bash
# from the repo root
./run.sh --project templates/template_newspaper --pipeline
```

Stage 02 runs the `scripts/` (figures + newspaper render); Stage 03 renders the
descriptive `manuscript/`.

## Tests & checks

```bash
python -m pytest                  # 28 tests
python -m pytest --cov=newspaper  # ~95%
mypy src/newspaper                # clean
ruff check src scripts tests      # clean
```
