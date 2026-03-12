# AGENTS: `tests/` — Template Project Test Suite

Technical specification for the template project test infrastructure.

## Test Inventory

| File | Test Count | Coverage Target |
|------|-----------|-----------------|
| `test_meta.py` | 39 tests | 90%+ on `introspection.py` |

## Test Classes

| Class | Tests | What It Validates |
|-------|-------|-------------------|
| `TestDiscoverInfrastructureModules` | 8 | Module discovery, sorting, `__init__.py` presence |
| `TestDiscoverProjects` | 7 | Project workspace detection, config loading |
| `TestCountPipelineStages` | 7 | Stage enumeration, sequential numbering |
| `TestAnalyzeCoverageConfig` | 5 | Config parsing, threshold extraction |
| `TestBuildInfrastructureReport` | 9 | Aggregated report, computed properties |

## Patterns

- **Zero-Mock**: All tests run against the real repository filesystem
- **`REPO_ROOT`**: Computed as `Path(__file__).parent.parent.parent.parent` (4 levels up)
- **`PROJECT_DIR`**: Template project root (`Path(__file__).parent.parent`)
- **Assertions**: Minimum-count checks (≥8 modules, ≥3 projects, ≥5 stages) for forward compatibility
