# scripts/ — Thin Orchestrators

## Overview

Thin orchestrators that coordinate I/O and delegate to `src/`. No business
logic here — all computation lives in `src/`.

## Scripts

| Script | Role |
|--------|------|
| `refinement_analysis.py` | Run the refinery pipeline, write `output/data/refinery_results.json` and `output/reports/token_plan.json` |
| `z_generate_manuscript_variables.py` | Generate `{{TOKEN}}` variables, write `output/data/manuscript_variables.json`, inject into `output/manuscript/` |

The `z_` prefix on the second script means it runs **after** analysis — it
consumes `output/data/refinery_results.json` and must run last before rendering.

## Commands

```bash
# Run the refinery analysis
uv run python projects/templates/template_gold_refinement/scripts/refinement_analysis.py

# Generate manuscript variables (requires analysis outputs)
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py

# Draft mode (allows N/A fallbacks when analysis is missing)
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py --allow-draft
```
