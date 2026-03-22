# density_bioscales

Cross-scale density models: ideal gases, reference liquids, insect-scale composite mixtures, buoyancy helpers, and interval-valued sweeps.

## Quick start

```bash
# From repository root
uv run python scripts/01_run_tests.py --project density_bioscales
uv run python scripts/02_run_analysis.py --project density_bioscales
uv run python scripts/03_render_pdf.py --project density_bioscales
```

## Layout

| Path | Purpose |
|------|---------|
| `src/` | Physics and composition modules |
| `tests/` | Pytest suite (no mocks, ≥90% coverage) |
| `scripts/` | Tables and figures → `output/` |
| `manuscript/` | Markdown sections + `config.yaml` |

## Epistemic note

Preset mass splits and the `internal_gas` effective density are **illustrative** — not taxonomic measurements. See `03b_insect_composite_model.md`.
