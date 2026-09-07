# Testing Philosophy

## Zero-Mock Policy

All tests use real data, real computation, and real files. No `MagicMock`,
`mocker.patch`, or `unittest.mock` is permitted.

## Test categories

The suite covers: purity/karat grading (`test_purity.py`), the refinery
pipeline (`test_refinery.py`, `test_property_monotonicity.py`), config schema
(`test_config.py`, `test_negative_controls.py`), token composition
(`test_composition.py`), assay and evidence validation (`test_assay.py`,
`test_evidence.py`), manuscript variables
(`test_manuscript_variables.py`), figures and registries (`test_figures.py`,
`test_figures_submodules.py`, `test_registry_integrity.py`), and the
dashboard/policy/cover/security/boundary surfaces. The full file map with
coverage areas lives in [`../tests/AGENTS.md`](../tests/AGENTS.md).

Live test count and achieved coverage are generated — see
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); do not
copy measured percentages into this file.

## Key invariants tested

1. **Monotone purity**: purity strictly increases across all refinery stages
2. **Deterministic tokens**: same seed + lexicon = same token plan
3. **Token coverage**: every `{{TOKEN}}` in manuscript source is generated
4. **Config validation**: invalid config raises `GoldRefinementConfigError`
5. **Karat grading**: purity maps to correct standard karat grade

## Commands

```bash
uv run pytest projects/templates/template_gold_refinement/tests/ -v
uv run pytest projects/templates/template_gold_refinement/tests/ \
  --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90
```
