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

| File | Cluster | Contract |
|------|---------|----------|
| `core/test_meta.py` | `core` | Introspection, injection, and real-manuscript integration |
| `metrics/test_metrics.py` | `metrics` | Metric computation and table generation |
| `figures/test_architecture_viz.py` | `figures` | Real PNG generation and matrix invariants |
| `core/test_confidentiality.py` | `core` | Public/private discovery boundary |
| `core/test_edge_cases.py` | `core` | Error branches and filesystem fallbacks |
| `metrics/test_evidence_contract.py` | `metrics` | Policy-source binding plus manuscript evidence fail-closed controls |
| `core/test_script_entrypoints.py` | `core` | Sandboxed subprocess execution of the manuscript-metrics orchestrator |
| `metrics/test_stale_metrics_control.py` | `metrics` | Negative controls for stale generated metrics |
| `core/test_contracts.py` | `core` | Receipt schema + matrix lockstep + deterministic defaults |

Live test and coverage counts belong in the generated repository metrics, not
this inventory. All tests use real filesystem paths and imports; the project
suite introduces no prohibited mock framework.
