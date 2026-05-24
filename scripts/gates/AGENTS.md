# scripts/gates/AGENTS.md

## Purpose

Optional gate scripts for Hermes-plugin workflows and advisory checks. **None of these run in the default `./run.sh` pipeline or CI** except where a dedicated workflow invokes them explicitly.

## Modules

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `gate_cache.py` | `infrastructure.core.cache_gate.run_cache_gate` | Hermes cache validation (requires `HERMES_HOME`; opt-in) |
| `module_line_count_check.py` | `infrastructure.validation.line_count.scan_infrastructure_and_scripts`, `scan_project_scripts` | Line-count gate: infra/scripts warn ≥800 fail ≥950; project scripts warn ≥150 fail ≥250 |
| `security_scan.py` | `infrastructure.validation.security_gate.run_security_scan` | Security scanning (bandit, safety, pip-audit) |
| `plugin_export_check.py` | `infrastructure.validation.plugin_export.run_plugin_export_check` | Hermes plugin export verification (opt-in) |

## Usage

Invoke directly when needed — not wired into default pipeline stages:

```bash
uv run python scripts/gates/security_scan.py
uv run python scripts/gates/gate_cache.py   # Hermes-only; requires HERMES_HOME
```

## See also

- [`scripts/`](../) — Pipeline orchestration scripts
- [`infrastructure/validation/`](../../infrastructure/validation/) — Validation infrastructure
