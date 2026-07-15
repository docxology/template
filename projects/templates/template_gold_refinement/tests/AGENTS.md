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
| `test_figures_submodules.py` | Direct unit tests for the split `src/figures/` subpackage (`_common`/`graphs`/`charts`/`diagrams`) |
| `test_registry_integrity.py` | Manuscript figure/table/equation references, registry parity, figure quality report parity |
| `test_scripts_smoke.py` | Analysis and manuscript-variable scripts, generated reports, SVG companions |
| `test_cover_visualization.py` | Cover-image generation script, generated PNG dimensions and non-blank content |
| `test_coercion.py` | Strict boolean coercion helper used by config parsing |
| `test_dashboard.py` | Interactive HTML dashboard generation from `src/dashboard.py` |
| `test_domain_adapter.py` | `domain_profile.yaml` loading and domain-adapter schema validation |
| `test_edge_cases.py` | Uncovered-path edge cases for evidence, dashboard, figures, and manuscript variables |
| `test_evidence.py` | Evidence registry construction and claim-ledger alignment (`src/evidence.py`) |
| `test_negative_controls.py` | Deliberately broken inputs must fail correctly (negative-control proof for config/composition gates) |
| `test_parsing.py` | Shared parsing helpers used across config and manuscript-variable modules |
| `test_pipeline_policy.py` | `pipeline_policy.py` LLM-review gate reasoning and enablement logic |
| `test_property_monotonicity.py` | Hypothesis property-based tests for monotone purity across refinery stages |
| `test_security_assay.py` | Security assay record construction, table rendering, and claim-boundary summary |

`__init__.py` and `conftest.py` are package/fixture scaffolding, not test files, and are omitted from the table above.

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
