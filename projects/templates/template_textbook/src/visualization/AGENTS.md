# `src/visualization/` — Agent Guide

Deterministic matplotlib figure generation.

**Contents.** `plots.py` builds every chapter figure; `gallery.py` renders the
format gallery from `gallery_specs.yaml`; `_scaffold.py` placeholder generation
honoring the `<part_id>_<stem>.png` filename contract; `registry.py` writes
`figure_registry.json` via atomic I/O.

**Contract.** Figures are generated to `output/figures/` and tracked as public
release artifacts when they stay below the size ceiling; reproduce them with
`scripts/generate_figures.py` (chapter plots plus optional gallery under
`output/figures/gallery/`).

Optional square PNG padding uses Pillow (`uv sync --extra visuals`).

See the project [`AGENTS.md`](../../AGENTS.md) and [`docs/`](../../docs/) for the full map.
