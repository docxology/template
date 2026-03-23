# AGENTS: `scripts/`

## `generate_masthead.py`

- **Pattern**: Thin orchestrator (path bootstrap, logging, `render_masthead_png`).
- **Env**: `PROJECT_DIR` (optional); `NEWSPAPER_TITLE`, `NEWSPAPER_TAGLINE` override masthead strings (defaults match `masthead.render_masthead_png`).
- **Stdout**: Absolute path to `masthead.png` for analysis manifest collection.

## `generate_layout_schematic.py`

- **Pattern**: Thin orchestrator; calls `render_layout_schematic_png` from `newspaper.layout_figure`.
- **Env**: `PROJECT_DIR` (optional).
- **Stdout**: Absolute path to `layout_schematic.png` for analysis manifest collection.

## `generate_section_banners.py`

- **Pattern**: Thin orchestrator; loops `sections.section_banner_targets()` and calls `render_section_banner_bw` from `newspaper.section_graphics`.
- **Env**: `PROJECT_DIR` (optional).
- **Output**: `output/figures/section_banner_{stem}.png` for each target (19 files: core `02`–`16` plus `S01`, `S02`, `S03`, `98` stems).
- **Stdout**: One absolute path per banner line, for manifest collection.

## `report_manuscript_stats.py`

- **Pattern**: Thin orchestrator; reads `manuscript/*.md` listed by `newspaper.sections.all_tracked_manuscript_basenames()` (core + optional); skips missing files with a warning.
- **Output**: `output/data/manuscript_stats.json` (`project`, `files[]` with `path`, `lines`, `words`, `bytes`).
- **Stdout**: Absolute path to the JSON file.

## `visualization_wordcount_bw.py`

- **Pattern**: Thin orchestrator; requires `output/data/manuscript_stats.json` (run after `report_manuscript_stats.py`; discovery order runs this script last among the four `*.py` files).
- **Output**: `output/figures/wordcount_bars_bw.png` via `newspaper.visualization.render_wordcount_chart_from_stats_file`.
- **Stdout**: Absolute path to the PNG.
- **Exit**: Status `1` if stats JSON is missing.
