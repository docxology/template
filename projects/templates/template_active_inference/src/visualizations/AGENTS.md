# Visualization Notes

Use the headless Agg backend and pin `savefig` metadata so figures are byte-reproducible across machines and matplotlib versions. Every figure is derived from a substantive generated data artifact, not hard-coded values.

## Figure registry

| Module | Role |
| --- | --- |
| [`figure_style.py`](figure_style.py) | Matplotlib style from `figures.yaml` palette/dpi (includes pass/fail/proved/sorry roles) |
| [`figure_registry.py`](figure_registry.py) | Alt text, captions, `section_figures` map, markdown renderers, `write_figure_registry_json()` |
| [`figure_helpers.py`](figure_helpers.py) | `styled_figure()` context, `save_styled_figure`, `style_grid` |
| [`figure_io.py`](figure_io.py) | Shared PNG save + RGB normalization |
| [`figures.py`](figures.py) | Analytical + SI plot generators; `FIGURE_GENERATORS` registry parity map |
| [`figures_diagrams.py`](figures_diagrams.py) | Schematic/dashboard figures (invariants, T-maze, architecture, Lean, GNN) |
| [`lean_boundary.py`](lean_boundary.py) | Lean module scanner for boundary-status table |
| [`figures_sheaf.py`](figures_sheaf.py) | Coverage heatmap + layers overview (`figures_sheaf_{payload,draw}.py`) |

`generate_all_figures()` writes `output/figures/figure_registry.json` (keys `fig:{id}`) for output validation. Source metadata remains in root `figures.yaml`.

`figures.yaml` `section_figures.coverage_page` binds the front-matter heatmap without a figure number; `appendix_full_sheaf` binds repeat embeddings with `labeled: false` to avoid duplicate pandoc-crossref labels.

Alt strings in `figures.yaml` are full accessibility descriptions. Captions and alt text use `{{token}}` placeholders resolved at hydration (`z_generate_manuscript_variables.py`). Partial substitution via `variables=` is fail-closed. Unknown tokens fail hydration with `ValueError`. Single-brace `{token}` typos are rejected at hydration.

**Caption rule:** pandoc-crossref owns all figure numbering. `render_figure_markdown` emits one `{#fig:id}` label per labeled figure with the caption in the image alt slot (verbose description rides `fig-alt`) and **never** a hand-written `Figure N` / `*Figure ...*` line; reused figures use empty alt + a `Reproduced from [@fig:id]` cite (unnumbered). `caption_prefix`/`number` in `figures.yaml` are deprecated and ignored.

**Heatmap:** `figures_sheaf_draw.draw_coverage_heatmap` draws IMRAD block labels on the left margin when `heatmap.group_separator` is enabled in `manuscript/sheaf/coverage.yaml`.
