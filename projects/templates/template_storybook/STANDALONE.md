# Standalone Fork Guide

## Purpose

`template_storybook` is a deterministic picture-book exemplar with data-owned
story pages, procedural full-page art, text overlays, and PDF assembly.

## Copy This When

Use it when a fork needs an illustrated PDF book or visual story artifact where
each page is a complete scene and scripts remain thin.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_storybook \
  --dest projects/working/my_storybook \
  --new-name my_storybook
```

Fallback:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_storybook/ projects/working/my_storybook/
```

## Required Post-Fork Edits

- Replace `content/story.yaml`.
- Update `manuscript/config.yaml`, `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Re-render every page and inspect the generated PDF.

## Validation Commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/90_build_storybook_pdf.py
```

## What Not To Claim

Do not claim the bundled fictional story is a sourced case study, therapeutic
intervention, or real educational trial.
