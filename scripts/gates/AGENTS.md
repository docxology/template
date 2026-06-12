# scripts/gates/AGENTS.md

## Purpose

Optional gate scripts for Hermes-plugin workflows and advisory checks. **None of these run in the default `./run.sh` pipeline or CI** except where a dedicated workflow invokes them explicitly.

## Modules

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `gate_cache.py` | `infrastructure.core.cache_gate.run_cache_gate` | Hermes cache validation (requires `HERMES_HOME`; opt-in) |
| `methods_plan_check.py` | `infrastructure.methods.build_methods_orchestration_plan`, `validate_methods_orchestration_plan` | Methods-plan gate: validates every public exemplar (or one `--project`) has stage `definition_of_done`, a manuscript methods/methodology section, and artifact-manifest / evidence-registry surfaces. Fails on `error`-severity issues (opt-in) |
| `module_line_count_check.py` | `infrastructure.validation.line_count.scan_infrastructure_and_scripts`, `scan_project_scripts` | Line-count gate: infra/scripts warn ≥800 fail ≥950; project scripts warn ≥150 fail ≥250 |
| `security_scan.py` | `infrastructure.validation.security_gate.run_security_scan` | Security scanning (bandit, safety, pip-audit) |
| `plugin_export_check.py` | `infrastructure.validation.plugin_export.run_plugin_export_check` | Hermes plugin export verification (opt-in) |

## Usage

Invoke directly when needed — not wired into default pipeline stages:

```bash
uv run python scripts/gates/security_scan.py
uv run python scripts/gates/gate_cache.py   # Hermes-only; requires HERMES_HOME

# Methods-plan gate (opt-in; NOT wired into default pipeline or CI).
# Run after a pipeline pass so generated output reports exist, or against a
# fully-specified project. Defaults to every public exemplar; pass --project
# for one. Mirrors `python -m infrastructure.methods plan --check`.
uv run python scripts/gates/methods_plan_check.py
uv run python scripts/gates/methods_plan_check.py --project templates/template_code_project
```

## See also

- [`scripts/`](../) — Pipeline orchestration scripts
- [`infrastructure/validation/`](../../infrastructure/validation/) — Validation infrastructure
