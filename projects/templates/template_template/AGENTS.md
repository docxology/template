# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project that analyzes and documents the Docxology Template repository.

**Location:** [`projects/templates/template_template/`](.) — public canonical exemplar (`infrastructure.project.public_scope`).

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Purpose

Programmatic introspection and documentation of the template repository's own architecture, serving as both a live demonstration of pipeline capabilities and a comprehensive technical reference.

## Architecture

```text
template_template/
├── src/template_template/        # Domain modules (core / metrics / figures)
│   ├── core/                     # Introspection, contracts, repo-root discovery
│   ├── metrics/                  # Manuscript metrics + ${variable} injection
│   └── figures/                  # Figure orchestrator + per-figure builders + palette
├── scripts/                      # Thin orchestrators (metrics, figures)
├── tests/                     # 90%+ coverage on src/
├── manuscript/                # Chapters + config + references
├── docs/                      # Project-level technical docs
└── output/                    # Generated figures, metrics, manuscript, PDF
```

#
## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-template/SKILL.md`](.agents/skills/template-template/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

# Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
- Concept DOI: `manuscript/config.yaml` → `publication.doi` (PDF cover); `version_doi` / `version_record` for latest Zenodo deposit
- Standalone repo: [template_template GitHub repository](https://github.com/docxology/template_template)

## Key Subsystems

### Introspection (`src/template_template/core/introspection.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules` | `list[ModuleInfo]` | Scan `infrastructure/` subpackages |
| `discover_projects` | `list[ProjectAnalysis]` | Public exemplar roster only |
| `load_pipeline_stages_from_yaml` | `list[PipelineStage]` | Parse `pipeline.yaml` |
| `build_infrastructure_report` | `InfrastructureReport` | Full aggregated report |

### Metrics (`src/template_template/metrics/metrics.py`)

| Function | Description |
|----------|-------------|
| `build_manuscript_metrics_dict` | `${variable}` values from live repo |
| `save_metrics_json` | Write `output/data/metrics.json` |

### Injection (`src/template_template/metrics/inject_metrics.py`)

| Function | Description |
|----------|-------------|
| `render_all_chapters` | Write `output/manuscript/` with substituted tokens |

### Visualization (`src/template_template/figures/architecture_viz.py`)

`generate_all_architecture_figures` orchestrates the four dedicated figure builders under `figures/` — `figure_architecture_overview.py`, `figure_pipeline_stages.py`, `figure_module_inventory.py`, and `figure_comparative_matrix.py` (sharing `figures/viz_palette.py` helpers) — to write architecture overview, pipeline stages, module inventory, and comparative feature matrix figures under `output/figures/`.

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


## Standalone complete-source DATA

The selected `research-project-template==4.0.2` SDK supplies executable infrastructure. Complete Root tests, manuscripts, all public exemplars and native Git facts are separate DATA inputs. A standalone preparation harness must supply all three `TEMPLATE_PUBLIC_REFERENCE_ROOT`, `TEMPLATE_PUBLIC_REFERENCE_COMMIT` and `TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT` fields from the admitted clean candidate. The reference must contain the initialized pinned Kmyth checkout; no tool initializes or retrieves it during admission. Never add this DATA root to `sys.path` or manufacture it inside wheel site-packages.

Whole-source producers and the full own test suite admit this reference once, retain the original finite session clock, and recheck source/inventory/SDK custody before accepting results. Keep own-project outputs outside the DATA root. Existing source-checkout discovery remains available for ordinary development and genuine path-discovery controls; it grants no standalone DATA or installed-wheel acceptance. Invalid, missing or changed required DATA remains blocked by the acceptance harness, with no coverage reduction or dropped cases.

After explicit SDK/dev preparation, run `python -I -m pytest tests/ --cov=src --cov-fail-under=90` from the standalone own project. This command requires the admitted DATA environment and every declared renderer/provider needed by the selected cases. A fresh complete own-suite receipt and actual installed-wheel execution remain distinct acceptance requirements.

Public metrics enumerate only the exact canonical qualified public roster paths under projects/templates. Local lifecycle or flat aliases with a public leaf name remain available only to explicit public_only=False diagnostics; they cannot enter published counts. Canonical public directory redirects are refused.
