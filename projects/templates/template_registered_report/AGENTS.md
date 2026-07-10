# template_registered_report - AGENTS.md

## Ground truth

Configuration lives in `manuscript/config.yaml`; preregistration fixtures live in `data/`; reusable plan-freezing and deviation logic lives in `src/registered_report/`.

## Commands

```bash
uv run pytest projects/templates/template_registered_report/tests --cov=projects/templates/template_registered_report/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_registered_report --project-only
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_registered_report
```

## Contracts and boundaries

Do not let post-run result prose rewrite preregistered intent. Keep confirmatory claims, deviations, sensitivity checks, ethics/stage metadata, and exploratory claims separated in source, tests, review packets, and manuscript.
