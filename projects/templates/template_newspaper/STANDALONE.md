# Standalone Fork Guide

## Purpose

`template_newspaper` is a data-driven, large-format newspaper layout exemplar
with content YAML, deterministic figure generation, and a tested ReportLab
layout engine.

## Copy This When

Use it when a fork needs print-layout machinery, page furniture, ads, weather or
market panels, and a raster-verifiable PDF edition.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_newspaper \
  --dest projects/working/my_newspaper \
  --new-name my_newspaper
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_newspaper/ projects/working/my_newspaper/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Replace `content/`, masthead settings, ad inventory, and local fixtures before
  presenting a fork as a real publication.
- Regenerate figures and the final PDF after changing content or trim size.

## Validation Commands

From the copied project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/10_generate_figures.py
uv run python scripts/20_render_newspaper.py
```

For the public exemplar from the template repository root:

```bash
uv run pytest projects/templates/template_newspaper/tests/ \
  --cov=projects/templates/template_newspaper/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

The layout engine and project tests are project-local. The script bootstrap can
use the template infrastructure logger when present, but falls back for ordinary
project execution. Monorepo rendering/copy stages remain optional polish.

## What Not To Claim

Do not claim the fictional edition is a real newspaper issue. Do not claim
layout quality after content changes until the PDF is rendered and page rasters
are inspected for overset text, missing assets, and geometry regressions.
