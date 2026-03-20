# AGENTS: `scripts/` — Thin Orchestrator Scripts

Technical specification for the template project's analysis scripts.

## Script Inventory

| Script | Pattern | Input | Output |
|--------|---------|-------|--------|
| `generate_manuscript_metrics.py` | Stage 02 Thin Orchestrator | `src/template/metrics.py`, `src/template/inject_metrics.py` | `output/data/metrics.json`, rendered `output/manuscript/*` |
| `generate_architecture_viz.py` | Stage 02 Thin Orchestrator | `src/template/architecture_viz.py` | 4 PNG figures in `output/figures/` |

## Design Contract

- Scripts are orchestration only: path bootstrap, logging, and module entrypoint invocation.
- Data/model/plot logic lives in `src/template/`.
- All reusable script behavior must be covered by tests in `projects/template/tests/`.

## `generate_architecture_viz.py` Outputs

| Figure | Filename | Description |
|--------|----------|-------------|
| 1 | `architecture_overview.png` | Two-Layer Architecture diagram with module file counts and four-layer doc badges |
| 2 | `pipeline_stages.png` | Eight-stage pipeline flow with stage descriptions |
| 3 | `module_inventory.png` | Bar chart of Python files per infrastructure module with [ARSP] doc badges |
| 4 | `comparative_feature_matrix.png` | 14×10 tool capability heatmap with ✓/◐/— symbols and group dividers |

## `generate_manuscript_metrics.py` Outputs

| Output | Path | Description |
|--------|------|-------------|
| Metrics JSON | `output/data/metrics.json` | ~40 live repo counts and derived manuscript variables |
| Rendered chapters | `output/manuscript/*.md` | Variable-injected chapter files used by render stage |
| Ancillary copy | `output/manuscript/references.bib`, `config.yaml`, `preamble.md` | Rendering dependencies copied verbatim |
