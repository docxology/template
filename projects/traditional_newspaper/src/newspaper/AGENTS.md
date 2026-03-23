# AGENTS: `src/newspaper/`

## Modules

| Module | Public API |
|--------|------------|
| `layout_spec.py` | `NewspaperLayout`, `LAYOUT`, `geometry_latex_options()`, `multicol_sep_latex()`, `column_count_valid(n)` |
| `sections.py` | `PAGE_SLICES`, `SLICE_BY_STEM`, `slice_stems()`, `manuscript_filenames()`, `manuscript_stems_ordered()`, `slice_count()`, `get_slice(stem)`, `validate_inventory()`, `MANUSCRIPT_OPTIONAL_FILENAMES`, `all_tracked_manuscript_basenames()` |
| `snippets.py` | `multicol_begin`, `multicol_end`, `headline`, `byline`, `rule_line`, `dateline`, `section_label`, `pull_quote`, `classified_line`; internal `_escape_latex_fragment` |
| `content.py` | `FIXTURE_SENTENCES`, `fixture_paragraph(seed=...)`, `fixture_copy(n, seed=...)` |
| `masthead.py` | `render_masthead_png(path, *, seed=42, dpi=200, title=..., tagline=...)` |
| `layout_figure.py` | `render_layout_schematic_png(path, *, layout=None, dpi=150)` |
| `visualization.py` | `configure_matplotlib_bw_style()`, `wordcount_pairs_from_manuscript_stats(data)`, `load_manuscript_stats(path)`, `render_wordcount_bar_chart_bw(path, entries, ...)`, `render_wordcount_chart_from_stats_file(stats_json, out_png, ...)` |
| `section_graphics.py` | `render_section_banner_bw(path, stem, section_title, ...)`, `section_banner_filename(stem)` |
| `__init__.py` | Re-exports above including `render_layout_schematic_png` and visualization helpers |

## Conventions

- `multicol_begin` requires `n >= 2`; `column_count_valid` allows 2–8.
- `headline` / `byline` / other text snippets escape LaTeX specials via `_escape_latex_fragment` (backslash expanded first, then braces).
- Masthead uses `numpy.random.Generator` for rule jitter; title/tagline are plain matplotlib text.
