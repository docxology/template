# Gate Scripts

Pipeline gate scripts for template.

## Gates

- `gate_cache` — Validates and populates the cache
- `security_scan` — Runs security scanning (bandit, safety, pip-audit)
- `mypy_ratchet.py` — Compatibility-named strict gate; fails on any typing error.
- `exemplar_export_smoke.py` — Exports each public exemplar to a clean temporary tree, installs its locked project environment, and imports every top-level `src` target.
- `pip_audit_ignore_policy.py` — Requires accountable metadata on every dependency-audit exemption.
- `plugin_export_check` — Verifies plugin exports
- `methods_plan_check` — Validates source or rendered methods contracts for one project or all public exemplars. Source mode runs in unified health; rendered mode is an explicit publication gate.
- `public_capabilities.py` — Audits structural completeness and classifies every discovered public-exemplar test skip.
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
