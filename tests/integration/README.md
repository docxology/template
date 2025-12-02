# tests/integration/ - Integration Test Suite

Cross-module integration tests validating complete system workflows.

## Quick Start

### Run Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# With verbose output
pytest tests/integration/ -vs
```

## Test Coverage

- `test_module_interoperability.py` - Cross-module functionality validation
- `test_output_copying.py` - File handling and output management

## Purpose

Integration tests validate that multiple components work together correctly, including:

- Module interactions and data flow
- File I/O coordination
- End-to-end workflow completion
- Error handling across boundaries

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../../tests/README.md`](../../tests/README.md) - Test suite overview
