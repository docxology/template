# Two-Layer Architecture - Current State Analysis

## Document Purpose

This document captures the complete analysis of the template's two-layer architecture, identifying how repo-scale infrastructure and project-specific scientific content are currently organized, and how they will be reorganized for maximum clarity.

## Current Architecture

### Layer 1: Infrastructure (Repo-Scale)

These modules provide generic build, validation, and development infrastructure applicable to any research project using this template:

#### In src/
- `build_verifier.py` - Build process verification and artifact validation
- `integrity.py` - File integrity checking and cross-reference validation
- `quality_checker.py` - Document quality metrics and academic standards checking
- `reproducibility.py` - Build reproducibility tracking and environment capture
- `publishing.py` - Academic publishing workflow assistance (DOI, citations, metadata)
- `pdf_validator.py` - PDF rendering quality validation
- `glossary_gen.py` - Automatic API documentation generation from source code
- `markdown_integration.py` - Figure insertion and markdown cross-reference management
- `figure_manager.py` - Automatic figure numbering and LaTeX block generation
- `image_manager.py` - Image file management and insertion

#### In scripts/
- `run_all.py` - Master pipeline orchestrator (6 stages)
- `00_setup_environment.py` - Environment setup & validation
- `01_run_tests.py` - Test execution with coverage
- `02_run_analysis.py` - Analysis script discovery & execution
- `03_render_pdf.py` - PDF rendering orchestration
- `04_validate_output.py` - Output validation & reporting
- `05_copy_outputs.py` - Copy final deliverables

#### Supporting Files
- `ide_style.css` - HTML rendering styling
- `convert_latex_images.lua` - Pandoc LaTeX to HTML filter

#### In tests/
- Infrastructure-specific tests: `test_build_verifier.py`, `test_integrity.py`, `test_quality_checker.py`, etc.

---

### Layer 2: Scientific (Project-Specific)

These modules implement domain-specific functionality for the research project:

#### In src/
- `example.py` - Basic mathematical operations (template demo)
- `simulation.py` - Core simulation framework with reproducibility
- `statistics.py` - Statistical analysis functions
- `data_generator.py` - Synthetic data generation
- `data_processing.py` - Data preprocessing and cleaning
- `metrics.py` - Performance and quality metrics
- `parameters.py` - Parameter set management and validation
- `performance.py` - Convergence and scalability analysis
- `plots.py` - Publication-quality plot implementations
- `reporting.py` - Automated report generation
- `validation.py` - Result validation framework
- `visualization.py` - Visualization engine with styling

#### In scripts/
- `example_figure.py` - Basic figure generation example
- `generate_research_figures.py` - Complex research figure generation
- `analysis_pipeline.py` - Statistical analysis workflow
- `scientific_simulation.py` - Simulation execution example
- `generate_scientific_figures.py` - Automated figure generation with markdown integration

#### In manuscript/
- `01_abstract.md` through `09_appendix.md` - Research content
- `S01_supplemental_methods.md` through `S04_supplemental_applications.md` - Supplementary material
- `98_symbols_glossary.md` - API reference (auto-generated)
- `99_references.md` - Bibliography

#### In tests/
- Scientific-specific tests: `test_example.py`, `test_simulation.py`, `test_statistics.py`, etc.

---

## Key Observations

### Current Strengths

1. **Functional Separation**: Infrastructure and scientific code are already functionally separate
2. **Thin Orchestrator Pattern**: Scripts properly use src/ methods without duplicating logic
3. **Testing Culture**: 97% coverage achieved with real data testing (no mocks)
4. **Documentation**: Each directory has AGENTS.md explaining its role
5. **Build Integration**: Pipeline works reliably end-to-end

### Current Weaknesses

1. **No Explicit Package Structure**: All 23 modules live flat in src/, making separation implicit
2. **Unclear Naming**: Module names don't indicate which layer they belong to
3. **Mixed Imports**: Tests and scripts don't distinguish infrastructure from scientific imports
4. **Logging Blind Spots**: No indication when execution crosses layer boundaries
5. **Documentation Gaps**: Users must infer layer membership from module description
6. **Adding Code**: No clear decision tree for where to add new functionality

---

## Layer Characteristics

### Infrastructure Layer Requirements

**Define as:** Generic, reusable, template functionality

**Examples:**
- "Does it make sense in ANY research project using this template?"
- "Is it about building, validating, or packaging?"
- "Would multiple projects use this unchanged?"

**Key Properties:**
- 49% minimum test coverage (currently achieving 55.89%)
- Real data testing (no mocks)
- Comprehensive error handling
- Logged execution with clear messages
- Type hints on all APIs

### Scientific Layer Requirements

**Define as:** Project-specific algorithms, analysis, visualizations

**Examples:**
- "Is it specific to our research domain?"
- "Would a different project use completely different code?"
- "Does it use domain-specific logic?"

**Key Properties:**
- 70% minimum test coverage (currently achieving 99.88%)
- Uses infrastructure layer tools when needed
- Real data testing (no mocks)
- Domain-specific documentation
- Integration with manuscript

---

## Impact of Reorganization

### What Changes
- Code organization structure (explicit packages)
- Import statements (clearer paths)
- Test organization (mirrors code structure)
- Logging (layer-aware)
- Documentation (explicit layer assignment)

### What Stays the Same
- Functional behavior (all code remains unchanged)
- Test coverage requirements (100%)
- Build pipeline (continues to work)
- API surface (no breaking changes)
- Thin orchestrator pattern

---

## Migration Strategy

### Phase Approach
1. Create package structure
2. Move files (code unchanged)
3. Update all imports
4. Enhance logging
5. Reorganize tests
6. Update documentation
7. Validate everything

### No Breaking Changes
- All functionality remains identical
- Only import paths and file organization change
- Existing scripts continue to work
- Tests maintain same coverage

### Rollback Plan
If needed: `git restore .` returns to current state

---

## Measurement Success

✅ Code organization makes layer boundaries explicit  
✅ Documentation clearly explains which code belongs where  
✅ Logging shows layer transitions during execution  
✅ All tests pass with 95%+ coverage  
✅ PDFs generate successfully  
✅ New developers understand layers quickly  
✅ Adding new code to correct layer is obvious  

---

## Next Steps

Implementation proceeds through 7 phases as outlined in the main plan, starting with package creation.



