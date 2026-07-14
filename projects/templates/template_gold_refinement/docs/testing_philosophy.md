# Testing Philosophy

## Zero-Mock Policy

All tests use real data, real computation, and real files. No `MagicMock`,
`mocker.patch`, or `unittest.mock` is permitted.

## Test categories

| Category | File | Coverage |
|----------|------|----------|
| Purity & karat | `test_purity.py` | 97% |
| Refinery pipeline | `test_refinery.py` | 97% |
| Config schema | `test_config.py` | 93% |
| Token composition | `test_composition.py` | 97% |
| Assay validation | `test_assay.py` | 100% |
| Manuscript variables | `test_manuscript_variables.py` | 96% |
| Seed sensitivity and report integrity | `test_seed_sensitivity.py`, `test_scripts_smoke.py` | Determinism, technical replicates, interval metadata, minimum-`n`, bootstrap, tamper rejection |

## Key invariants tested

1. **Monotone purity**: purity strictly increases across all refinery stages
2. **Deterministic tokens**: same seed + lexicon = same token plan
3. **Token coverage**: every `{{TOKEN}}` in manuscript source is generated
4. **Config validation**: invalid config raises `GoldRefinementConfigError`
5. **Karat grading**: purity maps to correct standard karat grade
6. **Seed-report provenance**: generated sensitivity JSON must equal a fresh deterministic recomputation from the current configuration
7. **Fail-closed validation**: contradicted claims, missing generated figures, malformed manuscript bytes, and structural output failures cannot produce a green Stage 04 result

## Commands

```bash
uv run pytest projects/templates/template_gold_refinement/tests/ -v
uv run pytest projects/templates/template_gold_refinement/tests/ \
  --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90
```
