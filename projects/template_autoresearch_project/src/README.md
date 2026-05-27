# Source Modules

Reusable AutoResearch project logic lives here. See [`AGENTS.md`](AGENTS.md) for the full module map.

## Core loop

- `config.py` — loop configuration from `autoresearch.yaml` + manuscript settings
- `loop.py` — deterministic plan/evidence/claim/artifact/readiness orchestration
- `writers.py` — artifact I/O; `writers_figure_dispatch.py` (`FIGURE_DISPATCH`, `render_figure_batch`); `writers_benchmark.py` — benchmark grading

## ML task

- `ml_training.py` — numpy-only training primitives; `ml_task.py` — public exports
- `ml_data.py`, `ml_models.py`, `ml_selection.py` — data, evaluation, candidate selection
- `diagnostics_*.py` — probability records, metrics, intervals, reports (`diagnostics.py` facade)

## Figures

- `figures_core.py` — shared matplotlib primitives
- `figures_ml_*.py` — ML/MNIST/calibration/matrices writers (`figures_ml.py` barrel)
- `figures_process.py`, `figures_security.py` — process and security figure families
- `figure_registry.py` (facade), `figure_registry_{captions,records}.py` — registry metadata for `figure_registry.json`

## Manuscript hydration

- `manuscript_tokens_{core,ml,figures,format}.py` — render-time `{{TOKEN}}` values (`manuscript_variables.py` facade)
- `manuscript_tables_{builders,format}.py` — registry-backed tables (`manuscript_tables.py` facade)
- `reports.py` — loop and review markdown renderers

## Governance

- `source_ledger.py`, `artifact_schemas.py`, `research_object.py` — citation ledgers and local manifests
- `security.py` — deterministic security profile and attestation artifacts
