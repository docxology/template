# src/ - Core Business Logic

The `src/` directory contains all core business logic with 100% test coverage.

## Quick Overview

This directory is the **single source of truth** for all computational functionality. Scripts import and use these modules - they never implement algorithms themselves (thin orchestrator pattern).

## Modules

### Core
- `example.py` - Basic mathematical operations (template example)
- `glossary_gen.py` - API documentation generation
- `pdf_validator.py` - PDF rendering validation

### Data Processing
- `data_generator.py` - Synthetic data generation with configurable distributions
- `data_processing.py` - Data cleaning, preprocessing, normalization, outlier detection
- `statistics.py` - Descriptive statistics, hypothesis testing, correlation analysis
- `metrics.py` - Performance metrics, convergence metrics, quality metrics
- `validation.py` - Result validation, reproducibility verification, anomaly detection

### Visualization & Figure Management
- `visualization.py` - Publication-quality figure generation with consistent styling
- `plots.py` - Plot type implementations (line, scatter, bar, heatmap, contour)
- `figure_manager.py` - Automatic figure numbering, caption generation, cross-referencing
- `image_manager.py` - Automatic image insertion into markdown, caption management
- `markdown_integration.py` - LaTeX figure block generation, section detection, reference insertion

### Simulation & Analysis
- `simulation.py` - Core simulation framework with reproducibility and checkpointing
- `parameters.py` - Parameter set management, validation, sweeps, serialization
- `performance.py` - Convergence analysis, scalability metrics, benchmark comparisons
- `reporting.py` - Automated report generation from simulation results

### Advanced
- `build_verifier.py` - Build artifact verification and validation
- `integrity.py` - Output integrity checking and cross-references
- `quality_checker.py` - Document quality analysis and metrics
- `reproducibility.py` - Environment tracking and build manifests
- `publishing.py` - Academic publishing workflow assistance
- `scientific_dev.py` - Scientific computing best practices

## Usage

### From Scripts
```python
# Add src/ to path first
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Then import
from example import add_numbers, calculate_average
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats
from visualization import VisualizationEngine
```

### From Tests
```python
# Path already configured in conftest.py
from example import add_numbers
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats
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




