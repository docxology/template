# template_pools_rules_tools TODO

Forward-only backlog for the meta-project exemplar integrating the top-level
`fonds/`, `rules/`, and `tools/` resource-pool directories (read-only from this
project's perspective).

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_pools_rules_tools/tests/ --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90`
- Type-checking: `uv run mypy projects/templates/template_pools_rules_tools/src --config-file projects/templates/template_pools_rules_tools/pyproject.toml`
- Strong-rule validation gate: `uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Live test count and measured coverage percentage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (regenerated, never hardcoded here).

## Integrity and template-status gaps

- Keep the three resource directories read-only: never write back to `fonds/`, `rules/`, or `tools/` from this project.
- Keep `src/type_defs.py` the single source of truth for all TypedDict shapes; no inline dicts and no `Any` in public signatures.
- Keep graceful-fallback behavior everywhere — `src/` functions return `None` or empty collections when files are absent and never raise.
- Confirm every `pytest.mark.skipif` guard keeps an accurate resource file-path check as pool contents evolve.

## Configurable-surface gaps

- Extend the `integration:` block in `manuscript/config.yaml` when new public fonds/rules/tools ship.
- Add typed loaders for any new resource-pool category before wiring it into `integration.py`.

## Documentation and signposting gaps

- Keep `.agents/skills/template-pools-rules-tools/SKILL.md` aligned with the public resource-pool surface it discovers.
- Keep README, AGENTS, and CLAUDE guidance clear that repo-root resolution relies on `parents[4]` and that the module is named `type_defs.py` (never `types.py`).

## Test and validator gaps

- Add negative-control fixtures for malformed fonds/rules/tools payloads to exercise the fallback paths.
- Extend strong-rule semantic evaluation coverage as new formal constraints are added under `rules/templates/`.

## Ordered improvement ladder

1. Add a fourth fond type (e.g. `template_models`) once that fond exemplar exists.
2. Broaden strong-rule programmatic evaluation as new constraint families ship.
3. Add per-resource schema assertions whenever a pool gains required fields.
4. Refresh generated docs and the SKILL manifest after any public-surface change.
