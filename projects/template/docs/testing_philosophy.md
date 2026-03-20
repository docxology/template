# Testing Philosophy — Template Meta-Project

## Zero-Mock Policy

This project follows the repository-wide Zero-Mock testing standard. No `unittest.mock`, `MagicMock`, `@patch`, or any mocking framework is used anywhere. All tests exercise real code paths against real data.

### What This Means in Practice

```python
# ✅ CORRECT: Real filesystem, real computation
def test_build_infrastructure_report(repo_root):
    report = build_infrastructure_report(repo_root)
    assert report.module_count >= 10        # checks real disk
    assert report.total_python_files > 500  # counts real files

# ❌ PROHIBITED: Mock objects substitute assumptions for reality
def test_build_report_mocked():
    with patch('template.introspection.Path.rglob') as mock_rglob:
        mock_rglob.return_value = [Path('a.py'), Path('b.py')]
        report = build_infrastructure_report(Path('.'))
        assert report.total_python_files == 2  # tests the mock, not the code
```

### Why This Matters for a Self-Referential Project

The template project's tests are particularly sensitive to mocking because they validate claims that appear in the published manuscript. A mocked test that asserts `module_count == 12` passes regardless of whether the infrastructure actually has 12 modules. A real test fails immediately when the infrastructure changes — which is exactly the alert we need to update the manuscript.

## Test Categories

### `test_meta.py` — Introspection + Integration

Tests that the `build_infrastructure_report()` function correctly:

- Discovers all infrastructure subpackages on disk
- Counts Python files in each module
- Identifies active projects in `projects/`
- Enumerates pipeline stages
- Excludes `.venv`, `__pycache__`, `.git` from counts

### `test_architecture_viz.py` — Figure Generation

Tests that architecture visualization functions:

- Produce valid PNG files
- Generate files with non-zero size
- Handle edge cases (empty modules, single project)

### `test_metrics.py` — Metric Formatting

Tests for formatting utilities:

- `format_count()` produces human-readable numbers
- `build_module_inventory_table()` generates valid Markdown tables
- `build_manuscript_metrics_dict()` returns all expected keys

## Coverage Target

- **Project source**: 90%+ coverage for `projects/template/src/`
- **Enforcement**: The pipeline halts at Stage 01 if coverage drops below threshold
- **Current**: 65 tests, all passing

## Running Tests

```bash
# Quick run
PYTHONPATH=. uv run pytest projects/template/tests/ -v --tb=short

# With coverage
PYTHONPATH=. uv run pytest projects/template/tests/ -v --tb=short \
  --cov=projects/template/src --cov-report=term-missing

# Single test file
PYTHONPATH=. uv run pytest projects/template/tests/test_meta.py -v
```

## Adding New Tests

1. Create `test_<module>.py` in `projects/template/tests/`
2. Import from `template.<module>` (the `src/` is on `PYTHONPATH` via conftest)
3. Use real data — no mocks, no fakes, no stubs
4. Assert against real repository state
5. Update `docs/VERIFICATION.md` test count if changed
