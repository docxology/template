# Scripts — template_autopoiesis

Thin orchestrators calling `src/` for grammar expansion, materialization, and
verification. Invoked by the standard pipeline analysis stage.

`01_generate_manuscript_assets.py` also binds the four manuscript figure specs
from `src/manuscript_figures.py` to the PNGs produced in the same run and emits
`output/figures/figure_registry.json`; missing coverage or a missing figure is
an error, not a skipped registry entry.

## Files on disk

The analysis-stage allowlist in `manuscript/config.yaml` currently names these
thin entry points, in execution order:

- `02_measure_test_coverage.py`
- `01_generate_manuscript_assets.py`
- `generate_cover_art.py`
- `realize_archetypes.py`
- `realize_child_full.py`
- `04_seal.py`
- `z_generate_manuscript_variables.py`

Additional command-line helpers present in this directory are:
`autopoiesis.py` and `seal_child.py`. The `__pycache__/` directory is local
runtime state and is not a source entry point.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
