# Gate Scripts

## Purpose

Gate scripts that run as part of the template pipeline. Gates are atomic validation or transformation steps that record metrics and determine pipeline progression.

## Modules

| Module | Purpose |
|--------|---------|
| `gate_cache` | Cache validation and population gate |
| `security_scan` | Security scanning gate (bandit, safety, pip-audit) |
| `plugin_export_check` | Plugin export verification gate |

## Usage

Gates are invoked by the pipeline orchestrator (`scripts/execute_pipeline.py`) or directly via `./run.sh gates`.

## See also

- [`scripts/` ..](../../) — Pipeline orchestration scripts
- [`infrastructure/validation/`](../../infrastructure/validation/) — Validation infrastructure
