# Quickstart

```bash
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_storybook
open projects/templates/template_storybook/output/pdf/the-shape-between.pdf
```

Run tests:

```bash
uv run pytest projects/templates/template_storybook/tests/ \
  --cov=projects/templates/template_storybook/src --cov-fail-under=90
```
