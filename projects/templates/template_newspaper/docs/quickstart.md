# Quickstart

## Prerequisites

For a standalone checkout, follow the genuine SDK/dev setup in
[`README.md`](../README.md#quick-start), then activate that project's environment.
It provides `reportlab`, `Pillow`, `matplotlib`, and PyYAML. In the monorepo,
enter `projects/templates/template_newspaper/` first and select its prepared
environment. No external PDF compiler is needed for the newspaper itself;
`pdftoppm` is a separate visual-review prerequisite.

## Render the paper

Run from the project directory (already the repository root in a standalone clone):

```bash
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
# From the monorepo root only; this script is not shipped at a standalone root
./run.sh --project templates/template_newspaper --pipeline
```

Stage 02 runs the `scripts/` (figures + newspaper render); Stage 03 renders the
descriptive `manuscript/`.

## Tests & checks

```bash
python -m pytest                  # full suite
python -m pytest --cov=newspaper  # ~99% branch coverage (gate: 90%)
mypy src/newspaper                # clean
ruff check src scripts tests      # clean
```

Ruff and mypy require the monorepo toolchain or separate explicit preparation;
they are not declared by this project's `dev` extra. Standalone source tests
retain the same 90% floor; do not infer visual acceptance from their exit status.
