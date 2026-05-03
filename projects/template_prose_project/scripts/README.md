# `template_prose_project/scripts/`

Three thin orchestrators (alphabetical execution order under stage 02).

## Quick reference

```bash
# Full review
uv run python projects/template_prose_project/scripts/run_prose_pipeline.py

# Strict mode (exit non-zero on check failure)
uv run python projects/template_prose_project/scripts/run_prose_pipeline.py --strict

# Generate figures (requires manuscript_report.json from previous step)
uv run python projects/template_prose_project/scripts/y_generate_prose_figures.py

# Hydrate manuscript variables (requires manuscript_report.json)
uv run python projects/template_prose_project/scripts/z_generate_manuscript_variables.py
```

## Execution order

| Order | Script | Inputs | Outputs |
|---|---|---|---|
| 1 | `run_prose_pipeline.py` | `manuscript/` + `manuscript/config.yaml` | `output/{manuscript_report,checks,run_summary}.json`, `output/review_report.md` |
| 2 | `y_generate_prose_figures.py` | `output/manuscript_report.json` | `output/figures/{section_word_counts,readability_metrics,citation_density}.png` |
| 3 | `z_generate_manuscript_variables.py` | `output/manuscript_report.json` + config | `output/data/manuscript_variables.json` |

The naming convention (`run_*`, `y_*`, `z_*`) ensures the infrastructure
pipeline runner executes them in the right order without any extra
configuration.

See [AGENTS.md](AGENTS.md) for the thin-orchestrator rules and
checklist for adding new scripts.
