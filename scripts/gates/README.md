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

```bash
# Run all gates
./run.sh gates

# Dry-run (skip actual changes)
./run.sh gates --dry-run
```
