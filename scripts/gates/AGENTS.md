# scripts/gates/AGENTS.md

## Purpose

Optional gate scripts for Hermes-plugin workflows and advisory checks. **None of these run in the default `./run.sh` pipeline or CI** except where a dedicated workflow invokes them explicitly.

## Modules

| Module | Purpose |
|--------|---------|
| `gate_cache` | Hermes cache validation (requires `HERMES_HOME`; opt-in via `scripts/gates/gate_cache.py`) |
| `module_line_count_check` | Advisory line-count gate for `infrastructure/` and `scripts/` (warn ≥800, fail ≥950) |
| `security_scan` | Security scanning gate (bandit, safety, pip-audit) |
| `plugin_export_check` | Hermes plugin export verification (opt-in) |

## Usage

Invoke directly when needed — not wired into default pipeline stages:

```bash
uv run python scripts/gates/security_scan.py
uv run python scripts/gates/gate_cache.py   # Hermes-only; requires HERMES_HOME
```

## See also

- [`scripts/`](../) — Pipeline orchestration scripts
- [`infrastructure/validation/`](../../infrastructure/validation/) — Validation infrastructure
