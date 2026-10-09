# scripts/gates/AGENTS.md

## Purpose

Gate scripts for release, health, Hermes-plugin, and advisory checks. The table
states which surfaces are wired into unified health or remain explicit.

## Modules

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `infra_ci_partition.py` | `infrastructure.core.testing.ci_infra_partition`, `infrastructure.core.testing.ci_infra_coverage` | Complete ordinary infrastructure matrix, exact shard data export and required ≥60% coverage union |
| `ci_policy.py` | `infrastructure.core.ci_policy.required_ci_jobs` | Source-owned complete job selection for CI Gate; missing or extra hosted job outcomes refuse completion |
| `gate_cache.py` | `infrastructure.core.cache_gate.run_cache_gate` | Hermes cache validation (requires `HERMES_HOME`; opt-in) |
| `methods_plan_check.py` | `infrastructure.methods.audit_methods_projects` | All-public or single-project source/rendered methods audit. Source mode runs in unified health; rendered mode remains an explicit publication gate. |
| `public_capabilities.py` | `infrastructure.project.public_capabilities.audit_public_capabilities` | Deterministic fail-closed syntax, structure, package/Python, render, hydration, analysis, and skip-contract manifest for every canonical public exemplar. |
| `check_private_project_promotion.py` | `infrastructure.project.promotion.main` | Compatibility entrypoint for candidate security scanning and composite promotion evaluation. |
| `module_line_count_check.py` | `infrastructure.validation.line_count.scan_infrastructure_and_scripts`, `scan_project_scripts` | Line-count gate: infra/scripts warn ≥800 fail ≥950; project scripts warn ≥150 fail ≥250; current oversized source modules use expiring downward-only ratchets |
| `status_freshness.py` | `parse_status_rows`, `freshness_findings` | Fail-closed six-month freshness check for every dated `STATUS.md` subsystem row and its ledger header |
| `security_scan.py` | `infrastructure.validation.security_gate.run_security_scan` | Security scanning (bandit, safety, pip-audit) |
| `plugin_export_check.py` | `infrastructure.validation.plugin_export.run_plugin_export_check` | Hermes plugin export verification (opt-in) |
| `installed_public.py` | `infrastructure.project.installed_acceptance.run_installed_acceptance` | Genuine source-bound root/public installed-wheel matrix: all26 scopes on all3 supported Python minors, locked transitives, declared provider wheels, outside-source isolated probes |
| `public_readiness.py` | `infrastructure.project.public_readiness.run_public_readiness`, `infrastructure.project.public_acceptance.run_public_acceptance` | Isolated deterministic readiness or source-bound whole-selection supported-runtime acceptance matrix for every public exemplar |

## Usage

Invoke directly when needed — not wired into default pipeline stages:

```bash
uv run python scripts/gates/security_scan.py
uv run python scripts/gates/gate_cache.py   # Hermes-only; requires HERMES_HOME

# Source mode is part of unified health; rendered mode checks generated evidence.
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode source
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode rendered
uv run python scripts/gates/methods_plan_check.py --project templates/template_code_project
uv run python scripts/gates/public_capabilities.py
uv run python scripts/gates/check_private_project_promotion.py --project-root /path/to/candidate
uv run python scripts/gates/public_readiness.py --json
uv run python scripts/gates/public_readiness.py --include-ollama-tests --allow-skips
```

## See also

- [`scripts/`](../) — Pipeline orchestration scripts
- [`infrastructure/validation/`](../../infrastructure/validation/) — Validation infrastructure

## Release acceptance modules

| Module | Role |
| --- | --- |
| `native_formats.py` | Execute the source-bound public native-format acceptance producer. |
