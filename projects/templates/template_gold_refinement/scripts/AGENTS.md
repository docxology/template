# scripts/ — Thin Orchestrators

## Overview

Thin orchestrators that coordinate I/O and delegate to `src/`. No business
logic here — all computation lives in `src/`.

## Scripts

| Script | Role |
|--------|------|
| `refinement_analysis.py` | Run the refinery pipeline, write `output/data/refinery_results.json` and `output/reports/token_plan.json` |
| `z_generate_manuscript_variables.py` | Generate `{{TOKEN}}` variables, write `output/data/manuscript_variables.json`, inject into `output/manuscript/` |
| `zz_generate_cover_visualization.py` | Generate the manuscript cover image (`figures/cover_visualization.png`) from `src/cover_visualization.py` |

The `z_`/`zz_` prefixes encode run order: both scripts run **after** analysis
and consume `output/data/refinery_results.json`; `zz_generate_cover_visualization.py`
runs last, after manuscript variables are generated, so the cover reflects the
same run's data.

## Commands

```bash
# Run the refinery analysis
uv run python projects/templates/template_gold_refinement/scripts/refinement_analysis.py

# Generate manuscript variables (requires analysis outputs)
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py

# Draft mode (allows N/A fallbacks when analysis is missing)
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py --allow-draft

# Generate the cover visualization (requires analysis outputs)
uv run python projects/templates/template_gold_refinement/scripts/zz_generate_cover_visualization.py
```
