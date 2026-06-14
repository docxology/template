# Standalone Fork Guide

## Purpose

`template_code_project` is the canonical code-driven research exemplar: tested
source modules, deterministic analysis scripts, generated figures, manuscript
variables, and publication-ready metadata.

## Copy This When

Use it for computational research where claims should trace to source code,
analysis outputs, figures, and project-local tests.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_code_project \
  --dest projects/working/my_code_project \
  --new-name my_code_project
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_code_project/ projects/working/my_code_project/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`.
- Replace the optimizer, experiment config, manuscript variables, and figure
  generation with the fork's research code.
- Regenerate analysis outputs before updating manuscript result claims.

## Validation Commands

From the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_code_project/tests/ \
  --cov=projects/working/my_code_project/src --cov-fail-under=90
uv run python projects/working/my_code_project/scripts/optimization_analysis.py
uv run python projects/working/my_code_project/scripts/z_generate_manuscript_variables.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

Some analysis and documentation helpers intentionally use shared template
infrastructure. The pure optimizer modules are project-local, but the full
exemplar is forkable as a project in the broader template repository paradigm,
not as an infrastructure-free package unless you also replace those adapters.

## What Not To Claim

Do not claim new optimization results from a renamed fork until
`output/data/optimization_results.csv`, figures, validation reports, and
manuscript variables have been regenerated from the forked code.
