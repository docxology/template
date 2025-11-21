# src/ - Two-Layer Architecture

## Purpose

The `src/` directory contains **all core business logic** organized into two distinct layers:
- **Layer 1: Infrastructure** - Generic build, validation, and document management tools
- **Layer 2: Scientific** - Project-specific algorithms, analysis, and visualization

## Architectural Organization

### Layer 1: Infrastructure (`src/infrastructure/`)

**Reusable build and validation tools** applicable to any research project using this template.

**Modules:**
```
infrastructure/
├── build_verifier.py          # Build artifact verification
├── integrity.py               # Integrity checking
├── quality_checker.py         # Document quality analysis
├── reproducibility.py         # Reproducibility tracking
├── publishing.py              # Academic publishing support
├── pdf_validator.py           # PDF validation
├── glossary_gen.py            # API documentation
├── markdown_integration.py     # Markdown figure integration
├── figure_manager.py          # Figure numbering/management
└── image_manager.py           # Image file management
```

**Key Characteristics:**
- Generic and reusable
- Project-independent
- No domain-specific logic
- 100% test coverage

**See:** [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md)

### Layer 2: Scientific (`src/scientific/`)

**Project-specific scientific code** implementing algorithms, analysis, and visualization.

**Modules:**
```
scientific/
├── example.py                 # Template example
├── simulation.py              # Simulation framework
├── parameters.py              # Parameter management
├── data_generator.py          # Synthetic data generation
├── data_processing.py         # Data preprocessing
├── statistics.py              # Statistical analysis
├── metrics.py                 # Performance metrics
├── performance.py             # Convergence analysis
├── validation.py              # Result validation
├── visualization.py           # Figure generation
├── plots.py                   # Plot implementations
└── reporting.py               # Report generation
```

**Key Characteristics:**
- Domain-specific
- Project-unique
- Implements algorithms
- 100% test coverage

**See:** [`scientific/AGENTS.md`](scientific/AGENTS.md)

## Architecture Diagram

```
┌─────────────────────────────────────┐
│    LAYER 1: INFRASTRUCTURE          │
│  (Generic build & validation tools) │
│                                     │
│  build_verifier, integrity,         │
│  quality_checker, reproducibility,  │
│  publishing, pdf_validator,         │
│  glossary_gen, markdown_integration,│
│  figure_manager, image_manager      │
└─────────────────────────────────────┘
         ▲                        
         │ (uses)                 
         │                        
┌─────────────────────────────────────┐
│    LAYER 2: SCIENTIFIC              │
│  (Project-specific algorithms)      │
│                                     │
│  example, simulation, parameters,   │
│  data_generator, data_processing,   │
│  statistics, metrics, performance,  │
│  validation, visualization, plots,  │
│  reporting                          │
└─────────────────────────────────────┘
```

## Thin Orchestrator Pattern

**Layer 1** infrastructure is used by **Layer 2** scientific code via scripts:

```
┌──────────────────┐
│   src/scientific │  Layer 2 modules
│   (computation)  │  (what we compute)
└────────┬─────────┘
         │ (uses)
         ▼
┌──────────────────────┐
│src/infrastructure    │  Layer 1 modules  
│(build & validation)  │  (how we build it)
└──────────────────────┘
```

## Import Guidelines

### ✅ Allowed

```python
# Infrastructure can import from infrastructure
from infrastructure.figure_manager import FigureManager
from infrastructure.integrity import verify_file_integrity

# Scientific can import from scientific
from scientific.simulation import SimpleSimulation
from scientific.statistics import calculate_descriptive_stats

# Scientific can import from infrastructure
from infrastructure.figure_manager import FigureManager
from scientific.visualization import plot_results
```

### ❌ Not Allowed

```python
# Infrastructure must NOT import from scientific
from infrastructure.build_verifier import verify_artifacts
from scientific.simulation import SimpleSimulation  # ❌ VIOLATION
```

**Reason:** Breaks abstraction, makes infrastructure project-specific

## Module Organization

```
src/
├── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── AGENTS.md              # Infrastructure documentation
│   ├── README.md              # Quick reference
│   ├── build_verifier.py
│   ├── integrity.py
│   ├── quality_checker.py
│   ├── reproducibility.py
│   ├── publishing.py
│   ├── pdf_validator.py
│   ├── glossary_gen.py
│   ├── markdown_integration.py
│   ├── figure_manager.py
│   └── image_manager.py
└── scientific/
    ├── __init__.py
    ├── AGENTS.md              # Scientific documentation
    ├── README.md              # Quick reference
    ├── example.py
    ├── simulation.py
    ├── parameters.py
    ├── data_generator.py
    ├── data_processing.py
    ├── statistics.py
    ├── metrics.py
    ├── performance.py
    ├── validation.py
    ├── visualization.py
    ├── plots.py
    └── reporting.py
```

