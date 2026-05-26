# Source Modules

Reusable AutoResearch project logic lives here.

- `config.py` loads project-local loop configuration.
- `loop.py` executes the deterministic plan/evidence/claim/artifact/readiness loop.
- `ml_training.py` implements the bounded numpy training loop; `ml_task.py`
  preserves the public orchestration exports.
- `ml_data.py`, `ml_models.py`, and `ml_selection.py` expose data-loading,
  model/metric, and candidate-selection entry points.
- `diagnostics_reports.py` derives probability records, class metrics, calibration,
  confusion-pair summaries, generalization gaps, deterministic robustness
  smoke-test metrics, candidate intervals, class-balance counts, bootstrap
  intervals, matched baseline comparison, and probability-quality and
  training-dynamics statistical summaries.
- `diagnostics.py`, `diagnostics_records.py`, `diagnostics_metrics.py`, and
  `diagnostics_intervals.py` preserve focused compatibility exports.
- `writers.py` writes loop artifacts, method ledgers, review decisions, and benchmark scores.
- `reports.py` renders loop, review, and summary Markdown.
- `figure_registry_contract.py` applies the shared caption, method, validation,
  and claim-boundary contract for registry-backed figures.
- `figures_core.py` writes readiness, ML diagnostic, learning-curve, complexity,
  error-example, calibration, class-metric, confusion-pair, generalization-gap,
  robustness, probability-margin, bootstrap-interval, paired-correctness,
  selective-accuracy, probability-quality, training-dynamics,
  candidate-lifecycle, per-class, class-balance, contact-sheet, and closure-flow figures, then
  registers caption, source, method, validation, alt-text, and claim-boundary
  metadata.
- `figures.py`, `figures_ml.py`, `figures_process.py`, and
  `figures_security.py` preserve compatibility exports by figure family.
- `manuscript_variables.py` computes render-time manuscript tokens.
- `source_ledger.py`, `artifact_schemas.py`, and `research_object.py` validate
  citation-source ledgers and generate local governance manifests.
