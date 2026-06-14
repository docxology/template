# Standalone Fork Guide

## Purpose

`template_prose_project` is the manuscript-focused prose-review exemplar:
readability checks, bibliography diagnostics, report generation, figures, and
manuscript-variable injection.

## Copy This When

Use it when the main research object is a prose corpus or review manuscript and
the fork should preserve auditable editorial checks.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_prose_project \
  --dest projects/working/my_prose_project \
  --new-name my_prose_project
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_prose_project/ projects/working/my_prose_project/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`.
- Replace manuscript chapters, bibliography, review thresholds, and any
  generated-report claims.
- Regenerate prose reports, figures, and manuscript variables after editing the
  corpus.

## Validation Commands

Run from the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_prose_project/tests/ \
  --cov=projects/working/my_prose_project/src --cov-fail-under=90
uv run python projects/working/my_prose_project/scripts/run_prose_pipeline.py
uv run python projects/working/my_prose_project/scripts/z_generate_manuscript_variables.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_prose_project/tests/ \
  --cov=projects/templates/template_prose_project/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

This exemplar intentionally uses shared `infrastructure.prose` and manuscript
injection helpers. It is forkable as a project in a full template checkout. A
copy outside that checkout must vendor or replace those prose-analysis adapters.

## What Not To Claim

Do not claim source completeness, readability outcomes, or bibliography health
from a renamed fork until the fork has regenerated its prose report and
manuscript variables against its own corpus.
