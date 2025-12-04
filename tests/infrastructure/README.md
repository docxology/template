# tests/infrastructure/ - Infrastructure Module Tests

Comprehensive test suite for reusable infrastructure modules (49%+ coverage required).

## Quick Start

### Run All Infrastructure Tests

```bash
# With coverage report
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html

# Require 49% coverage
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=49

# Skip network-dependent tests
pytest tests/infrastructure/ -m "not requires_ollama"
```

### Run Module-Specific Tests

```bash
# Core utilities
pytest tests/infrastructure/core/ -v

# Literature search
pytest tests/infrastructure/literature/ -v

# Validation system
pytest tests/infrastructure/validation/ -v
```

## Coverage Requirements

- **49% minimum** for infrastructure modules
- Currently achieving **55.89%** coverage
- Network-dependent tests can be skipped

## Test Categories

### Core Infrastructure
- `core/` - Configuration, logging, exceptions
- `build/` - Build verification and quality checking
- `documentation/` - Figure and API documentation management

### Research Tools
- `literature/` - Academic literature search and management
- `llm/` - Local LLM integration for research assistance
- `rendering/` - Multi-format document rendering

### Publishing & Validation
- `publishing/` - Academic publishing workflows
- `validation/` - Quality assurance and validation
- `scientific/` - Scientific computing utilities

## Testing Philosophy

- **Real implementations** - no mocks, actual functionality
- **Network-optional** - core logic testable without external services
- **Integration validation** - end-to-end workflow testing

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Module overview


