# Quickstart — AutoScientists

```bash
# Run the full coordinated search (deterministic)
uv run python projects/templates/template_autoscientists/scripts/run_search.py

# Run ablation study (all mechanisms toggled one by one)
uv run python projects/templates/template_autoscientists/scripts/run_ablation.py

# Run tests
uv run pytest projects/templates/template_autoscientists/tests/ --cov=src --cov-fail-under=90
```

Outputs land in `output/figures/` (ablation metric/efficiency plots) and
`output/data/` (search results JSON).
