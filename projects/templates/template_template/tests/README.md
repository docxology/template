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


The platform SDK pinned in this project's package metadata and lock is selected from the prepared Python environment before the exact own package namespace is registered. Neither own `src/` nor an inferred Root SOURCE DATA directory is added to global import paths. Invoke standalone tests from the own project using `python -I -m pytest tests/ --cov=src --cov-fail-under=90` after preparing the declared SDK and own development dependencies.

Repository-wide deck facts, manuscript metrics, and architecture counts additionally consume the complete public Root SOURCE DATA. Those real cases remain required. A platform wheel does not supply Root tests, manuscripts, or the complete exemplar roster. Current local source locators support genuine checkout inputs; final standalone DATA acceptance additionally requires the harness's independently admitted clean candidate commit, complete tracked public inventory and expected fingerprint, with before/after source checks. Locator success alone is not that acceptance. No source DATA directory becomes SDK authority, and no checkout files are fabricated in site-packages.
