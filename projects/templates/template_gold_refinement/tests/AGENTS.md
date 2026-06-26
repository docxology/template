# tests/ — Gold Refinement Test Suite

## Overview

Tests for the gold-refinement domain logic. All tests use real data and
computation — no mocks.

## Files

| File | Coverage area |
|------|--------------|
| `test_purity.py` | Karat grading, purity formatting, nines counting, monotone enforcement |
| `test_refinery.py` | Refinery pipeline stages, stage lookup, purity progression |
| `test_config.py` | Config schema validation, lexicon/slot parsing, section conditions |
| `test_composition.py` | Token plan generation, deterministic selection, section composition |
| `test_assay.py` | Claim records, assay reports, purity computation from claims |
| `test_manuscript_variables.py` | Variable generation, token coverage, live cross-reference test |

## Zero-Mock Policy

No `MagicMock`, `mocker.patch`, or `unittest.mock`. All tests exercise real
code paths with real data.

## Commands

```bash
# Run all tests
uv run pytest projects/templates/template_gold_refinement/tests/ -v

# With coverage gate (90% minimum)
uv run pytest projects/templates/template_gold_refinement/tests/ \
  --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90
```
