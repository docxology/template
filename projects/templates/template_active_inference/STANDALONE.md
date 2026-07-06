# Standalone Fork Guide

## Purpose

`template_active_inference` is the multi-track active-inference exemplar: analytical
checks, pymdp rollout artifacts, sheaf composition, figure registry validation,
and manuscript hydration all live in the project tree.

## Copy This When

Use it when a fork needs several independent research tracks to compose into one
evidence-backed manuscript, or when you want a portable sheaf-style manuscript
registry with local validation.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_active_inference \
  --dest projects/working/my_active_inference \
  --new-name my_active_inference
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_active_inference/ projects/working/my_active_inference/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json` for the new research object.
- Replace or regenerate `pymdp.yaml`, `figures.yaml`, `tracks.yaml`, and the
  sheaf manifests when changing the domain.
- Keep generated files under `output/` out of the fork baseline; regenerate them
  after the copy.

## Validation Commands

From the copied project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/validate_outputs.py
```

Template-root only, the public exemplar gate remains:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_active_inference
```

## Intentional Non-Standalone Dependencies

The project ships a standalone renderer and does not need the monorepo
`infrastructure/` layer for its project-local tests, scripts, or PDF renderer.
The monorepo pipeline can still render it with additional publication bookends,
but that is the polished template-repo path, not the minimum standalone path.

## What Not To Claim

Do not claim a copied fork proves new active-inference results until the fork has
regenerated its analytical, rollout, sheaf, and figure-registry artifacts. Do not
claim the generic sheaf engine validates a new domain without updating the local
manifests and rerunning the strict checks above.
