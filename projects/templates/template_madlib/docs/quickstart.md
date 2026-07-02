# Quickstart — Template Madlib

```bash
# Run the full pipeline
uv run python scripts/02_run_analysis.py --project templates/template_madlib
uv run python scripts/03_render_pdf.py --project templates/template_madlib

# Run tests
uv run pytest projects/templates/template_madlib/tests/ --cov=src --cov-fail-under=90
```
