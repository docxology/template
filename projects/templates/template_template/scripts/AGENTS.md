# AGENTS: `scripts/` — Thin Orchestrator Scripts

Technical specification for the template project's analysis scripts.

## Script Inventory

| Script | Pattern | Input | Output |
|--------|---------|-------|--------|
| `generate_manuscript_metrics.py` | Stage 02 Thin Orchestrator | `src/template_template/metrics/metrics.py`, `src/template_template/metrics/inject_metrics.py` | `output/data/metrics.json`, rendered `output/manuscript/*` |
| `generate_architecture_viz.py` | Stage 02 Thin Orchestrator | `src/template_template/figures/architecture_viz.py` | 4 PNG figures in `output/figures/` |

## Design Contract

- Scripts are orchestration only: path bootstrap, logging, and module entrypoint invocation.
- Data/model/plot logic lives in `src/template_template/`.
- All reusable script behavior must be covered by tests in `projects/templates/template_template/tests/`.

## `generate_architecture_viz.py` Outputs

| Figure | Filename | Description |
|--------|----------|-------------|
| 1 | `architecture_overview.png` | Two-Layer Architecture diagram with module file counts and four-layer doc badges |
| 2 | `pipeline_stages.png` | YAML-declared pipeline pipeline flow with stage descriptions |
| 3 | `module_inventory.png` | Bar chart of Python files per infrastructure module with [ARSP] doc badges |
| 4 | `comparative_feature_matrix.png` | 14×10 tool capability heatmap with ✓/◐/— symbols and group dividers |

## `generate_manuscript_metrics.py` Outputs

| Output | Path | Description |
|--------|------|-------------|
| Metrics JSON | `output/data/metrics.json` | Live repo counts and derived manuscript variables |
| Rendered chapters | `output/manuscript/*.md` | Variable-injected chapter files used by render stage |
| Ancillary copy | `output/manuscript/references.bib`, `config.yaml`, `preamble.md` | Rendering dependencies copied verbatim |


The platform SDK pinned in this project's package metadata and lock is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
