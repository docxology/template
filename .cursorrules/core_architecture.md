# Core Architecture Principles

## System Overview

This repository follows a unified paradigm: source code, tests, and documentation developed together using a thin orchestrator pattern.

## Core Components

### src/ - Business Logic (100% Tested)
- All mathematical implementations
- Data analysis algorithms
- Complex computations
- API definitions with type hints
- **Requirement**: 100% test coverage
- **Principle**: Pure, testable functions

### tests/ - Comprehensive Testing
- Tests for all `src/` code
- Real data analysis (no mocks)
- Integration tests
- Deterministic, reproducible
- **Requirement**: 100% coverage for `src/`
- **Principle**: Test actual behavior, not mocks

### scripts/ - Thin Orchestrators
- Import methods from `src/`
- Handle I/O and visualization
- Coordinate between components
- Demonstrate integration patterns
- **Principle**: No business logic here
- **Pattern**: Lightweight wrappers

### docs/ - Documentation Hub
- Project documentation
- Architecture guides
- Manuscript content (generates PDFs)
- API references
- **Organization**: Modular by topic
- **Coverage**: Every directory has AGENTS.md + README.md

### Output/ - Generated Artifacts (All Disposable)
- PDFs from LaTeX compilation
- Figures from script execution
- Data files (CSV, NPZ)
- Reports and analysis
- **Principle**: Regenerated from source
- **Management**: Never commit to version control
- **Documentation**: NO AGENTS.md or README.md (directory is cleaned on every build)

## Workflow Integration

```
manuscript/ (markdown) → render_pdf.sh → output/ (PDFs)
                           ↓
                      run tests ✅
                           ↓
                      execute scripts
                           ↓
                      generate output
                           ↓
                      validate & done
```

### Build Pipeline Stages

1. **Clean**: Remove previous outputs
2. **Test**: Verify code with 100% coverage
3. **Execute**: Run all scripts with src/ functions
4. **Generate**: Create PDFs, figures, reports
5. **Validate**: Check all outputs valid
6. **Package**: Organize for distribution

## Key Principles

### 1. Thin Orchestrator Pattern
- **src/**: Contains algorithms and logic
- **scripts/**: Coordinate and visualize
- **Benefit**: Reusable, testable, maintainable

### 2. 100% Test Coverage
- Every line in `src/` is tested
- Uses real data, no mocks
- Tests validate actual behavior
- Ensures reliability

### 3. Reproducibility
- Deterministic algorithms (fixed seeds)
- Consistent output format
- Version-controlled source
- Regenerable build artifacts

### 4. Complete Documentation
- AGENTS.md at every directory level
- README.md for quick reference
- Clear, well-commented code
- Auto-generated where possible

### 5. Coherent Integration
- Changes reflected across components
- Tests validate full pipeline
- Output reflects source state
- Documentation stays current

## Component Relationships

```
src/ ←→ tests/
  ↓         ↓
scripts/ ← uses
  ↓
output/ (figures, data)
  ↓
docs/ (references output)
  ↓
manuscript/ (references all)
  ↓
PDFs (final output)
```

## Design Patterns

### Separation of Concerns
- Each module has clear responsibility
- Minimal dependencies between components
- Interfaces are well-defined
- Easy to test and modify

### Composability
- Functions designed for reuse
- Clear input/output contracts
- Support different calling patterns
- Facilitate testing and mocking (where needed)

### Orchestration Rigor
- Scripts follow clear patterns
- Dependencies tracked explicitly
- Error handling comprehensive
- Logging provides visibility

## Scaling Considerations

### Modularity
- Add new modules in `src/`
- Create corresponding tests
- Write scripts using new functions
- Document with AGENTS.md/README.md

### Testing Growth
- Tests follow same patterns
- Real data for all tests
- No mock methods (real integration)
- Coverage maintained at 100%

### Documentation Scale
- Each module documents itself
- Cross-references between modules
- Automated generation where possible
- Consistent structure maintained

## Comprehensive Documentation

For in-depth guidance on these architectural principles, see:

- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) - Complete system architecture overview
- [`docs/TWO_LAYER_ARCHITECTURE.md`](../docs/TWO_LAYER_ARCHITECTURE.md) - Two-layer architecture details
- [`docs/DECISION_TREE.md`](../docs/DECISION_TREE.md) - Code placement decision guide
- [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development process and workflow integration

## See Also

- [thin_orchestrator.md](thin_orchestrator.md) - Detailed pattern explanation
- [testing.md](testing.md) - Testing standards and practices
- [documentation.md](documentation.md) - Documentation requirements
- [../AGENTS.md](../AGENTS.md) - Complete system documentation

