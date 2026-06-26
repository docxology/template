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
| `test_formalisms.py` | Formalism uniqueness, equation labels, and traceability rows |
| `test_integrity.py` | Integrity dimensions, evidence tiers, residual-risk records |
| `test_figures.py` | Figure spec uniqueness, graph topology contracts, PNG/SVG generation, quality report thresholds |
| `test_registry_integrity.py` | Manuscript figure/table/equation references, registry parity, figure quality report parity |
| `test_scripts_smoke.py` | Analysis and manuscript-variable scripts, generated reports, SVG companions |

## Visualization QA contract

Visualization tests should protect source ownership, not just file existence.
When a figure changes, keep these checks aligned:

- no duplicate figure names, labels, PNG paths, or SVG paths
- generated registry exactly matches `FIGURE_SPECS`
- every figure has PNG and SVG output
- graph figures expose deterministic builder functions with asserted node and
  edge counts
- `figure_quality_report.json` records dimensions, nonblank pixel fraction,
  color variance, PNG/SVG existence, and registry parity
- manuscript variables expose the figure-quality summary without dangling
  placeholders

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
