# {{TITLE_REPRODUCIBILITY}} {#sec:reproducibility}

## Deterministic regeneration

The refinery pipeline is fully deterministic. Given the same `manuscript/config.yaml` and `src/` code, every run produces identical output.

- **Seed:** {{CONFIG_SEED}}
- **Config hash:** {{CONFIG_HASH}}
- **Generation timestamp:** {{GENERATION_TIMESTAMP}}
- **Python version:** {{PYTHON_VERSION}}

## Artifact inventory

| Category | Count |
|----------|-------|
| Figures | {{ARTIFACT_FIGURES}} |
| Data files | {{ARTIFACT_DATA_FILES}} |
| Reports | {{ARTIFACT_REPORTS}} |
| **Total** | {{ARTIFACT_TOTAL}} |

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
