# Standalone Fork Guide

## Purpose

`template_sia` is the self-improvement-agent evaluation harness exemplar: a
fixture-first loop, run artifacts, generation records, reports, and explicit
separation between fixture replay and live execution.

## Copy This When

Use it when a fork needs an auditable SIA loop scaffold with local fixture
evidence and conservative live-claim boundaries.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_sia \
  --dest projects/working/my_sia \
  --new-name my_sia
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_sia/ projects/working/my_sia/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Replace fixtures, reference-agent behavior, evaluation runner assumptions, and
  live-execution settings before claiming a new task result.
- Regenerate run summaries, reports, figures, and manuscript variables.

## Validation Commands

Run from the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_sia/tests/ \
  --cov=projects/working/my_sia/src --cov-fail-under=90
uv run python projects/working/my_sia/scripts/run_sia_loop.py
uv run python projects/working/my_sia/scripts/z_generate_manuscript_variables.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_sia/tests/ \
  --cov=projects/templates/template_sia/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

The fixture-facing project modules are local, but the loop implementation and
some tests intentionally call `infrastructure.sia` and shared rendering helpers.
Treat the exemplar as forkable inside a full template checkout unless those
adapters are vendored or replaced.

## What Not To Claim

Do not claim live self-improvement performance from fixture replay. Do not claim
new task accuracy until the fork has generated fresh run artifacts and the live
or fixture boundary is explicit.
