# template_pools_rules_tools TODO

Forward-only backlog for the meta-project exemplar integrating the top-level
`fonds/`, `rules/`, and `tools/` resource-pool directories (read-only from this
project's perspective).

## Current validation evidence

- Project tests and coverage (2026-08-02): 259 passed, 2 skipped, 0 failed; 94.88% total coverage, above the 90% floor. Command: `uv run pytest projects/templates/template_pools_rules_tools/tests --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90`.
- Pre-render validation (2026-08-02): passed with no render-blocking pitfalls or undefined citations.
- Analysis stage (2026-08-02): 6/6 scripts completed successfully; observed 3 fonds, 2/2 rule sets OK, 4 tools discovered and valid, 8 bibliography entries, 5 contacts, and 5 datasets. The non-IMRaD section-schema messages are advisory by design.
- Render stage (2026-08-02): combined PDF generated successfully from 8 manuscript sections; 9 figures found, including the cover art. Render logs contain 0 lines beginning with `!` and the combined PDF contains 0 `??` tokens; `pdfinfo` reports 21 pages.
- Output validation: all component checks pass (PDF, bookends, Markdown, structure, figure registry, evidence registry, design overlays, and artifact manifest). The rendered-provenance binding remains blocked by the shared validator's `ARTIFACT_MANIFEST_INCOMPLETE` comparison of stable generated files; this exemplar does not modify shared infrastructure, so the issue remains recorded here.
- Output copy stage: passed; 121 files copied to `output/templates/template_pools_rules_tools/` and the combined PDF was copied successfully.
- Repo drift gate (2026-08-02): `uv run python scripts/audit/check_template_drift.py --project templates/template_pools_rules_tools --strict` passed.
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

- Extend the discovery adapters in `src/integration.py` when new public fonds/rules/tools ship; do not duplicate the discovered roster in manuscript configuration.
- Add typed loaders for any new resource-pool category before wiring it into `integration.py`.

## Documentation and signposting gaps

- Keep `.agents/skills/template-pools-rules-tools/SKILL.md` aligned with the public resource-pool surface it discovers.
- Keep README, AGENTS, and CLAUDE guidance clear that repo-root resolution relies on `parents[4]` and that the module is named `type_defs.py` (never `types.py`).

## Test and validator gaps

- ~~Add negative-control fixtures for malformed fonds/rules/tools payloads to exercise the fallback paths.~~ **Done** — `tests/test_strong_rule_evaluator.py` gained 20+ negative-control tests (malformed YAML, real rule violations, type-mismatched context values), raising `strong_rule_evaluator.py` from 81.87% to the mid-90s%; each was spot-verified to actually fail when its target guard is removed (regression-discriminating, not coverage-padding). Run `uv run pytest … --cov-report=term-missing` for the current number.
- Extend strong-rule semantic evaluation coverage as new formal constraints are added under `rules/templates/`.

## Ordered improvement ladder

1. Add a fourth fond type (e.g. `template_models`) once that fond exemplar exists. **Still blocked** — needs the fond exemplar to exist first, and touches shared allowlists/docs outside this project; ask before starting.
2. Broaden strong-rule programmatic evaluation as new constraint families ship. **Partially done**: a fifth evaluator (`manifest_freshness`) is implemented and unit-tested in `src/strong_rule_evaluator.py`, but deliberately not wired to a real strong-rule YAML file — that would mean writing into the shared `rules/templates/*/strong/` tree, which needs an explicit go-ahead first (one new file in an existing directory; mechanically low blast-radius, but still crosses this project's read-only boundary). Ask before adding that file.
3. Add per-resource schema assertions whenever a pool gains required fields.
4. ~~Refresh generated docs and the SKILL manifest after any public-surface change.~~ **Done** — `.agents/skills/template-pools-rules-tools/SKILL.md`'s Quick Reference and Pitfalls sections updated to cover `04_validate_strong_rules.py`, `05_generate_figures.py`, `z_generate_manuscript_variables.py`, and this session's gotchas (preamble fence, token case, figure-registry-is-metadata-only, tcolorbox-vs-Beamer).
