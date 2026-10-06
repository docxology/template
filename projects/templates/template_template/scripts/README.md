# Template Scripts

Thin orchestrator scripts for the template meta-project. Testable logic lives in
`src/template_template/`; scripts only set paths and invoke module entrypoints.

## Scripts

### `generate_manuscript_metrics.py`

Builds metrics and renders injected manuscript chapters.

```bash
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py
```

Module logic:

- `src/template_template/metrics/metrics.py` — metrics computation, module inventory table, and JSON save
- `src/template_template/metrics/inject_metrics.py` — `${variable}` substitution and chapter rendering

Outputs:

- `output/data/metrics.json` — live repository variables (count grows with the exemplar roster and metric surface)
- `output/manuscript/*.md` — rendered chapters plus copied ancillary files (`.bib`, `.yaml`, `.md`)

### `generate_architecture_viz.py`

Generates architecture figures from live introspection data.

```bash
uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
```

Module logic:

- `src/template_template/figures/architecture_viz.py` — all figure construction, colour palette, and comparative matrix data
- `src/template_template/core/introspection.py` — repository data used by figure generators

Outputs (`output/figures/`):

- `architecture_overview.png` — Two-Layer Architecture diagram with file counts and four-layer doc badges
- `pipeline_stages.png` — YAML-declared pipeline flow with stage descriptions
- `module_inventory.png` — module file counts with graduated colour and [ARSP] badges
- `comparative_feature_matrix.png` — 14×10 capability heatmap with ✓/◐/— symbols


The declared platform 4.0.0 SDK is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
