# Standalone Fork Guide

## Purpose

`template_autoresearch_project` demonstrates a bounded, offline AutoResearch
loop with file-backed evidence registries, review gates, artifact manifests,
and manuscript variables.

## Copy This When

Use it when a fork should stay inside the template repository paradigm and needs
a reproducible AutoResearch loop rather than a free-form agent demo.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_autoresearch_project \
  --dest projects/working/my_autoresearch_project \
  --new-name my_autoresearch_project
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_autoresearch_project/ projects/working/my_autoresearch_project/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Replace the research object, budget policy, evidence ledger, and fixture data
  with domain-specific inputs before making scientific claims.
- Keep generated `output/` artifacts out of the seed copy and regenerate them
  with the fork's own scripts.

## Validation Commands

Run from the template repository root after copying into `projects/working/` or
another full template checkout:

```bash
uv run pytest projects/working/my_autoresearch_project/tests/ \
  --cov=projects/working/my_autoresearch_project/src --cov-fail-under=90
uv run python projects/working/my_autoresearch_project/scripts/check_source_ledger.py
uv run python projects/working/my_autoresearch_project/scripts/run_autoresearch_loop.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_autoresearch_project/tests/ \
  --cov=projects/templates/template_autoresearch_project/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

This exemplar intentionally imports reusable Layer-1 infrastructure such as
`infrastructure.autoresearch`, artifact hashing, and evidence-registry helpers.
It is forkable as a project in a template-style checkout. It is not advertised as
a self-contained package that runs after copying only this directory outside the
template infrastructure.

## What Not To Claim

Do not claim live autonomous discovery or benchmark superiority from the default
fixture. The fork demonstrates a bounded, auditable loop; new performance claims
require new evidence ledgers and regenerated artifacts.
