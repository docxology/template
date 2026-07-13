# Gate Scripts

Pipeline gate scripts for template.

## Gates

- `gate_cache` — Validates and populates the cache
- `security_scan` — Runs security scanning (bandit, safety, pip-audit)
- `mypy_ratchet.py` — Fails on package typing-debt growth or errors in new files.
- `exemplar_export_smoke.py` — Exports each public exemplar to a clean temporary tree, installs its locked project environment, and imports every top-level `src` target.
- `pip_audit_ignore_policy.py` — Requires accountable metadata on every dependency-audit exemption.
- `plugin_export_check` — Verifies plugin exports
- `methods_plan_check` — Validates the methods-orchestration contract (stage definition-of-done, manuscript methods section, artifact-manifest / evidence-registry surfaces) per project. **Opt-in: NOT wired into the default pipeline or CI.**

```bash
# Opt-in methods-plan gate (all public exemplars, or one --project)
uv run python scripts/gates/methods_plan_check.py
uv run python scripts/gates/methods_plan_check.py --project templates/template_code_project
```

## Running

```bash
# Run all gates
./run.sh gates

# Dry-run (skip actual changes)
./run.sh gates --dry-run
```