## Test Organization

Tests mirror code organization:

```
tests/
├── conftest.py                # Global configuration
├── infrastructure/            # Test Layer 1
│   ├── test_build_verifier.py
│   ├── test_integrity.py
│   ├── test_quality_checker.py
│   ├── ...
├── scientific/                # Test Layer 2
│   ├── test_example.py
│   ├── test_simulation.py
│   ├── test_statistics.py
│   ├── ...
└── integration/               # Cross-layer tests
    ├── test_integration_pipeline.py
    ├── test_example_figure.py
    └── ...
```

## Usage Patterns

### From Scripts (Orchestration)

```python
# scripts/analysis_pipeline.py
from scientific.data_generator import generate_synthetic_data
from scientific.statistics import calculate_descriptive_stats
from infrastructure.figure_manager import FigureManager

# Layer 2: Generate and analyze data
data = generate_synthetic_data(n_samples=1000)
stats = calculate_descriptive_stats(data)

# Layer 1: Manage figures
fm = FigureManager()
fm.register_figure("results.png", label="fig:results")
```

### From Scientific Code

```python
# src/scientific/analysis.py
from infrastructure.figure_manager import FigureManager
from infrastructure.markdown_integration import MarkdownIntegration

def generate_analysis_figures():
    # Scientific computation
    results = run_analysis()
    
    # Use infrastructure for document management
    fm = FigureManager()
    fm.register_figure("analysis.png", "fig:analysis")
    
    return results
```

## Requirements

### All Code

- **100% test coverage required**
- Type hints on public APIs
- Comprehensive docstrings
- Real data testing (no mocks)
- Clear error messages
- Follow PEP 8 style

### Infrastructure Modules

- Must be generic and reusable
- No domain-specific assumptions
- Project-independent logic
- Tested in `tests/infrastructure/`

### Scientific Modules

- Must be domain-specific
- Implements project algorithms
- Uses infrastructure tools when needed
- Tested in `tests/scientific/`

## Adding New Modules

### Decision Tree

```
New code to write?
│
├─ Is it build/validation infrastructure?
│  └─ YES → Add to src/infrastructure/
│
└─ Is it project-specific science?
   └─ YES → Add to src/scientific/
```

**For Infrastructure:**
1. Create in `src/infrastructure/`
2. Add tests to `tests/infrastructure/`
3. Document in `infrastructure/AGENTS.md`
4. Update `infrastructure/__init__.py`

**For Scientific:**
1. Create in `src/scientific/`
2. Add tests to `tests/scientific/`
3. Document in `scientific/AGENTS.md`
4. Update `scientific/__init__.py`

## Testing

```bash
# Test infrastructure layer
pytest tests/infrastructure/ --cov=src/infrastructure

# Test scientific layer
pytest tests/scientific/ --cov=src/scientific

# Test integration between layers
pytest tests/integration/ --cov=src

# All tests with coverage
pytest tests/ --cov=src --cov-fail-under=95
```

## Best Practices

### Infrastructure Development

✅ **Do:**
- Write generic, reusable code
- Test extensively
- Document non-domain-specific concepts
- Consider extensibility

❌ **Don't:**
- Import scientific code
- Assume research domain
- Skip tests
- Mix concerns

### Scientific Development

✅ **Do:**
- Use infrastructure tools
- Follow thin orchestrator pattern
- Implement domain-specific logic
- Document domain context

❌ **Don't:**
- Duplicate infrastructure functionality
- Implement document generation
- Skip tests
- Violate layer boundaries

## Layer Separation Benefits

✅ **Modularity** - Each layer has clear responsibility  
✅ **Reusability** - Infrastructure applies across projects  
✅ **Testability** - Layers can be tested independently  
✅ **Maintainability** - Clear code organization  
✅ **Clarity** - Purpose of each module obvious  

## References

- [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md) - Infrastructure layer documentation
- [`scientific/AGENTS.md`](scientific/AGENTS.md) - Scientific layer documentation
- [`../docs/TWO_LAYER_ARCHITECTURE.md`](../docs/TWO_LAYER_ARCHITECTURE.md) - Architecture overview
- [`../docs/DECISION_TREE.md`](../docs/DECISION_TREE.md) - Code placement guide
- [`../docs/ARCHITECTURE_ANALYSIS.md`](../docs/ARCHITECTURE_ANALYSIS.md) - Current state analysis
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation

## Key Takeaway

**Two layers, clear separation:**
- **Layer 1** handles *how* research is built and validated
- **Layer 2** focuses on *what* research is conducted

This structure keeps code organized, testable, and maintainable.
