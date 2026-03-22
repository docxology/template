# tests/ — area_handbook

| Module | Focus |
|--------|--------|
| `test_corpus_io.py` | YAML/JSON load, validation, duplicate ids, empty fields, NaN weights |
| `test_corpus_stats.py` | Theme counts, unused themes, total weight |
| `test_handbook_md.py` | Markdown builders, gap report, TOC depth, theme table with zero rows |
| `test_outline_synthesis_metrics.py` | Outline, `section_coverage_score`, `synthesize` thresholds, metrics dict |
| `test_handbook_plot_data.py` | `section_scores_with_gap_flags` vs metrics / sparse corpus |
| `test_integration.py` | End-to-end fixture pipeline |
| `test_init_exports.py` | `src.__all__` |

**56 tests**, 100% line/branch coverage on `src/`, zero mocks.

See [../docs/testing.md](../docs/testing.md).
