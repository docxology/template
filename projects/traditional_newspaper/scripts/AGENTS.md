# AGENTS: `scripts/`

## `generate_masthead.py`

- **Pattern**: Thin orchestrator (path bootstrap, logging, `render_masthead_png`).
- **Env**: `PROJECT_DIR` (optional); `NEWSPAPER_TITLE`, `NEWSPAPER_TAGLINE` override masthead strings (defaults match `masthead.render_masthead_png`).
- **Stdout**: Absolute path to `masthead.png` for analysis manifest collection.

## `report_manuscript_stats.py`

- **Pattern**: Thin orchestrator; reads `manuscript/*.md` listed by `newspaper.sections.all_tracked_manuscript_basenames()` (core + optional); skips missing files with a warning.
- **Output**: `output/data/manuscript_stats.json` (`project`, `files[]` with `path`, `lines`, `words`, `bytes`).
- **Stdout**: Absolute path to the JSON file.
