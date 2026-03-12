# Template Scripts

Thin orchestrator scripts for the template meta-project. All domain logic lives in `src/template/`; scripts only wire data to visualizations.

## Scripts

### `generate_architecture_viz.py`

Generates 3 publication-quality architecture figures by introspecting the live repository:

```bash
uv run python projects/template/scripts/generate_architecture_viz.py
```

**Output** → `output/figures/`:

- `architecture_overview.png` — Two-Layer diagram
- `pipeline_stages.png` — 8-stage waterfall
- `module_inventory.png` — Module file counts
