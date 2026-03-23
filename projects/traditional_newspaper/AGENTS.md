# AGENTS: `traditional_newspaper/`

## Purpose

Pipeline exemplar: **16 core markdown folios** + **supplemental `S01`–`S03`** + **glossary `98`** + **custom preamble** (11×17 in, three columns) + **deterministic masthead** figure. No cross-project imports; logic in `src/newspaper/`.

## Layout

| Path | Role |
|------|------|
| `src/newspaper/layout_spec.py` | `NewspaperLayout`, `LAYOUT`, `column_count_valid(n)` |
| `src/newspaper/sections.py` | `PAGE_SLICES`, `SLICE_BY_STEM`, `get_slice`, `slice_count`, `manuscript_stems_ordered`, `validate_inventory`, `MANUSCRIPT_OPTIONAL_FILENAMES`, `all_tracked_manuscript_basenames()` |
| `src/newspaper/snippets.py` | `{=latex}` helpers: `multicol_*`, `headline`, `byline`, `rule_line`, `dateline`, `section_label`, `pull_quote`, `classified_line` |
| `src/newspaper/content.py` | `FIXTURE_SENTENCES`, `fixture_paragraph`, `fixture_copy` (deterministic filler) |
| `src/newspaper/masthead.py` | `render_masthead_png(path, *, seed=42, title=..., tagline=...)` |
| `scripts/generate_masthead.py` | Masthead PNG; env `NEWSPAPER_TITLE`, `NEWSPAPER_TAGLINE` |
| `scripts/generate_layout_schematic.py` | Tabloid/column schematic PNG (`layout_schematic.png`) |
| `scripts/generate_section_banners.py` | B\&W desk banners `section_banner_{stem}.png` for folios `02`–`16` and supplements |
| `scripts/report_manuscript_stats.py` | Word/line counts → `output/data/manuscript_stats.json` |
| `scripts/visualization_wordcount_bw.py` | B&W word-count bar chart → `output/figures/wordcount_bars_bw.png` (requires stats JSON) |
| `src/newspaper/visualization.py` | Monochrome matplotlib helpers and word-count chart builders |
| `src/newspaper/section_graphics.py` | `render_section_banner_bw`, `section_banner_filename`; uses BW style from `visualization` |
| `manuscript/01_*.md` … `16_*.md` | Core folios; front page includes masthead + optional `\cite` |
| `manuscript/S01_*.md` … `S03_*.md` | Supplemental (after 16, before 98) |
| `manuscript/98_*.md` | Glossary table |
| `docs/` | Modular docs hub ([`docs/README.md`](docs/README.md), [`docs/AGENTS.md`](docs/AGENTS.md)) |

## Discovery

Listed by `discover_projects()` when under `projects/` with `manuscript/config.yaml`, `src/`, `tests/`.

## Testing

- `tests/conftest.py` adds `src/` to `sys.path`, sets `MPLBACKEND=Agg`.
- `test_script_stats.py` runs `report_manuscript_stats.py` via **subprocess** (no mocks).
- Coverage gate: 90%+ on `projects/traditional_newspaper/src` (via root test orchestrator).

## Dependencies

Project `pyproject.toml` lists `matplotlib` and `numpy` (also in root workspace deps for scripts without a local `.venv`).
