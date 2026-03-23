# AGENTS: `tests/`

## Files

| File | Focus |
|------|--------|
| `conftest.py` | `sys.path` → `../src`, `MPLBACKEND=Agg` |
| `test_layout_spec.py` | `NewspaperLayout`, `LAYOUT`, `column_count_valid` |
| `test_sections.py` | `PAGE_SLICES`, `validate_inventory`, repo manuscript completeness |
| `test_sections_extended.py` | `get_slice`, `slice_count`, `SLICE_BY_STEM`, `all_tracked_manuscript_basenames` |
| `test_snippets.py` | Core LaTeX fragment builders |
| `test_snippets_extended.py` | `dateline`, `section_label`, `pull_quote`, `classified_line`, `_escape_latex_fragment` |
| `test_content.py` | `fixture_paragraph`, `fixture_copy` |
| `test_masthead.py` | PNG bytes, shape, seed sensitivity |
| `test_layout_figure.py` | Layout schematic PNG bytes, determinism, custom layout |
| `test_script_stats.py` | Subprocess integration for `report_manuscript_stats.py` |
| `test_visualization.py` | Stats parsing, B&W bar chart PNG, grayscale pixel check |
| `test_visualization_script.py` | Subprocess: stats script then `visualization_wordcount_bw.py` |
| `test_section_graphics.py` | Banner PNG bytes, determinism, grayscale, `section_banner_targets` |
| `test_section_banners_script.py` | Subprocess `generate_section_banners.py` path lines |
| `test_init_exports.py` | Package `__init__` surface |
