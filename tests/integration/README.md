# tests/integration/ - Integration Test Suite

Cross-module integration tests validating system workflows.

## Quick Start

### Run Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# With verbose output
pytest tests/integration/ -vs

# Specific test categories
pytest tests/integration/test_module_interoperability.py -v  # Cross-module tests
pytest tests/integration/test_output_copying.py -v           # File handling tests
pytest tests/integration/test_run_sh.py -v                   # Script orchestration tests
pytest tests/integration/test_executive_report_generation.py -v   # Executive reporting
pytest tests/integration/test_bash_utils.sh                  # Bash utilities (run directly)
```

## Test Coverage

### Core Integration Tests
- `test_module_interoperability.py` - Cross-module functionality validation
- `test_output_copying.py` - File handling and output management
- `test_figure_equation_citation.py` - Figure/equation/citation handling
- `test_edge_cases_and_error_paths.py` - Edge cases and error handling

### Script and Build System Tests
- `test_run_sh.py` - Script orchestration and project discovery
- `test_executive_report_generation.py` - Executive report generation (Stage 10)
- `test_logging.py` - Bash logging integration tests
- `test_bash_utils.sh` - Bash utility function validation

## Purpose

Integration tests validate that multiple components work together correctly, including:

- Module interactions and data flow
- File I/O coordination
- End-to-end workflow completion
- Error handling across boundaries

## See Also

- [`AGENTS.md`](AGENTS.md) - documentation
- [`../../tests/README.md`](../../tests/README.md) - Test suite overview
