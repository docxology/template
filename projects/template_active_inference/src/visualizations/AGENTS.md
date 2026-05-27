# Visualization Notes

Use the headless Agg backend and pin `savefig` metadata so figures are byte-reproducible across machines and matplotlib versions. Every figure is derived from a substantive generated data artifact, not hard-coded values.

## Figure registry

| Module | Role |
| --- | --- |
| [`figure_style.py`](figure_style.py) | Matplotlib style from `figures.yaml` palette/dpi |
| [`figure_registry.py`](figure_registry.py) | Alt text, captions, `section_figures` map, `render_figure_markdown`, `render_section_figures` |
| [`figure_io.py`](figure_io.py) | Shared PNG save + RGB normalization |
| [`figures.py`](figures.py) | Analytical + SI plot generators; `FIGURE_GENERATORS` registry parity map |
| [`figures_sheaf.py`](figures_sheaf.py) | Coverage heatmap + layers overview (`pcolormesh` with grid edges, registry panel) |

`figures.yaml` `section_figures.coverage_page` binds the front-matter heatmap without a figure number; `appendix_full_sheaf` binds the same PNG as Figure 4.

Alt strings in `figures.yaml` are full accessibility descriptions. Captions and alt text use `{{token}}` placeholders resolved at hydration (`z_generate_manuscript_variables.py`). Partial substitution via `variables=` is fail-closed. Unknown tokens fail hydration with `ValueError`. Single-brace `{token}` typos are rejected at hydration.

**Caption rule:** when `caption_prefix` is set (e.g. `Figure 6 (methods). `), `render_figure_markdown` does not also emit a redundant `Figure {n}.` prefix.
