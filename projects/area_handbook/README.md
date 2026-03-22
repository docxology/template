# area_handbook

Holistic **area reporting** pipeline: a versioned YAML corpus (themes + weighted evidence) is synthesized into handbook-style Markdown, JSON metrics, and figures, then rendered through the template PDF/HTML/slides pipeline.

## Quick start

```bash
uv run python scripts/01_run_tests.py --project area_handbook
uv run python scripts/02_run_analysis.py --project area_handbook
uv run python scripts/03_render_pdf.py --project area_handbook
```

## Layout

| Path | Role |
|------|------|
| `data/fixtures/riverbend_area.yaml` | Offline exemplar corpus |
| `src/` | Corpus I/O, stats, outline, synthesis, Markdown builders, metrics |
| `scripts/` | Thin orchestrators (artifacts + two figures) |
| `manuscript/` | Multi-section handbook narrative |
| `docs/` | Architecture and testing notes (not rendered into PDF) |
| `output/` | Generated data, figures, PDF (disposable) |

## Outputs (analysis stage)

- `output/data/handbook_report.json` — metrics, outline, gaps
- `output/data/handbook_body.md` — full Markdown rollup (summary + gap report + theme counts + sections)
- `output/data/handbook_toc.md` — outline only
- `output/figures/handbook_evidence_coverage.png` — section scores
- `output/figures/handbook_evidence_by_theme.png` — row counts per theme

See [AGENTS.md](AGENTS.md) for APIs and [docs/architecture.md](docs/architecture.md) for the data-flow diagram.
