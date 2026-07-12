# Template Project Tests

Comprehensive test suite for the `template_template` introspection, metrics, and visualization modules.

## Running Tests

```bash
# From repo root
uv run pytest projects/templates/template_template/tests/ -v

# With coverage
uv run pytest projects/templates/template_template/tests/ --cov=projects/templates/template_template/src/template_template --cov-report=term-missing
```

## Test Coverage

| File | Contract |
|------|----------|
| `test_meta.py` | Introspection, injection, and real-manuscript integration |
| `test_metrics.py` | Metric computation and table generation |
| `test_architecture_viz.py` | Real PNG generation and matrix invariants |
| `test_confidentiality.py` | Public/private discovery boundary |
| `test_edge_cases.py` | Error branches and filesystem fallbacks |
| `test_evidence_contract.py` | Policy-source binding plus manuscript evidence fail-closed controls |

Live test and coverage counts belong in the generated repository metrics, not
this inventory. All tests use real filesystem paths and imports; the project
suite introduces no prohibited mock framework.
