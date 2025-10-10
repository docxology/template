# Generic Project Development Workflow: The render_pdf.sh Paradigm

This document explains the complete development workflow that ensures source code, tests, and documentation remain in perfect coherence. For related information, see **[`docs/HOW_TO_USE.md`](docs/HOW_TO_USE.md)** for complete usage guidance, **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)**, **[`docs/THIN_ORCHESTRATOR_SUMMARY.md`](docs/THIN_ORCHESTRATOR_SUMMARY.md)**, and **[`README.md`](docs/README.md)**.

## Overview

The generic project template implements a **unified test-driven development paradigm** where:

- **Source code** implements mathematical functionality
- **Tests** validate all functionality with 100% coverage
- **Scripts** are **thin orchestrators** that import and use `src/` methods
- **Documentation** references code and displays generated outputs
- **`render_pdf.sh`** orchestrates the entire pipeline

## Complete Workflow Diagram

```mermaid
graph TB
    subgraph "Development Components"
        SRC[Source Code<br/>src/]
        TESTS[Tests<br/>tests/]
        SCRIPTS[Scripts<br/>scripts/]
        MD[Documentation<br/>markdown/]
    end
    
    subgraph "Validation & Generation"
        VALIDATION[Test Validation<br/>100% Coverage]
        FIGURES[Figure Generation<br/>Using src/ methods]
        DATA[Data Generation<br/>Using src/ methods]
        MARKDOWN_VAL[Markdown Validation<br/>Images & References]
    end
    
    subgraph "Build Pipeline"
        RENDER[render_pdf.sh<br/>Orchestrator]
        PDFS[PDF Generation<br/>Individual + Combined]
        LATEX[LaTeX Export<br/>For further processing]
    end
    
    SRC --> VALIDATION
    TESTS --> VALIDATION
    SRC --> FIGURES
    SRC --> DATA
    SCRIPTS --> FIGURES
    SCRIPTS --> DATA
    MD --> MARKDOWN_VAL
    FIGURES --> MARKDOWN_VAL
    DATA --> MARKDOWN_VAL
    
    VALIDATION --> RENDER
    FIGURES --> RENDER
    DATA --> RENDER
    MARKDOWN_VAL --> RENDER
    
    RENDER --> PDFS
    RENDER --> LATEX
    
    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef validation fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef pipeline fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    
    class SRC,TESTS,SCRIPTS,MD component
    class VALIDATION,FIGURES,DATA,MARKDOWN_VAL validation
    class RENDER,PDFS,LATEX pipeline
```

## How render_pdf.sh Works with Markdown and Code

The `render_pdf.sh` script is the central orchestrator that ensures complete coherence between all components:

