# src/ - Quick Reference

Core business logic organized in two layers: infrastructure (generic build tools) and scientific (project-specific algorithms).

## Quick Overview

**src/** contains all reusable, testable business logic with 100% test coverage:

| Layer | Purpose | Coverage |
|-------|---------|----------|
| **infrastructure/** | Generic build and validation tools | 100% |
| **scientific/** | Project-specific algorithms and analysis | 100% |

## Key Files

### Infrastructure Layer
- `infrastructure/build_verifier.py` - Build verification (398 lines)
- `infrastructure/integrity.py` - Integrity checking (354 lines)
- `infrastructure/quality_checker.py` - Quality metrics (252 lines)
- `infrastructure/pdf_validator.py` - PDF validation (51 lines)
- `infrastructure/publishing.py` - Academic publishing (305 lines)
- `infrastructure/reproducibility.py` - Reproducibility tracking (264 lines)
- `infrastructure/glossary_gen.py` - API documentation (56 lines)
- `infrastructure/figure_manager.py` - Figure numbering (84 lines)
- `infrastructure/image_manager.py` - Image management (91 lines)
- `infrastructure/markdown_integration.py` - Markdown integration (85 lines)

### Scientific Layer
- `scientific/example.py` - Template examples
- `scientific/simulation.py` - Simulation framework
- `scientific/parameters.py` - Parameter management
- `scientific/data_generator.py` - Data generation
- `scientific/data_processing.py` - Data preprocessing
- `scientific/statistics.py` - Statistical analysis
- `scientific/metrics.py` - Performance metrics
- `scientific/performance.py` - Performance analysis
- `scientific/validation.py` - Result validation
- `scientific/visualization.py` - Visualization
- `scientific/plots.py` - Plot implementations
- `scientific/reporting.py` - Report generation

## Common Operations

### Running Tests
```bash
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

### Using Infrastructure Layer
```python
from infrastructure.build_verifier import verify_build_artifacts
from infrastructure.quality_checker import analyze_document_quality

# Verify build artifacts
verification = verify_build_artifacts(output_dir, expected_files)

# Check document quality
metrics = analyze_document_quality(pdf_path)
```

### Using Scientific Layer
```python
from scientific.data_generator import generate_synthetic_data
from scientific.statistics import compute_mean, compute_variance
from scientific.visualization import create_convergence_plot

# Generate data
data = generate_synthetic_data(100)

# Analyze data
mean = compute_mean(data)
variance = compute_variance(data)

# Visualize results
plot = create_convergence_plot(data)
```

## Architecture

See [AGENTS.md](AGENTS.md) for detailed documentation.

- Infrastructure layer ([infrastructure/AGENTS.md](infrastructure/AGENTS.md))
- Scientific layer ([scientific/AGENTS.md](scientific/AGENTS.md))
- Architecture overview ([../docs/TWO_LAYER_ARCHITECTURE.md](../docs/TWO_LAYER_ARCHITECTURE.md))

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete src/ documentation
- [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md) - Infrastructure layer details
- [`scientific/AGENTS.md`](scientific/AGENTS.md) - Scientific layer details
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
- [`../tests/README.md`](../tests/README.md) - Testing guide

