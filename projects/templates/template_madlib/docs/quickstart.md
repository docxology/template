# Quickstart — Template Madlib

```bash
# Run the full pipeline
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib
uv run python scripts/pipeline/stage_03_render.py --project templates/template_madlib

# Run tests
uv run pytest projects/templates/template_madlib/tests/ --cov=src --cov-fail-under=90
```
