# tests/ — template_pools_rules_tools

Project tests (90% coverage floor on `src/`). Real fixtures under `fonds/`,
`rules/`, and `tools/` template trees — no mocks.

Figure-count tests must derive expectations from `INTEGRATION_FIGURE_SPECS` and
`COVER_FIGURE_FILENAMES` and include a changed-contract negative control; a
literal expected total can conceal drift between generated assets and prose.

## Running

```bash
uv run pytest projects/templates/template_pools_rules_tools/tests/ \
  --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90
```

## Files

The suite's project-owned test modules are:

Tests mirror the `src/` subpackage layout (SUBMODULAR): `tools/test_coverage_extras.py`,
`tools/test_fonds_reader.py`, `tools/test_integration.py`, `tools/test_property_based.py`,
`tools/test_resource_schema.py`, `tools/test_tools_invoker.py`; `rules/test_rules_applier.py`,
`rules/test_strong_rule_evaluator.py`; `figures/test_figures.py`,
`figures/test_generate_figures_script.py`, `figures/test_manuscript_variables.py`.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
