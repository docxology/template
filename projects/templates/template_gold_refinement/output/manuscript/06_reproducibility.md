# Reproducibility: Seeded Regeneration {#sec:reproducibility}

## Deterministic regeneration

The refinery pipeline is fully deterministic. Given the same `manuscript/config.yaml` and `src/` code, every run produces identical output.

- **Seed:** 431
- **Config hash:** ef9773080d4a8bec
- **Generation timestamp:** 2026-06-26T13:57:48Z
- **Python version:** 3.12.13

## Artifact inventory

| Category | Count |
|----------|-------|
| Figures | 6 |
| Data files | 2 |
| Reports | 9 |
| **Total** | 17 |

## Regeneration commands

```bash
# Run the refinery analysis
uv run python projects/templates/template_gold_refinement/scripts/refinement_analysis.py

# Generate manuscript variables
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py

# Full pipeline (from repo root)
./run.sh --project templates/template_gold_refinement --pipeline --core-only
```

## Config ownership

All vocabulary, slots, and section conditions are declared in `manuscript/config.yaml` under `gold_refinement:`. The config is the source of truth; generated prose is disposable.
