# 🏗️ Generic Project Architecture: Complete System Overview

> **Comprehensive overview** of the template's design, components, and build pipeline

**Quick Reference:** [How To Use](HOW_TO_USE.md) | [Two-Layer Architecture](TWO_LAYER_ARCHITECTURE.md) | [Workflow](WORKFLOW.md) | [Thin Orchestrator Summary](THIN_ORCHESTRATOR_SUMMARY.md)

This document provides a comprehensive overview of how the generic project template architecture works, explaining the connections between source code, tests, documentation, and the build pipeline. For related information, see **[`HOW_TO_USE.md`](HOW_TO_USE.md)** for complete usage guidance, **[`TWO_LAYER_ARCHITECTURE.md`](TWO_LAYER_ARCHITECTURE.md)** for the complete two-layer architecture guide, **[`WORKFLOW.md`](WORKFLOW.md)**, **[`THIN_ORCHESTRATOR_SUMMARY.md`](THIN_ORCHESTRATOR_SUMMARY.md)**, and **[`README.md`](README.md)**.

## Development Rules

For specific architectural rules and standards during development, see:

- **[`.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md)** - Complete development standards and guidelines
- **[`.cursorrules/infrastructure_modules.md`](../.cursorrules/infrastructure_modules.md)** - Infrastructure module development
- **[`.cursorrules/README.md`](../.cursorrules/README.md)** - Quick reference and patterns
- **[`THIN_ORCHESTRATOR_SUMMARY.md`](THIN_ORCHESTRATOR_SUMMARY.md)** - Thin orchestrator pattern implementation

## System Architecture Overview

```mermaid
graph TB
    subgraph "Generic Project Repository"
        subgraph "Core Components"
            INFRA[Infrastructure<br/>infrastructure/]
            PROJECT[Project Code<br/>project/src/]
            TESTS[Tests<br/>tests/ & project/tests/]
            SCRIPTS[Scripts<br/>scripts/ & project/scripts/]
            MD[Documentation<br/>docs/]
            MANUSCRIPT[Manuscript<br/>project/manuscript/]
        end
        
        subgraph "Thin Orchestrator Pattern"
            PROJECT -->|"100% tested<br/>methods"| SCRIPTS
            SCRIPTS -->|"import & use"| PROJECT
            PROJECT -->|"uses"| INFRA
            SCRIPTS -->|"generate"| OUTPUTS
            MANUSCRIPT -->|"reference"| OUTPUTS
        end
        
        subgraph "Build Pipeline"
            REPO_UTILS[Repo Utilities<br/>repo_utilities/]
            RENDER[run_all.py<br/>Pipeline Orchestrator]
        end
        
        subgraph "Outputs"
            OUTPUTS[Generated Outputs<br/>output/]
            PDFS[PDFs<br/>output/pdf/]
            FIGS[Figures<br/>output/figures/]
            DATA[Data<br/>output/data/]
            TEX[LaTeX<br/>output/tex/]
        end
        
        TESTS -->|"validate"| SRC
        SCRIPTS -->|"create"| FIGS
        SCRIPTS -->|"create"| DATA
        MD -->|"reference"| FIGS
        RENDER -->|"orchestrates"| ALL[All Components]
        REPO_UTILS -->|"support"| RENDER
    end
    
    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef pattern fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef pipeline fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef outputs fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SRC,TESTS,SCRIPTS,MD core
    class SRC,SCRIPTS pattern
    class REPO_UTILS,RENDER pipeline
    class OUTPUTS,PDFS,FIGS,DATA,TEX outputs
```

## Component Interactions

### 1. [LAYER 1] Infrastructure (`infrastructure/`)

**Location**: `infrastructure/` (root level)

**Purpose**: Generic, reusable build and validation tools that work with any research project.

**Key Modules**:
- `infrastructure/build/` - Build verification and reproducibility
- `infrastructure/core/` - Core utilities (exceptions, logging, config)
- `infrastructure/validation/` - PDF and markdown validation
- `infrastructure/documentation/` - Figure and documentation management
- `infrastructure/publishing/` - Academic publishing tools
- `infrastructure/literature/` - Literature search
- `infrastructure/llm/` - LLM integration
- `infrastructure/rendering/` - Multi-format rendering
- `infrastructure/scientific/` - Scientific dev tools

### 2. [LAYER 2] Project Code (`project/src/`)
**Purpose**: Implements mathematical functionality and business logic with comprehensive test coverage.

**Key Modules**:
- `example.py`: Basic mathematical functions (add, multiply, average, etc.)
- `simulation.py`: Scientific simulation framework
- `statistics.py`: Statistical analysis
- `data_generator.py`: Synthetic data generation
- `data_processing.py`: Data preprocessing and cleaning
- `metrics.py`: Performance metrics
- `parameters.py`: Parameter management
- `performance.py`: Convergence and scalability analysis
- `plots.py`: Plot implementations
- `reporting.py`: Report generation
- `validation.py`: Result validation
- `visualization.py`: Visualization engine

**Note**: `glossary_gen.py` is in `infrastructure/documentation/`, not `project/src/`

**Responsibilities**:
- Provide clean, well-typed APIs for mathematical operations
- Ensure numerical stability and exact arithmetic where appropriate
- Maintain mathematical consistency across all modules
- **CRITICAL**: Contain ALL business logic and algorithms

### 2. Test Suite (`tests/`)
**Purpose**: Validates all source code functionality with comprehensive coverage.

**Coverage Requirements**:
- **Infrastructure**: 60% minimum (currently achieving 66.76%)
- **Project code**: 90% minimum (currently achieving 98.03%)
- **No mocks**: All tests use real numerical examples
- **Deterministic**: Fixed RNG seeds for reproducible results

**Validation Scope**:
- Mathematical correctness of all functions
- Import compatibility between modules
- Output generation and path management
- Integration with generation scripts

### 3. Generation Scripts (`scripts/`)
**Purpose**: **Thin orchestrators** that import and use `src/` methods to generate figures and data.

**Key Scripts**:
- `example_figure.py`: Basic integration example using project/src/ methods
- `generate_research_figures.py`: Advanced integration example

**Thin Orchestrator Pattern**:
```mermaid
graph LR
    subgraph "Scripts (scripts/)"
        SCRIPT[Script File]
        IMPORT[Import project/src/ methods]
        USE[Use project/src/ methods]
        VISUALIZE[Handle visualization]
        OUTPUT[Save outputs]
    end
    
    subgraph "Project Source (project/src/)"
        FUNC1[add_numbers]
        FUNC2[calculate_average]
        FUNC3[find_maximum]
    end
    
    SCRIPT --> IMPORT
    IMPORT --> USE
    USE --> FUNC1
    USE --> FUNC2
    USE --> FUNC3
    USE --> VISUALIZE
    VISUALIZE --> OUTPUT
    
    classDef script fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef src fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class SCRIPT,IMPORT,USE,VISUALIZE,OUTPUT script
    class FUNC1,FUNC2,FUNC3 src
```

**Workflow**:
1. Import required functions from `project/src/` modules
2. Use project/src/ methods for all computation (never implement algorithms)
3. Handle visualization, I/O, and orchestration
4. Generate deterministic outputs with fixed seeds
5. Save figures to `output/figures/`
6. Save data to `output/data/`
7. Print output paths for manifest collection

### 4. Documentation (`docs/`)
**Purpose**: Document mathematical concepts with references to implemented code.

**Structure**:
- `manuscript/preamble.md`: LaTeX preamble and styling
- `manuscript/01_introduction.md`: Project introduction and overview
- `manuscript/02_methodology.md`: Mathematical framework and equations
- `manuscript/03_experimental_results.md`: Results with figure references
- `manuscript/04_discussion.md`: Discussion and cross-references
- `manuscript/05_conclusion.md`: Summary and conclusions
- `manuscript/98_symbols_glossary.md`: Auto-generated API reference from `project/src/`

**Content Requirements**:
- Reference source code using inline code formatting
- Display generated figures from `output/figures/`
- Use descriptive links (no bare URLs)
- Pass all validation checks
- Include proper LaTeX equation environments

## The Pipeline Orchestrator

### Complete Pipeline Flow

```mermaid
flowchart TD
    START([Start run_all.py]) --> STAGE0[Stage 00: Setup Environment]
    STAGE0 --> STAGE1[Stage 01: Run Tests]
    STAGE1 --> STAGE2[Stage 02: Run Analysis]
    STAGE2 --> STAGE3[Stage 03: Render PDF]
    STAGE3 --> STAGE4[Stage 04: Validate Output]
    STAGE4 --> STAGE5[Stage 05: Copy Outputs]
    STAGE5 --> SUCCESS[Build successful]

    STAGE0 -->|Fail| FAIL0[Setup failed]
    STAGE1 -->|Fail| FAIL1[Tests failed]
    STAGE2 -->|Fail| FAIL2[Analysis failed]
    STAGE3 -->|Fail| FAIL3[PDF build failed]
    STAGE4 -->|Fail| FAIL4[Validation failed]
    STAGE5 -->|Fail| FAIL5[Copy failed]
    
    FAIL0 --> END([Exit with error])
    FAIL1 --> END
    FAIL2 --> END
    FAIL3 --> END
    FAIL4 --> END
    FAIL5 --> END
    
    SUCCESS --> END
    
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef failure fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    
    class SUCCESS success
    class FAIL0,FAIL1,FAIL2,FAIL3,FAIL4,FAIL5 failure
    class STAGE0,STAGE1,STAGE2,STAGE3,STAGE4,STAGE5 process
```

### Phase 1: Code Validation
```bash
# Run all generation scripts to validate project/src/ code works
uv run python scripts/example_figure.py
uv run python scripts/generate_research_figures.py
```

**Purpose**: Ensures that all source code modules can be imported and used successfully by generation scripts.

### Phase 2: Markdown Validation
```bash
# Validate all markdown references and images
python3 -m infrastructure.validation.cli markdown project/manuscript/
```

**Checks**:
- All referenced images exist in output directories
- Internal links have valid anchors
- Equations have unique labels
- No bare URLs (use informative link text)

### Phase 3: Documentation Generation
```bash
# Auto-generate glossary from current project/src/ API
python3 -m infrastructure.documentation.generate_glossary_cli
```

**Purpose**: Keeps documentation automatically synchronized with source code changes. This is also integrated into the build pipeline (Stage 03).

### Phase 4: Output Generation
```bash
# Build individual PDFs from validated markdown
pandoc [markdown_file] -o [output_pdf]

# Build combined PDF from all sections
pandoc [combined_markdown] -o project_combined.pdf

# Export LaTeX for further processing
pandoc [markdown_file] -o [output_tex]
```

## Data Flow and Dependencies

### Input Dependencies
1. **Project code** (`project/src/`) - Mathematical implementations
2. **Markdown files** (`manuscript/`) - Manuscript content
3. **LaTeX preamble** (`manuscript/preamble.md`) - Formatting

### Processing Pipeline
```mermaid
graph LR
    subgraph "Input"
        PROJECT[project/src/ modules]
        MD[Markdown files]
        MANUSCRIPT[manuscript/ files]
        PREAMBLE[LaTeX preamble]
    end
    
    subgraph "Processing"
        TESTS[Test validation]
        SCRIPTS[Script execution]
        VALIDATION[Markdown validation]
        GLOSSARY[Glossary generation]
    end
    
    subgraph "Output"
        FIGS[Figures]
        DATA[Data files]
        PDFS[PDFs]
        TEX[LaTeX exports]
    end
    
    SRC --> TESTS
    SRC --> SCRIPTS
    MD --> VALIDATION
    MANUSCRIPT --> VALIDATION
    SRC --> GLOSSARY
    SCRIPTS --> FIGS
    SCRIPTS --> DATA
    MD --> PDFS
    MANUSCRIPT --> PDFS
    MD --> TEX
    MANUSCRIPT --> TEX
    
    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SRC,MD,MANUSCRIPT,PREAMBLE input
    class TESTS,SCRIPTS,VALIDATION,GLOSSARY process
    class FIGS,DATA,PDFS,TEX output
```

1. **Scripts import from project/src/** → Validate code functionality
2. **Scripts generate outputs** → Create figures and data
3. **Markdown references outputs** → Link documentation to results
4. **Validation ensures coherence** → All references are valid
5. **PDF generation** → Create final documentation

### Output Structure
```
output/
├── figures/          # PNG/MP4/SVG files from scripts
├── data/             # CSV/NPZ files and manifests
├── pdf/              # Individual and combined PDFs
└── tex/              # Exported LaTeX files
```

## Quality Assurance Mechanisms

### 1. Test Coverage Enforcement
- **90% project coverage, 60% infrastructure** minimum via build pipeline
- **Automated validation** in build pipeline
- **Real numerical examples** ensure mathematical correctness

### 2. Markdown Validation
- **Image reference validation** - All figures must exist
- **Link validation** - Internal references must be valid
- **Equation validation** - Proper LaTeX formatting required

### 3. Pipeline Validation
- **Script execution** - All generation scripts must succeed
- **Output generation** - All expected files must be created
- **PDF compilation** - All markdown must generate valid PDFs

### 4. Reproducibility
- **Deterministic RNG** - Fixed seeds for all random operations
- **Headless plotting** - `MPLBACKEND=Agg` for CI compatibility
- **Path management** - Consistent output directory structure

### 5. Automatic Numbering and Cross-Referencing
- **Figure numbering**: Automatically managed by LaTeX/pandoc
- **Equation numbering**: LaTeX equation environments with `\label{}` and `\eqref{}`
- **Section numbering**: Automatic section numbering with `--number-sections`
- **Table of contents**: Auto-generated TOC with `--toc` and `--toc-depth=3`
- **Cross-references**: Use `\ref{}` for figures and `\eqref{}` for equations

**Example markdown usage**:
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/figure.png}
\caption{Figure caption}
\label{fig:example}
\end{figure}

\begin{equation}\label{eq:example}
E = mc^2
\end{equation}

See Figure \ref{fig:example} and Equation \eqref{eq:example}.
```

## Development Workflow

### 1. Code Changes
```bash
# Write tests first (TDD)
# Implement functionality
# Ensure coverage requirements met
# Update documentation if needed
```

### 2. Validation
```bash
# Run complete test suite
uv run pytest tests/ --cov=src --cov-report=term-missing

# Generate figures and validate
uv run python scripts/example_figure.py
python3 -m infrastructure.validation.cli markdown project/manuscript/
```

### 3. Integration
```bash
# Run complete pipeline
python3 scripts/run_all.py

# Or individual stages
python3 scripts/03_render_pdf.py  # PDF generation

# Verify all outputs are generated
# Check that PDFs build successfully
```

## Benefits of This Architecture

1. **Coherence**: Source code, tests, and documentation stay synchronized
2. **Validation**: Automatic checking of all references and outputs
3. **Reproducibility**: Deterministic generation of all artifacts
4. **Maintainability**: Clear separation of concerns with unified workflow
5. **Quality**: Comprehensive test coverage enforced automatically
6. **Documentation**: Auto-generated API references and validation
7. **Thin Orchestrator Pattern**: Scripts use tested project/src/ methods, not duplicate logic

## Key Principles

1. **Single Source of Truth**: Source code is the authoritative implementation
2. **Test-Driven Development**: Tests validate functionality before implementation
3. **Automated Validation**: All components are automatically checked for coherence
4. **Reproducible Outputs**: All results are deterministic and verifiable
5. **Integrated Workflow**: One command (`python3 scripts/run_all.py`) validates the entire system
6. **Thin Orchestrator Pattern**: Scripts import and use project/src/ methods, never implement algorithms

## Thin Orchestrator Pattern

The architecture enforces a **thin orchestrator pattern** where:

- **`project/src/`** contains ALL business logic, algorithms, and mathematical implementations
- **`project/scripts/`** are lightweight wrappers that import and use `project/src/` methods
- **`project/tests/`** ensures comprehensive coverage of `project/src/` functionality
- **`scripts/run_all.py`** orchestrates the entire 6-stage pipeline

This ensures:
- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality
- **Reusability**: Scripts can use any `project/src/` method
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system

This architecture ensures that the generic project template maintains the highest standards of code quality, documentation coherence, and maintainability while providing a clear, scalable structure for development and collaboration.

For more details on implementation, see:
- **[`TWO_LAYER_ARCHITECTURE.md`](TWO_LAYER_ARCHITECTURE.md)** - Complete two-layer architecture guide
- **[`THIN_ORCHESTRATOR_SUMMARY.md`](THIN_ORCHESTRATOR_SUMMARY.md)** - Thin orchestrator pattern details
- **[`WORKFLOW.md`](WORKFLOW.md)** - Development workflow