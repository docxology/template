# scripts/

Thin orchestrators only. Domain logic lives in `../src/`.

| Script | Output |
|--------|--------|
| `01_build_handbook_artifacts.py` | `output/data/handbook_report.json`, `area_outline.json`, `handbook_body.md`, `theme_glossary.md` |
| `02_generate_handbook_figure.py` | `output/figures/handbook_evidence_coverage.png` |

Requires `PROJECT_DIR` (set by `scripts/02_run_analysis.py`) or falls back to project root from `__file__`.
