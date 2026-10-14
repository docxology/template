# Source Modules

Reusable AutoResearch project logic lives here. See [`AGENTS.md`](template_autoresearch_project/AGENTS.md) for the full module map.

## Core loop

- `loop/config.py` — loop configuration from `autoresearch.yaml` + manuscript settings
- `loop/loop.py` — deterministic plan/evidence/claim/artifact/readiness orchestration
- `writers/io.py`, `writers/manifests.py`, `writers/payloads.py` — artifact I/O; `writers/figure_dispatch.py` (`FIGURE_DISPATCH`, `render_figure_batch`); `writers/benchmark.py` — benchmark grading (`writers/__init__.py` facade)

## ML task

- `ml/training.py` — numpy-only training primitives; `ml/task.py` — public exports
- `ml/data.py`, `ml/models.py`, `ml/selection.py` — data, evaluation, candidate selection
- `diagnostics/*.py` — probability records, metrics, intervals, reports (`diagnostics/__init__.py` facade)

## Figures

- `figures/figures_core.py` — shared matplotlib primitives
- `figures/figures_ml_*.py` — ML/MNIST/calibration/matrices writers (`figures/__init__.py` barrel)
- `figures/figures_process.py`, `figures/figures_security.py` — process and security figure families
- `figures/figure_registry.py` (facade), `figures/figure_registry_{captions,records}.py` — registry metadata for `figure_registry.json`

## Manuscript hydration

- `manuscript/manuscript_tokens_{core,ml,figures,format}.py` — render-time `{{TOKEN}}` values (`manuscript/manuscript_variables.py` API)
- `manuscript/manuscript_tables_{builders,format}.py` — registry-backed tables; the supported table API is `template_autoresearch_project.manuscript.manuscript_tables`.
- `writers/reports.py` — loop and review markdown renderers

## Governance

- `diagnostics/source_ledger.py`, `writers/artifact_schemas.py`, `writers/research_object.py` — citation ledgers and local manifests
- `security/{artifacts,payloads,render}.py` — deterministic security profile and attestation artifacts
