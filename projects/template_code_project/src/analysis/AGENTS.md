# `template_code_project/src/analysis/` - agent guide

## Purpose

Importable analysis orchestration for the code exemplar.

## Rules

- Keep mathematical primitives in `src/optimizer.py` and `src/invariants.py`.
- Keep CLI parsing in `scripts/`; this package should expose callable workflow
  functions.
- Keep generated file writes explicit and covered by tests.
- Preserve deterministic experiment inputs from `experiment_config.py`.

## See Also

- [`README.md`](README.md) - quick reference
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
