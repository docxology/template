# Output Conventions

## Directory structure

```
output/
├── data/
│   ├── refinery_results.json       # Refinery pipeline results
│   └── manuscript_variables.json   # {{TOKEN}} → value mapping
├── reports/
│   └── token_plan.json             # Token plan with provenance
├── figures/
│   ├── purity_progression.png      # Purity progression chart
│   ├── karat_grading.png           # Karat grading scale
│   ├── token_density.png           # Token distribution
│   └── figure_registry.json        # Figure registry
├── manuscript/                     # Hydrated manuscript (resolved tokens)
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   └── ...
├── pdf/
│   └── template_gold_refinement_combined.pdf
└── web/
    └── index.html
```

## File conventions

- **JSON files**: `indent=2`, `sort_keys=True`, `ensure_ascii=False`
- **Figures**: 300 DPI PNG, tight bounding box
- **Manuscript**: Markdown with `{{TOKEN}}` placeholders resolved
- **Registry**: `figure_registry.json` with label, path, caption per figure

## Regeneration

All output is disposable. Regenerate from source:

```bash
uv run python scripts/refinement_analysis.py
uv run python scripts/z_generate_manuscript_variables.py
```

Never hand-edit files under `output/`.
