# Template Scripts

Thin orchestrator scripts for the template meta-project. Testable logic lives in
`src/template/`; scripts only set paths and invoke module entrypoints.

## Scripts

### `generate_manuscript_metrics.py`

Builds metrics and renders injected manuscript chapters.

```bash
uv run python projects/template/scripts/generate_manuscript_metrics.py
```

Module logic:

- `src/template/metrics.py` — metrics computation, module inventory table, and JSON save
- `src/template/inject_metrics.py` — `${variable}` substitution and chapter rendering

Outputs:

- `output/data/metrics.json` — ~40 live repository variables
- `output/manuscript/*.md` — rendered chapters plus copied ancillary files (`.bib`, `.yaml`, `.md`)

### `generate_architecture_viz.py`

Generates architecture figures from live introspection data.

```bash
uv run python projects/template/scripts/generate_architecture_viz.py
```

Module logic:

- `src/template/architecture_viz.py` — all figure construction, colour palette, and comparative matrix data
- `src/template/introspection.py` — repository data used by figure generators

Outputs (`output/figures/`):

- `architecture_overview.png` — Two-Layer Architecture diagram with file counts and four-layer doc badges
- `pipeline_stages.png` — eight-stage pipeline flow with descriptions
- `module_inventory.png` — module file counts with graduated colour and [ARSP] badges
- `comparative_feature_matrix.png` — 14×10 capability heatmap with ✓/◐/— symbols
