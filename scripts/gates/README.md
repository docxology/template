# Gate Scripts

Pipeline gate scripts for template.

## Gates

- `gate_cache` — Validates and populates the cache
- `infra_ci_partition.py` — Emits the complete ordinary infrastructure CI matrix or packages/verifies its actual branch-coverage union; selection and coverage implementations reside in Layer 1.
- `ci_policy.py` — Emits the complete source-owned hosted job set; CI Gate refuses missing, extra, failed, or unjustifiably skipped outcomes.
- `security_scan` — Runs security scanning (bandit, safety, pip-audit)
- `mypy_ratchet.py` — Compatibility-named strict gate; fails on any typing error.
- `installed_public.py` — Builds genuine root and public exemplar wheels, admits exact source/resource bytes, supplies declared provider wheels and locked transitives, and probes isolated installed runtimes outside source. See [the installed-wheel matrix](../../docs/development/installed-wheel-matrix.md).
- `pip_audit_ignore_policy.py` — Requires accountable metadata on every dependency-audit exemption.
- `plugin_export_check` — Verifies plugin exports
- `methods_plan_check` — Validates source or rendered methods contracts for one project or all public exemplars. Source mode runs in unified health; rendered mode is an explicit publication gate.
- `public_capabilities.py` — Emits the deterministic public-exemplar capability manifest and fails closed on roster/matrix, package/Python, source/test syntax, render, hydration, analysis, and skip-contract drift.
- `check_private_project_promotion.py` — Candidate security scan and composite private-promotion gate, with the historical script entrypoint retained.

```bash
# Methods gates (all public exemplars, or one --project)
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode source
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode rendered
uv run python scripts/gates/methods_plan_check.py --project templates/template_code_project
```

## Running

For ordinary development, start with the existing direct local lane for the
area changed. The [local command map](../../docs/maintenance/ci-local.md) lists
owning tests, supported lanes and the separate release acceptance route.
Run these commands from repository root:

```bash
# Inspect a selected development lane before running it
./scripts/shell/ci_local.sh --no-act --dry-run -j lint
./scripts/shell/ci_local.sh --no-act -j lint

# Inspect all supported direct lanes
./scripts/shell/ci_local.sh --no-act --list

# Run the complete static health registry
uv run --no-sync --offline python -m infrastructure.core.health --json
```

Focused local feedback must be followed by the required CI matrix and release
acceptance for the exact source revision. The local wrapper documents which
workflow jobs require `act` or GitHub Actions.
