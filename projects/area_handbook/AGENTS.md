# AGENTS: `area_handbook`

## Purpose

Reproducible path from structured area evidence to an updated handbook: load corpus, build fixed outline, synthesize per-section scores and gaps, emit Markdown/JSON, plot figures, and render manuscript.

## Layout

```
area_handbook/
├── src/
│   ├── models.py        # Dataclasses including SynthesisResult.gap_threshold
│   ├── corpus_io.py     # load_corpus, validation (unique ids, finite weights)
│   ├── corpus_stats.py  # evidence_counts_by_theme, themes_without_evidence, total_evidence_weight
│   ├── outline.py       # HANDBOOK_TEMPLATE, build_handbook_outline
│   ├── synthesis.py     # DEFAULT_GAP_THRESHOLD, section_coverage_score, synthesize(..., gap_threshold=)
│   ├── handbook_md.py   # Executive summary, gap report, theme table, TOC, full body, glossary
│   ├── metrics.py       # build_metrics_report (extended JSON)
│   └── handbook_plot_data.py  # section_scores_with_gap_flags (gap-status figure)
├── scripts/
│   ├── 01_build_handbook_artifacts.py   # JSON + handbook_body + glossary + handbook_toc
│   └── 02_generate_handbook_figure.py   # three PNGs + figure_registry.json (FigureManager)
├── data/fixtures/riverbend_area.yaml
├── docs/                # architecture + testing (not in PDF)
├── tests/               # 56 tests, 100% src coverage, zero mocks
└── manuscript/          # Numbered sections + S01_/S02_ + handbook_syntax.md
```

## Script imports

Pipeline sets `PYTHONPATH` to `repo`, `infrastructure`, and `project/src`. Scripts prepend `PROJECT_DIR` to `sys.path` and use `from src.module import ...`.

## Configuration

- `manuscript/config.yaml` uses only schema-known keys.
- Corpus data lives under `data/fixtures/` (not in `config.yaml`).

## See also

- [docs/guides/new-project-setup.md](../../docs/guides/new-project-setup.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/testing.md](docs/testing.md)
