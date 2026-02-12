# tests/infra_tests/ - Infrastructure Module Tests

test suite for reusable infrastructure modules (60%+ coverage required).

## Quick Start

### Run All Infrastructure Tests

```bash
# With coverage report
pytest tests/infra_tests/ --cov=infrastructure --cov-report=html

# Require 60% coverage
pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Skip network-dependent tests
pytest tests/infra_tests/ -m "not requires_ollama"
```

### Run Module-Specific Tests

```bash
# Core utilities
pytest tests/infra_tests/core/ -v

# Reporting
pytest tests/infra_tests/reporting/ -v

# Validation system
pytest tests/infra_tests/validation/ -v
```

## Coverage Requirements

- **60% minimum** for infrastructure modules
- Currently achieving **83.33%** coverage (exceeds requirement by 39%!)
- Network-dependent tests can be skipped
- See test coverage reports for detailed analysis

## Test Categories

### Core Infrastructure

- `core/` - Configuration, logging, exceptions, file operations, credentials, security
- `documentation/` - Figure and API documentation management
- `project/` - Project discovery and orchestration

### Research Tools

- `llm/` - Local LLM integration for research assistance
- `rendering/` - Multi-format document rendering
- `scientific/` - Scientific computing utilities

### Publishing & Validation

- `publishing/` - Academic publishing workflows
- `validation/` - Quality assurance and validation
- `reporting/` - Pipeline reporting and error aggregation

## Testing Philosophy

- **Real implementations** - no mocks, actual functionality
- **Network-optional** - core logic testable without external services
- **Integration validation** - end-to-end workflow testing

## See Also

- [`AGENTS.md`](AGENTS.md) - documentation
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Module overview
