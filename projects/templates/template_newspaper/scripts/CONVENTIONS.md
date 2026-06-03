# Script Conventions

- **Naming:** `NN_verb_noun.py`; the numeric prefix sets Stage-02 run order.
  `_bootstrap.py` (underscore) is a helper, not a stage.
- **Shape:** parse args → call one or two `src/newspaper` functions → write
  artifacts → return an exit code. No domain logic in scripts.
- **Paths:** resolve via `_bootstrap` (project root + repo root); never hard-code
  absolute paths.
- **Logging:** `_bootstrap.get_logger(name)` — infrastructure logger if present,
  else stdlib.
- **Artifacts:** write only under `output/`. Emit a machine-readable report
  (`output/data/*.json`) alongside human output.
- **Failure:** loud and non-zero; `--strict` promotes soft warnings (over-set) to
  failures.
