# Two-Layer Architecture Guide

## Overview

This research template implements a clear two-layer architecture separating generic build infrastructure from project-specific scientific content. This document explains the architecture, design rationale, and how to work within this structure.

## Architecture Layers

### Layer 1: Infrastructure (Generic Build & Validation Tools)

**Location:** `src/infrastructure/`, `repo_utilities/`

**Purpose:** Reusable tools and utilities that apply to any research project using this template. These handle:
- Build orchestration and PDF generation
- Document validation and quality checking
- Build artifact verification
- Environment reproducibility tracking
- Academic publishing assistance
- Figure and image management
- Markdown integration

**Modules:**
```
src/infrastructure/
├── build_verifier.py          # Build process verification
├── integrity.py               # File and cross-reference integrity
├── quality_checker.py         # Document quality metrics
├── reproducibility.py         # Build reproducibility tracking
├── publishing.py              # Academic publishing tools
├── pdf_validator.py           # PDF rendering quality
├── glossary_gen.py            # API documentation generation
├── markdown_integration.py     # Markdown figure integration
├── figure_manager.py          # Figure numbering and references
└── image_manager.py           # Image file management
```

**Key Characteristics:**
- Generic and reusable across projects
- Handles template infrastructure concerns
- 100% test coverage required
- No domain-specific logic
- Interfaces with project files (manuscript/, output/)

**Usage Pattern:**
```python
# Infrastructure usage from scripts
from infrastructure.figure_manager import FigureManager
from infrastructure.markdown_integration import MarkdownIntegration

# These manage the document structure, not the science
fm = FigureManager()
fm.register_figure("convergence_plot.png", label="fig:convergence")
```

---

### Layer 2: Scientific (Project-Specific Algorithms & Analysis)

**Location:** `src/scientific/`, `scripts/`

**Purpose:** Domain-specific code implementing the research project's scientific algorithms, data processing, analysis, and visualization.

**Modules:**
```
src/scientific/
├── example.py                 # Basic operations (template example)
├── simulation.py              # Scientific simulation framework
├── statistics.py              # Statistical analysis
├── data_generator.py          # Synthetic data generation
├── data_processing.py         # Data preprocessing and cleaning
├── metrics.py                 # Performance metrics
├── parameters.py              # Parameter management
├── performance.py             # Convergence and scalability analysis
├── plots.py                   # Plot implementations
├── reporting.py               # Report generation
├── validation.py              # Result validation
└── visualization.py           # Visualization engine
```

**Scripts (thin orchestrators):**
```
scripts/
├── example_figure.py              # Basic figure generation
├── generate_research_figures.py   # Complex figures
├── analysis_pipeline.py           # Analysis workflow
├── scientific_simulation.py       # Simulation execution
└── generate_scientific_figures.py # Automated figure generation
```

**Key Characteristics:**
- Domain-specific and research-focused
- Implements algorithms and computations
- Calls infrastructure when needed
- 100% test coverage required
- Follows thin orchestrator pattern

**Usage Pattern:**
```python
# Scientific usage from scripts
from scientific.simulation import SimpleSimulation
from scientific.statistics import calculate_descriptive_stats
from infrastructure.figure_manager import FigureManager

# Science: Run simulation and analysis
sim = SimpleSimulation()
results = sim.run()
stats = calculate_descriptive_stats(results)

# Infrastructure: Manage figures
fm = FigureManager()
fm.register_figure("results.png", label="fig:results")
```

---

## Layer Separation

