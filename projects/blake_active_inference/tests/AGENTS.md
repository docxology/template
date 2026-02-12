# Tests - Blake Active Inference

## Purpose

Test suite for visualization and manuscript validation.

## Modules

- `test_visualization.py` - 30 tests for figure generation
- `test_manuscript.py` - 23 tests for manuscript structure

## Quick Reference

```bash
# Run all tests
uv run pytest projects/blake_active_inference/tests/ -v

# Run with coverage
uv run pytest projects/blake_active_inference/tests/ --cov=projects/blake_active_inference/src
```

## Test Policies

- All figures validated for minimum font size (16pt)
- No unicode subscripts allowed (LaTeX compatibility)
- All citations must resolve to `references.bib`
- Figure minimum size: 50KB (resolution check)

## Entry Points

- `test_visualization.py::TestVisualizationModule` - Core tests
- `test_manuscript.py::TestThemeCountConsistency` - Consistency checks
