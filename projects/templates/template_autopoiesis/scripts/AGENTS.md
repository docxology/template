# Scripts — template_autopoiesis

Thin orchestrators calling `src/` for grammar expansion, materialization, and
verification. Invoked by the standard pipeline analysis stage.

`01_generate_manuscript_assets.py` also binds the four manuscript figure specs
from `src/manuscript_figures.py` to the PNGs produced in the same run and emits
`output/figures/figure_registry.json`; missing coverage or a missing figure is
an error, not a skipped registry entry.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
