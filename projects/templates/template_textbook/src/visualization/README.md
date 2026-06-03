# `src/visualization/` — deterministic figure generators

Produces every matplotlib figure the manuscript references. All drawing logic
lives here; `scripts/generate_figures.py` is a thin orchestrator that calls
`generate_all_figures` and prints output paths.

## Modules

| Module | Responsibility |
| --- | --- |
| `plots.py` | The figure generators — `generate_all_figures()` plus the individual plot functions. Produces **4 worked figures** (backed by `textbook.models`) and **12 per-chapter placeholders** named `<part_id>_<stem>.png`. |
| `_scaffold.py` | Shared placeholder helper — draws the labelled stub figure for a chapter that has no bespoke plot yet. |

## Determinism

Figures are reproducible by construction:

- Fixed RNG seeds for any sampled data.
- A single shared matplotlib style (see `textbook_visuals.py`) — no
  environment-dependent fonts or colors.
- `MPLBACKEND=Agg` (headless) is set by the pipeline.

The same inputs always produce the same PNG bytes, so figures can be validated
and diffed in CI.

## Worked vs. placeholder figures

The 4 worked figures plot real outputs from `textbook.models` (e.g. logistic
growth, saturating response, decay) and are the model an author imitates. The 12
placeholders (one per chapter, `<part_id>_<stem>.png`) are intentional stubs:
replace a placeholder with a bespoke generator function as you fill the matching
chapter, keep the filename, and the manuscript reference resolves unchanged.

## Generate

```bash
uv run python scripts/generate_figures.py
# default output: output/figures/
```

Add new figure logic here (with a test in `../../tests/test_visualization.py`),
never in the script.

## Plot-type gallery

`gallery.py` is a worked example of every common scientific plot type (line,
scatter-with-fit, bar, grouped/horizontal bar, histogram, box, violin, heatmap,
contour, quiver field, step, stacked area, error bars, log-log, pie, annotated,
multi-panel). Each function is deterministic and returns a PNG; the registry
`GALLERY` drives `generate_gallery_figures()`. `scripts/generate_figures.py`
writes them to `output/figures/gallery/`, and
`manuscript/appendices/appendix_format_gallery.md` embeds them. Add a new plot by
writing a `(output_dir) -> Path` function and registering it in `GALLERY`.
