# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project that analyzes and documents the Docxology Template repository.

**Location:** [`projects/templates/template_template/`](.) — public canonical exemplar (`infrastructure.project.public_scope`).

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Purpose

Programmatic introspection and documentation of the template repository's own architecture, serving as both a live demonstration of pipeline capabilities and a comprehensive technical reference.

## Architecture

```text
template_template/
├── src/template_template/        # Core modules
│   ├── introspection.py          # YAML + filesystem repository analysis
│   ├── metrics.py                # Manuscript metrics + token dict
│   ├── inject_metrics.py         # ${variable} substitution
│   ├── architecture_viz.py       # Figure orchestrator (calls figure_* modules)
│   ├── figure_architecture_overview.py  # Architecture overview figure
│   ├── figure_pipeline_stages.py        # Pipeline stages figure
│   ├── figure_module_inventory.py       # Module inventory figure
│   ├── figure_comparative_matrix.py     # Comparative feature matrix figure
│   ├── viz_palette.py            # Shared palette + drawing helpers
│   └── paths.py                  # Repository root discovery
├── scripts/                      # Thin orchestrators (metrics, figures)
├── tests/                     # 90%+ coverage on src/
├── manuscript/                # Chapters + config + references
├── docs/                      # Project-level technical docs
└── output/                    # Generated figures, metrics, manuscript, PDF
```

## Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md)
- Concept DOI: `manuscript/config.yaml` → `publication.doi` (PDF cover); `version_doi` / `version_record` for latest Zenodo deposit
- Standalone repo: [template_template GitHub repository](https://github.com/docxology/template_template)

## Key Subsystems

### Introspection (`src/template_template/introspection.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules` | `list[ModuleInfo]` | Scan `infrastructure/` subpackages |
| `discover_projects` | `list[ProjectAnalysis]` | Public exemplar roster only |
| `load_pipeline_stages_from_yaml` | `list[PipelineStage]` | Parse `pipeline.yaml` |
| `build_infrastructure_report` | `InfrastructureReport` | Full aggregated report |

### Metrics (`src/template_template/metrics.py`)

| Function | Description |
|----------|-------------|
| `build_manuscript_metrics_dict` | `${variable}` values from live repo |
| `save_metrics_json` | Write `output/data/metrics.json` |

### Injection (`src/template_template/inject_metrics.py`)

| Function | Description |
|----------|-------------|
| `render_all_chapters` | Write `output/manuscript/` with substituted tokens |

### Visualization (`src/template_template/architecture_viz.py`)

`generate_all_architecture_figures` orchestrates the four dedicated figure modules — `figure_architecture_overview.py`, `figure_pipeline_stages.py`, `figure_module_inventory.py`, and `figure_comparative_matrix.py` (sharing `viz_palette.py` helpers) — to write architecture overview, pipeline stages, module inventory, and comparative feature matrix figures under `output/figures/`.

## Verification

From the template repo root:

```bash
uv run pytest projects/templates/template_template/tests/ \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90 -v
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py
uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
```

## Patterns

- **Thin orchestrator:** scripts delegate to `src/template_template/`
- **Zero-mock testing:** real filesystem, real YAML, real imports
- **Measured prose:** inject counts via `${...}`; link rotating facts via `docs/_generated/active_projects.md`

## See also

- [`README.md`](README.md)
- [`docs/AGENTS.md`](docs/AGENTS.md)
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md)
- [`src/template_template/AGENTS.md`](src/template_template/AGENTS.md)