### 1. Code Validation Phase
- **Runs all generation scripts** - This validates that `src/` code works correctly
- **Scripts import from src/** - Ensures no code duplication and validates imports
- **Generates figures and data** - Creates outputs that markdown will reference

### 2. Markdown Validation Phase
- **Validates all image references** - Ensures figures referenced in markdown exist
- **Checks internal links** - Validates equation labels and section anchors
- **Validates equation formatting** - Ensures proper LaTeX equation environments

### 3. Documentation Generation Phase
- **Auto-generates glossary** - Creates API table from current `src/` code
- **Updates documentation** - Keeps code-doc sync automatically

### 4. Output Generation Phase
- **Builds individual PDFs** - Creates per-section PDFs from validated markdown
- **Builds combined PDF** - Creates unified document from all sections
- **Exports LaTeX** - Provides LaTeX source for further processing

## Test Suite and Code Connections

The test suite ensures 100% coverage of all `src/` modules and validates the entire pipeline:

### What Tests Validate
- **Mathematical correctness** - All functions produce expected results
- **Import compatibility** - Scripts can successfully import from `src/` modules
- **Output generation** - Figure and data generation works correctly
- **Deterministic execution** - All outputs are reproducible with fixed seeds
- **Path management** - Outputs go to correct directories

### Test-Driven Development Flow
```mermaid
flowchart TD
    START([Start Development]) --> TESTS[Write Tests First]
    TESTS --> IMPLEMENT[Implement Functionality]
    IMPLEMENT --> VALIDATE[Run Tests & Check Coverage]
    VALIDATE -->|Coverage < 100%| ADD_TESTS[Add Missing Tests]
    ADD_TESTS --> VALIDATE
    VALIDATE -->|Coverage = 100%| INTEGRATION[Test Script Integration]
    INTEGRATION --> DOCS[Update Documentation]
    DOCS --> PIPELINE[Run Complete Pipeline]
    PIPELINE --> SUCCESS[Development Complete]
    
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    
    class TESTS,IMPLEMENT,VALIDATE,ADD_TESTS,INTEGRATION,DOCS,PIPELINE process
    class START,SUCCESS success
```

1. **Write tests first** - Define expected behavior before implementation
2. **Implement functionality** - Write code to pass tests
3. **Validate integration** - Ensure scripts can use the code
4. **Update documentation** - Reflect changes in markdown
5. **Run complete pipeline** - Use `render_pdf.sh` to validate coherence

## Step-by-Step Workflow

### 1. Development Phase

```bash
# Always start with tests
uv run pytest tests/ --cov=src --cov-report=term-missing

# Check coverage (must be 100%)
coverage report

# Make code changes in src/
# Update corresponding tests
# Update documentation if needed
```

### 2. Validation Phase

```bash
# Run tests again to ensure changes work
uv run pytest

# Generate figures and data
uv run python scripts/example_figure.py
uv run python scripts/generate_research_figures.py

# Validate markdown integrity
uv run python repo_utilities/validate_markdown.py
```

### 3. Integration Phase

```bash
# Run the complete pipeline
./repo_utilities/render_pdf.sh
```

This script:
- Runs all generation scripts (validates src/ code works)
- Validates markdown references and images
- Generates auto-updated glossary from src/ API
- Builds individual and combined PDFs
- Exports LaTeX for further processing

## Key Components

### Source Code (`src/`)
- **`example.py`**: Basic mathematical functions (add, multiply, average, etc.)
- **`glossary_gen.py`**: API documentation generation utilities
- Additional modules can be added for specific project needs

**Critical Principle**: ALL business logic and algorithms must live in `src/` modules.

### Tests (`tests/`)
- **100% coverage required** for all src/ modules
- **Real numerical examples** (no mocks)
- **Deterministic RNG seeds** for reproducibility
- **Fast and hermetic** execution

### Generation Scripts (`scripts/`)
- **Import from src/** modules (no code duplication)
- **Use src/ methods for all computation** (never implement algorithms)
- **Generate figures and data** deterministically
- **Print output paths** to stdout for manifest collection
- **Use headless plotting** (MPLBACKEND=Agg)

### Documentation (`markdown/`)
- **References source code** using inline code formatting
- **Displays generated figures** from `output/figures/`
- **Passes validation** for images, references, and equations
- **Auto-updated glossary** from source API

### Output Structure (`output/`)
```
output/
├── figures/          # PNG/MP4/SVG files
├── data/             # CSV/NPZ files and manifests
├── pdf/              # Individual and combined PDFs
└── tex/              # Exported LaTeX files
```

## Validation Rules

### Markdown Validation
- All images must exist and be properly referenced
- Internal links must have valid anchors
- Equations must have unique labels
- No bare URLs (use informative link text)

### Code Validation
- All public APIs must have type hints
- No circular imports
- Consistent formatting and naming
- Error handling for edge cases

### Test Validation
- 100% statement and branch coverage
- All tests must pass
- No network or file-system writes outside output/
- Deterministic execution

## Development Commands

```bash
# Install dependencies
uv sync

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Generate figures
uv run python scripts/example_figure.py
uv run python scripts/generate_research_figures.py

# Validate markdown
uv run python repo_utilities/validate_markdown.py

# Build complete PDF pipeline
./repo_utilities/render_pdf.sh

# Clean all generated outputs (regeneratable)
./repo_utilities/clean_output.sh

# Check specific coverage
coverage report -m
```

## Output Management

### Clean Output Script

The `clean_output.sh` script safely removes all generated outputs since everything is regenerated from markdown sources:

```bash
# Clean all generated outputs
./repo_utilities/clean_output.sh
```

This script:
- Removes `output/` directory (all disposable)
- Preserves source code, tests, markdown, and scripts
- Provides clear instructions for regeneration

**Note**: All outputs are regeneratable from source, so cleaning is safe and often useful for troubleshooting or ensuring fresh builds.

### Output Directory Structure

```mermaid
graph TD
    OUTPUT[output/] --> FIGS[figures/<br/>PNG/MP4/SVG files]
    OUTPUT --> DATA[data/<br/>CSV/NPZ files]
    OUTPUT --> PDFS[pdf/<br/>Individual + Combined PDFs]
    OUTPUT --> TEX[tex/<br/>Exported LaTeX files]
    
    classDef dir fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef files fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class OUTPUT dir
    class FIGS,DATA,PDFS,TEX files
```

All directories under `output/` are disposable and can be safely cleaned.

## Benefits of This Paradigm

1. **Coherence**: Source code, tests, and documentation stay synchronized
2. **Validation**: Automatic checking of all references and outputs
3. **Reproducibility**: Deterministic generation of all artifacts
4. **Maintainability**: Clear separation of concerns with unified workflow
5. **Quality**: 100% test coverage enforced automatically
6. **Documentation**: Auto-generated API references and validation
7. **Thin Orchestrator Pattern**: Scripts use tested src/ methods, not duplicate logic

## Troubleshooting

### Common Issues

1. **Tests failing**: Check coverage and fix missing test cases
2. **Markdown validation errors**: Fix broken links, missing images, or duplicate labels
3. **Figure generation failures**: Ensure src/ modules work correctly
4. **PDF build errors**: Check pandoc and LaTeX installation

### Validation Commands

```bash
# Check what's failing
uv run python repo_utilities/validate_markdown.py

# Regenerate specific figures
uv run python scripts/example_figure.py

# Check test coverage gaps
coverage report -m
```

## Key Connections to Remember

1. **src/ modules → tests/ validation → scripts/ generation → markdown/ documentation**
2. **render_pdf.sh ensures all connections are valid before building outputs**
3. **Changes in any component must be reflected in all connected components**
4. **The test suite validates the entire pipeline, not just individual modules**
5. **Documentation is auto-generated where possible to maintain code-doc sync**
6. **Scripts are THIN ORCHESTRATORS that import and use src/ methods**
7. **Business logic lives ONLY in src/ - scripts handle orchestration and I/O**

## Thin Orchestrator Pattern

The workflow enforces a **thin orchestrator pattern** where:

- **`src/`** contains ALL business logic, algorithms, and mathematical implementations
- **`scripts/`** are lightweight wrappers that import and use `src/` methods
- **`tests/`** ensures 100% coverage of `src/` functionality
- **`render_pdf.sh`** orchestrates the entire pipeline

This ensures:
- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality
- **Reusability**: Scripts can use any `src/` method
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system

This workflow ensures that the generic project template maintains the highest standards of code quality, documentation coherence, and maintainability while providing a clear, scalable structure for development and collaboration.

For more details on architecture and implementation, see **[`ARCHITECTURE.md`](docs/ARCHITECTURE.md)** and **[`THIN_ORCHESTRATOR_SUMMARY.md`](docs/THIN_ORCHESTRATOR_SUMMARY.md)**.
