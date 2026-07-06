# Standalone Fork Guide

## Purpose

`template_autoscientists` isolates coordination primitives from the
AutoScientists paper in a deterministic, ablatable testbed with matched budgets.

## Copy This When

Use it when you need to measure coordination mechanisms, null effects, noise-band
confirmation, and dead-end registry behavior without claiming a full live agent
system.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_autoscientists \
  --dest projects/working/my_autoscientists \
  --new-name my_autoscientists
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_autoscientists/ projects/working/my_autoscientists/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.
- Replace `SyntheticObjective`, proposer policy, and ablation set when studying a
  new coordination problem.
- Regenerate `output/data/*.json` and `output/figures/*.png` before citing fork
  metrics.

## Validation Commands

From the copied project root:

```bash
uv run pytest tests/ -m "not requires_ollama" --cov=src --cov-fail-under=90
uv run python scripts/run_search_comparison.py
uv run python scripts/run_ablation.py
```

For the public exemplar from the template repository root:

```bash
uv run pytest projects/templates/template_autoscientists/tests/ \
  -m "not requires_ollama" \
  --cov=projects/templates/template_autoscientists/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

The deterministic core is project-local. The optional `HermesProposer` path uses
the template repo's `infrastructure.llm` client when run as an opt-in live demo;
standalone forks can replace that adapter or keep the template infrastructure.

## What Not To Claim

Do not claim coordinated teams outperform the baseline on this fixture. The
exemplar is designed to report null final-answer effects while measuring search
hygiene and noise robustness.
