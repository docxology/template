# AGENTS: `tests/` — Template Project Test Suite

Technical specification for the template project test infrastructure.

## Test Inventory

| File | Test Count | Coverage Target |
|------|-----------:|-----------------|
| `test_meta.py` | 49 tests | 90%+ on `introspection.py`, `inject_metrics.py` |
| `test_metrics.py` | 10 tests | `metrics.py` helpers and integration sanity |
| `test_architecture_viz.py` | 6 tests | `architecture_viz.py` matrix/data and PNG generation |
| **Total** | **65 tests** | |

## Test Classes (`test_meta.py`)

| Class | Tests | What It Validates |
|-------|------:|-------------------|
| `TestDiscoverInfrastructureModules` | 8 | Module discovery, sorting, `__init__.py` presence |
| `TestDiscoverProjects` | 7 | Project workspace detection, config loading |
| `TestCountPipelineStages` | 7 | Stage enumeration, sequential numbering |
| `TestAnalyzeCoverageConfig` | 5 | Config parsing, threshold extraction |
| `TestBuildInfrastructureReport` | 9 | Aggregated report, computed properties |
| `TestInjectMetrics` | 13 | `load_metrics`, `render_chapter`, `render_all_chapters`, round-trip |

## Additional Test Modules

- `test_metrics.py`: verifies count helpers (`count_test_functions`, `count_docs_markdown_files`), `format_count`, `build_module_inventory_table`, and real-repo metric dictionary shape.
- `test_architecture_viz.py`: verifies comparative matrix invariants (shape, value range, label count) and PNG file generation for all 4 figures.

## Patterns

- **Zero-Mock**: All tests run against the real repository filesystem
- **`REPO_ROOT`**: Computed as `Path(__file__).parent.parent.parent.parent` (4 levels up)
- **`PROJECT_DIR`**: Template project root (`Path(__file__).parent.parent`)
- **Assertions**: Minimum-count checks (≥8 modules, ≥2 projects, ≥5 stages) for forward compatibility
