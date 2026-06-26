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

The reproducibility spine uses {{REPRO_EVIDENCE_TERM_1}} and {{REPRO_EVIDENCE_TERM_2}} as generated artifacts rather than reader trust signals. Variable generation records `{{CONFIG_HASH}}`; analysis writes refinery, token, claim-support, dashboard, and figure artifacts; validation may add the shared evidence registry used by template scientific-integrity checks.

The implementation circuit gives a reproducibility checklist for future forks. A reader should be able to start at any rendered figure or claim, follow it to a generated variable or report, follow that artifact to `src/` or `manuscript/config.yaml`, and rerun the same stage command. If that path is broken, the fork has produced a static illustration rather than a reproducible refinement pipeline.

The same rule applies to visual polish. The figure registry is source-owned, every registered PNG now has a companion SVG, and `{{FIGURE_QUALITY_REPORT_PATH}}` records {{FIGURE_QUALITY_PNG_COUNT}} PNG files, {{FIGURE_QUALITY_SVG_COUNT}} SVG files, and {{FIGURE_QUALITY_PASSING_COUNT}} passing visual-quality checks for the current variable pass. A fork should treat [@tbl:figure_quality] as the figure-layer analogue of the claim-support registry: it proves that the visuals are regenerated, present in both raster and vector forms, nonblank, and aligned with the registry before prose promotes them.

## Evidence-registry separation

This exemplar now separates two evidence surfaces. `{{CLAIM_SUPPORT_REGISTRY_PATH}}` is the project-local contribution-claim assay consumed by the dashboard and claim-support figure. `output/reports/evidence_registry.json` is reserved for the shared template evidence validator, which registers numbers, citations, equations, sections, figures, tables, generated data, and claim-ledger facts.

The evidence-tier ladder in [@fig:evidence_tier_ladder] is the reproducibility counterpart to that separation. It does not merely count files. It shows which tier owns each support surface, so a future fork can see whether a conclusion rests on config declarations, generated metrics, claim-ledger facts, bibliography records, or rendered artifacts. That distinction matters because only some tiers can support domain truth; others support reproducibility, formatting, or local consistency.
