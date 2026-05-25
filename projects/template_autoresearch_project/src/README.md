# Source Modules

Reusable AutoResearch project logic lives here.

- `config.py` loads project-local loop configuration.
- `loop.py` executes the deterministic plan/evidence/claim/artifact/readiness loop.
- `ml_task.py` generates the fixed-seed ML task and evaluates bounded candidates.
- `writers.py` writes loop artifacts, method ledgers, review decisions, and benchmark scores.
- `reports.py` renders loop, review, and summary Markdown.
- `figures.py` writes the readiness and ML candidate-score figures.
- `manuscript_variables.py` computes render-time manuscript tokens.
