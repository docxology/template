# Source Modules

Reusable AutoResearch project logic lives here.

- `config.py` loads project-local loop configuration.
- `loop.py` executes the deterministic plan/evidence/claim/artifact/readiness loop.
- `ml_task.py` loads the local MNIST subset and evaluates bounded numpy neural-network candidates with configurable SGD schedules.
- `ml_task.py` also records epoch histories, learning-rate traces, probabilities, and accepted-candidate error examples.
- `diagnostics.py` derives probability records, class metrics, calibration,
  confusion-pair summaries, generalization gaps, deterministic robustness
  smoke-test metrics, candidate intervals, class-balance counts, bootstrap
  intervals, matched baseline comparison, and probability-quality and
  training-dynamics statistical summaries.
- `writers.py` writes loop artifacts, method ledgers, review decisions, and benchmark scores.
- `reports.py` renders loop, review, and summary Markdown.
- `figure_registry_contract.py` applies the shared caption, method, validation,
  and claim-boundary contract for registry-backed figures.
- `figures.py` writes readiness, ML diagnostic, learning-curve, complexity,
  error-example, calibration, class-metric, confusion-pair, generalization-gap,
  robustness, probability-margin, bootstrap-interval, paired-correctness,
  selective-accuracy, probability-quality, training-dynamics,
  candidate-lifecycle, per-class, class-balance, contact-sheet, and closure-flow figures, then
  registers caption, source, method, validation, alt-text, and claim-boundary
  metadata.
- `manuscript_variables.py` computes render-time manuscript tokens.