### Architectural Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                  LAYER 1: INFRASTRUCTURE                │
│  (Build orchestration, validation, document management) │
│                                                         │
│  ┌──────────────────┬────────────────────────────────┐ │
│  │ run_all.py       │ scripts/*.py                   │ │
│  │ (6-stage)        │ - 00_setup_environment.py   │ │
│  │                  │ - 01_run_tests.py            │ │
│  │                  │ - validate_pdf_output.py      │ │
│  └──────────────────┴────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  src/infrastructure/                            │ │
│  │  - build_verifier, integrity, quality_checker   │ │
│  │  - reproducibility, publishing, pdf_validator   │ │
│  │  - glossary_gen, markdown_integration           │ │
│  │  - figure_manager, image_manager                │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                                      │
         │ Manages structure and               │ Validates
         │ validates outputs                   │ science
         ▼                                      ▼
┌─────────────────────────────────────────────────────────┐
│                  LAYER 2: SCIENTIFIC                    │
│     (Algorithms, analysis, visualization, data)         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  src/scientific/                                │ │
│  │  - simulation, statistics, data_processing      │ │
│  │  - metrics, parameters, performance             │ │
│  │  - plots, reporting, validation, visualization  │ │
│  │  - data_generator, example                      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  scripts/ (thin orchestrators)                  │ │
│  │  - example_figure.py                            │ │
│  │  - generate_research_figures.py                 │ │
│  │  - analysis_pipeline.py                         │ │
│  │  - scientific_simulation.py                     │ │
│  │  - generate_scientific_figures.py               │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  Generates figures, data, and analysis output           │
└─────────────────────────────────────────────────────────┘
         │                                      
         │ Input: Manuscripts, configurations  
         │ Output: Figures, data, reports     
         ▼
┌─────────────────────────────────────────────────────────┐
│  manuscript/ (research content)                         │
│  01_abstract.md through 99_references.md                │
└─────────────────────────────────────────────────────────┘
```

### Import Guidelines

**✅ Layer 1 → Layer 1:** Infrastructure modules can import from other infrastructure modules
```python
from infrastructure.figure_manager import FigureManager
from infrastructure.image_manager import ImageManager
```

**✅ Layer 2 → Layer 1:** Scientific code can import infrastructure
```python
from scientific.visualization import plot_results
from infrastructure.figure_manager import FigureManager

# Use infrastructure for figure management
fig = plot_results(data)
fm = FigureManager()
fm.register_figure(fig, label="fig:results")
```

**✅ Layer 2 → Layer 2:** Scientific modules can import from other scientific modules
```python
from scientific.simulation import SimpleSimulation
from scientific.statistics import calculate_descriptive_stats
```

**❌ Layer 1 → Layer 2:** Infrastructure should NOT import scientific code
```python
# BAD: Build tools shouldn't depend on science
from infrastructure.build_verifier import verify_build_artifacts
from scientific.simulation import SimpleSimulation  # ❌ WRONG

# This breaks the abstraction and makes infrastructure project-specific
```

---

## Code Organization

### src/ Structure

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
    ├── statistics.py
    ├── data_generator.py
    ├── data_processing.py
    ├── metrics.py
    ├── parameters.py
    ├── performance.py
    ├── plots.py
    ├── reporting.py
    ├── validation.py
    └── visualization.py
```

### tests/ Structure

```
tests/
├── conftest.py                # Test configuration
├── infrastructure/            # Infrastructure layer tests
│   ├── __init__.py
│   ├── test_build_verifier.py
│   ├── test_integrity.py
│   ├── test_quality_checker.py
│   ├── test_reproducibility.py
│   ├── test_publishing.py
│   ├── test_pdf_validator.py
│   └── ...
├── scientific/                # Scientific layer tests
│   ├── __init__.py
│   ├── test_example.py
│   ├── test_simulation.py
│   ├── test_statistics.py
│   ├── test_data_generator.py
│   └── ...
└── integration/               # Cross-layer tests
    ├── __init__.py
    ├── test_integration_pipeline.py
    ├── test_example_figure.py
    └── test_generate_research_figures.py
```

---

## Execution Flow

### Build Pipeline - Layer Transitions

```
User runs: python3 scripts/run_all.py
    │
    ▼
┌─────────────────────────────────────────────┐
│ STAGE 0: LAYER 1 - Setup Environment        │
│ - Validate Python, dependencies            │
│ - Check build tools                        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ PHASE 1: LAYER 1 - Test Validation          │
│ - Run tests/infrastructure/*.py             │
│ - Run tests/scientific/*.py                 │
│ - Run tests/integration/*.py                │
│ - Validate 95%+ coverage                    │
│ - Report: [LAYER-1-INFRASTRUCTURE] Running  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ PHASE 2: LAYER 2 - Scientific Execution     │
│ - Run scripts/*.py                          │
│ - Generate figures                          │
│ - Process data                              │
│ - Create outputs                            │
│ - Report: [LAYER-2-SCIENTIFIC] Running      │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ PHASE 2.5: LAYER 1 - Utilities              │
│ - Generate API glossary                     │
│ - Validate markdown                         │
│ - Check cross-references                    │
│ - Report: [LAYER-1-INFRASTRUCTURE] Running  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ PHASE 3-5: LAYER 1 - Document Generation    │
│ - Generate LaTeX preamble                   │
│ - Build individual PDFs                     │
│ - Build combined PDF                        │
│ - Create HTML version                       │
│ - Report: [LAYER-1-INFRASTRUCTURE] Building │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ PHASE 6: LAYER 1 - Validation               │
│ - Validate PDF quality                      │
│ - Check for rendering issues                │
│ - Report: [LAYER-1-INFRASTRUCTURE] Done     │
└─────────────────────────────────────────────┘
    │
    ▼
Success: All PDFs generated, all layers working
```

### Logging Output Example

```
━━━ LAYER 1: Infrastructure Validation ━━━
[2025-11-21 09:31:20] [INFO] Running tests (infrastructure + scientific)
...tests output...
[2025-11-21 09:31:58] [INFO] ✅ All tests passed with adequate coverage

━━━ LAYER 2: Scientific Computation ━━━
[2025-11-21 09:31:58] [INFO] Executing scientific scripts...
[2025-11-21 09:31:58] [INFO] [LAYER-2-SCIENTIFIC] Starting analysis pipeline...
...script output...
[2025-11-21 09:32:01] [INFO] ✅ ALL project scripts executed successfully

━━━ LAYER 1: Infrastructure Validation ━━━
[2025-11-21 09:32:01] [INFO] Running repository utilities (glossary + markdown validation)
...validation output...
[2025-11-21 09:32:02] [INFO] ✅ Repository utilities completed

━━━ LAYER 1: Document Generation ━━━
[2025-11-21 09:32:02] [INFO] Step 3: Generating LaTeX preamble from markdown...
[2025-11-21 09:32:02] [INFO] Step 4: Discovering and building ALL markdown modules...
...PDF generation output...
[2025-11-21 09:33:06] [INFO] ✅ Combined document built successfully
```

---

## Adding New Code

### Decision Tree: Where Should Code Go?

```
┌─ Is this specific to our research project?
│  ├─ YES → Layer 2 (scientific/)
│  └─ NO  ─┐
│          └─ Is it about building/validating?
│             ├─ YES → Layer 1 (infrastructure/)
│             └─ NO  → Reconsider scope
│
├─ Examples that belong in Layer 2:
│  ├─ Simulation algorithms
│  ├─ Statistical analysis specific to our problem
│  ├─ Custom visualization for our data
│  ├─ Parameter sweeps for our experiment
│  └─ Domain-specific data processing
│
├─ Examples that belong in Layer 1:
│  ├─ PDF generation logic
│  ├─ Figure management and numbering
│  ├─ Document validation
│  ├─ Build artifact verification
│  ├─ Generic data processing utilities
│  └─ Cross-project templates
│
└─ Is your code reusable across projects?
   ├─ YES → Layer 1 (infrastructure/)
   └─ NO  → Layer 2 (scientific/)
```

### Adding a New Scientific Module

1. **Create the module:**
   ```bash
   vim src/scientific/new_algorithm.py
   ```

2. **Implement with type hints and docstrings:**
   ```python
   """New algorithm implementation."""
   from typing import List, Optional
   
   def analyze_data(data: List[float]) -> Optional[float]:
       """Analyze data.
       
       Args:
           data: Input data
           
       Returns:
           Analysis result
       """
       pass
   ```

3. **Write comprehensive tests:**
   ```bash
   vim tests/scientific/test_new_algorithm.py
   ```

4. **Add to scientific/__init__.py:**
   ```python
   from .new_algorithm import analyze_data
   ```

5. **Use in scripts:**
   ```python
   from scientific.new_algorithm import analyze_data
   ```

6. **Update documentation:**
   - Add to src/scientific/AGENTS.md
   - Add to src/scientific/README.md

### Adding a New Infrastructure Module

1. **Create the module:**
   ```bash
   vim src/infrastructure/new_validator.py
   ```

2. **Implement generic, project-independent logic:**
   ```python
   """New validation tool."""
   
   def validate_output_structure(output_dir: str) -> bool:
       """Validate output directory structure."""
       pass
   ```

3. **Write comprehensive tests:**
   ```bash
   vim tests/infrastructure/test_new_validator.py
   ```

4. **Document usage:**
   - Add to src/infrastructure/AGENTS.md
   - Include usage examples

5. **Integrate with build pipeline:**
   - Update scripts/run_all.py if needed
   - Update repo_utilities/ if applicable

---

## Testing Strategy

### Infrastructure Tests (tests/infrastructure/)

- Verify build orchestration works
- Test validation logic
- Check file integrity checking
- Validate PDF generation
- No dependency on scientific code

**Command:**
```bash
pytest tests/infrastructure/ --cov=src/infrastructure
```

### Scientific Tests (tests/scientific/)

- Test algorithms correctness
- Verify statistical computations
- Check data processing
- Validate visualization output
- No dependency on build infrastructure

**Command:**
```bash
pytest tests/scientific/ --cov=src/scientific
```

### Integration Tests (tests/integration/)

- End-to-end pipeline validation
- Script execution testing
- Layer interaction verification
- Output completeness checking

**Command:**
```bash
pytest tests/integration/ --cov=src
```

### Full Test Suite

```bash
# All tests with coverage
pytest tests/ --cov=src --cov-fail-under=95

# Generate coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Best Practices

### For Infrastructure Development

✅ **Do:**
- Write generic, reusable code
- Document with project-independent examples
- Test extensively with real scenarios
- Handle errors gracefully
- Provide clear logging

❌ **Don't:**
- Import scientific modules
- Assume specific research domain
- Skip tests to ship features
- Hardcode project-specific values
- Mix concerns (building vs. computation)

### For Scientific Development

✅ **Do:**
- Use infrastructure tools for document management
- Follow thin orchestrator pattern in scripts
- Implement algorithms in src/ modules
- Test with real data
- Document domain-specific concepts

❌ **Don't:**
- Duplicate build/validation logic
- Implement document generation in scripts
- Skip layer abstraction
- Mix orchestration with computation
- Depend on infrastructure internals

### Logging Best Practices

```python
# In scientific scripts - mark layer transitions
import logging
logger = logging.getLogger(__name__)

logger.info("[LAYER-2-SCIENTIFIC] Starting simulation...")
logger.info("[LAYER-1-INFRASTRUCTURE] Using FigureManager for output...")
```

```bash
# In build scripts - mark phase transitions
log_info "━━━ LAYER 1: Infrastructure Validation ━━━"
log_info "━━━ LAYER 2: Scientific Computation ━━━"
```

---

## Migration from Flat Structure

If you have an old project with flat src/, migrating to the two-layer structure:

1. **Create packages:**
   ```bash
   mkdir -p src/infrastructure src/scientific
   ```

2. **Move modules:**
   - Infrastructure modules → src/infrastructure/
   - Scientific modules → src/scientific/

3. **Update imports:**
   - `from example import` → `from scientific.example import`
   - `from build_verifier import` → `from infrastructure.build import`

4. **Update tests:**
   - Organize tests/ with infrastructure/ and scientific/ subdirectories
   - Update conftest.py if needed

5. **Validate:**
   ```bash
   pytest tests/ --cov=src --cov-fail-under=95
   python3 scripts/run_all.py
   ```

---

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'scientific'`

**Solution:** Ensure tests/conftest.py includes src/ on path:
```python
import sys
sys.path.insert(0, os.path.join(repo_root, "src"))
```

### Layer Violations

**Error:** Infrastructure module imports from scientific

**Solution:** Refactor to remove dependency or move code to appropriate layer

**Check:**
```bash
# Find infrastructure imports of scientific
grep -r "from scientific import" src/infrastructure/
grep -r "import scientific" src/infrastructure/
```

### Mixed Concerns

**Error:** Build logic in scientific module

**Solution:** Move to infrastructure layer or extract into separate module

---

## References

- [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md) - Current state analysis
- [DECISION_TREE.md](DECISION_TREE.md) - Code placement flowchart
- [src/infrastructure/AGENTS.md](../src/infrastructure/AGENTS.md) - Infrastructure docs
- [src/scientific/AGENTS.md](../src/scientific/AGENTS.md) - Scientific docs
- [../AGENTS.md](../AGENTS.md) - Complete system documentation

---

## Key Takeaway

**Layers separate concerns:**
- **Layer 1** handles *how* research is documented and built
- **Layer 2** focuses on *what* research is conducted

This separation makes code more modular, reusable, and maintainable.



