# AGENTS: `scripts/` — Thin Orchestrator Scripts

Technical specification for the template project's analysis scripts.

## Script Inventory

| Script | Pattern | Input | Output |
|--------|---------|-------|--------|
| `generate_architecture_viz.py` | Stage 02 Thin Orchestrator | `src/template/introspection.py` functions | 3 PNG figures |

## Figures Generated

| Figure | Filename | Description |
|--------|----------|-------------|
| 1 | `architecture_overview.png` | Two-Layer Architecture diagram (modules + projects) |
| 2 | `pipeline_stages.png` | 8-stage pipeline waterfall |
| 3 | `module_inventory.png` | Bar chart of Python files per infrastructure module |

## Design Standards

- **Colorblind-safe palette**: IBM Design / Wong palette (`#0072B2`, `#D55E00`, `#009E73`)
- **Font floor**: 16pt minimum for accessibility
- **DPI**: 300 for publication quality
- **Thin Orchestrator**: Script imports all logic from `template.introspection`, contains only visualization wiring
