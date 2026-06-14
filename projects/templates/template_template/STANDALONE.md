# Standalone Fork Guide

## Purpose

`template_template` is the meta-research exemplar: it studies a template-like
checkout by introspecting repository structure, public project scope, pipeline
metadata, metrics, figures, and manuscript tokens.

## Copy This When

Use it when the fork's subject is the template repository itself or another
checkout that deliberately preserves the same architecture and infrastructure
interfaces.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_template \
  --dest projects/working/my_template_meta_project \
  --new-name my_template_meta_project
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_template/ projects/working/my_template_meta_project/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Replace figure labels, metrics, and manuscript claims if the inspected
  checkout is not the canonical `template/` repository.
- Keep metric-token prose synchronized with regenerated `output/data/metrics.json`.

## Validation Commands

Run from a full template-like checkout after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_template_meta_project/tests/ \
  --cov=projects/working/my_template_meta_project/src --cov-fail-under=90
uv run python projects/working/my_template_meta_project/scripts/generate_architecture_viz.py
uv run python projects/working/my_template_meta_project/scripts/generate_manuscript_metrics.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_template/tests/ \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

This exemplar is not a generic standalone paper. It intentionally imports
template infrastructure and inspects a template-like repository root. A copy is
standalone only when it lives in, or is pointed at, a checkout with equivalent
`infrastructure/`, `projects/`, and pipeline contracts.

## What Not To Claim

Do not claim the copied project describes an arbitrary repository. Its claims
are true only for the checkout it introspects and only after metrics and figures
are regenerated.
