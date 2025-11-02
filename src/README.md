# src/ - Core Business Logic

The `src/` directory contains all core business logic with 100% test coverage.

## Quick Overview

This directory is the **single source of truth** for all computational functionality. Scripts import and use these modules - they never implement algorithms themselves (thin orchestrator pattern).

## Modules

### Core
- `example.py` - Basic mathematical operations (template example)
- `glossary_gen.py` - API documentation generation
- `pdf_validator.py` - PDF rendering validation

### Advanced
- `build_verifier.py` - Build artifact verification (1036 lines)
- `integrity.py` - Output integrity checking (753 lines)
- `quality_checker.py` - Document quality analysis (624 lines)
- `reproducibility.py` - Environment tracking (758 lines)
- `publishing.py` - Academic publishing tools (872 lines)
- `scientific_dev.py` - Scientific computing practices (978 lines)

## Usage

### From Scripts
```python
# Add src/ to path first
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Then import
from example import add_numbers, calculate_average
```

### From Tests
```python
# Path already configured in conftest.py
from example import add_numbers
```

## Requirements

- **100% test coverage** required for all modules
- Type hints on all public APIs
- Comprehensive docstrings
- Real data testing (no mocks)

## Testing

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Or with uv
uv run pytest tests/ --cov=src --cov-report=html
```

## Adding a Module

1. Create `src/new_module.py` with type hints and docs
2. Add tests in `tests/test_new_module.py`
3. Ensure 100% coverage
4. Update this README
5. Run full test suite

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) - Testing guide
- [`../scripts/README.md`](../scripts/README.md) - How scripts use src/

