# Ento-Linguistic Research Project

## Overview

This is a self-contained research project examining the entanglement of speech and thought in entomology. The project investigates how language shapes scientific understanding of ant biology through systematic analysis of terminology networks across six Ento-Linguistic domains.

Everything needed for the research is in this folder:

- **src/** - Ento-Linguistic analysis algorithms and text processing
- **tests/** - Test suite (90%+ coverage)
- **scripts/** - Analysis workflows and pipelines
- **manuscript/** - Research manuscript on language in entomology
- **output/** - Generated analyses, figures, data, and PDFs

## Research Focus

**Ento-Linguistic Analysis**: Systematic investigation of how terminology in entomological research creates conceptual frameworks, framing assumptions, and communication challenges.

**Six Core Domains**:

1. **Unit of Individuality** - What constitutes an "ant" (nestmate, colony, superorganism)?
2. **Behavior and Identity** - How behavioral descriptions create categorical identities?
3. **Power & Labor** - What hierarchical structures do terms like "caste" and "queen" impose?
4. **Sex & Reproduction** - How human gender concepts shape understanding of ant reproduction?
5. **Kin & Relatedness** - What constitutes "kin" in ant societies?
6. **Economics** - How market logic applies to resource allocation in colonies?

## Architecture

### Source Code (src/)

Organized into five subdirectory packages:

```
src/
├── __init__.py
├── analysis/              # Text analysis, NLP, and domain-specific modules
│   ├── __init__.py
│   ├── cace_scoring.py         # CACE scoring framework
│   ├── conceptual_mapping.py   # Concept mapping and network construction
│   ├── discourse_analysis.py   # Discourse pattern and rhetorical analysis
│   ├── discourse_patterns.py   # Discourse pattern detection
│   ├── domain_analysis.py      # Domain-specific analysis across six areas
│   ├── performance.py          # Convergence and scalability analysis
│   ├── persuasive_analysis.py  # Persuasive technique analysis
│   ├── rhetorical_analysis.py  # Rhetorical structure analysis
│   ├── semantic_entropy.py     # Semantic entropy computation
│   ├── statistics.py           # Statistical analysis of language patterns
│   ├── term_extraction.py      # Terminology extraction and domain classification
│   └── text_analysis.py        # Text processing and linguistic feature extraction
├── core/                  # Core utilities, validation, metrics
│   ├── __init__.py
│   ├── example.py              # Template example with basic operations
│   ├── exceptions.py           # Custom exception classes
│   ├── logging.py              # Logging utilities
│   ├── markdown_integration.py # Markdown integration helpers
│   ├── metrics.py              # Performance metrics and quality measures
│   ├── parameters.py           # Parameter set management and validation
│   ├── validation.py           # Result validation and quality assurance
│   └── validation_utils.py     # Validation utility functions
├── data/                  # Data loading, generation, and literature mining
│   ├── __init__.py
│   ├── data_generator.py       # Synthetic data generation
│   ├── data_processing.py      # Preprocessing, cleaning, normalization
│   ├── literature_mining.py    # Scientific literature collection and processing
│   └── loader.py               # Data loading utilities
├── pipeline/              # Simulation and reporting infrastructure
│   ├── __init__.py
│   ├── reporting.py            # Automated report generation
│   └── simulation.py           # Scientific simulation framework
└── visualization/         # All visualization and figure generation
    ├── __init__.py
    ├── concept_visualization.py    # Concept network and domain visualizations
    ├── figure_manager.py           # Figure registry and management
    ├── plots.py                    # Plot type implementations
    ├── statistical_visualization.py # Statistical analysis visualizations
    └── visualization.py            # Publication-quality figure generation
```

**Requirements:**

- 90% minimum test coverage
- Type hints on all public APIs
- Docstrings with examples
- Real literature data testing (no mocks)
- Reproducible text analysis pipelines

### Analysis Tests (tests/)

Test suite validating all Ento-Linguistic analysis code:

- **90% minimum coverage required** - All critical analysis paths tested
- **Real literature testing** - Use actual entomological texts, not mocks
- **Integration tests** - Test module interactions
- **Performance tests** - Validate algorithms

**Running tests:**

```bash
pytest tests/ --cov=src
pytest tests/ --cov=src --cov-report=html
```

### Analysis Scripts (scripts/)

Two active scripts plus archived helpers:

```
scripts/
├── 01_build_corpus.py            # Build literature corpus from sources
├── 02_generate_figures.py        # Generate all manuscript figures
├── _analysis_pipeline.py         # (inactive) Main orchestrator
├── _conceptual_mapping_script.py # (inactive) Concept mapping generation
├── _convert_corpus.py            # (inactive) Corpus format conversion
├── _discourse_analysis_script.py # (inactive) Discourse pattern analysis
├── _domain_analysis_script.py    # (inactive) Domain terminology analysis
├── _example_figure.py            # (inactive) Example figure generation
├── _generate_domain_figures.py   # (inactive) Domain figure generation
├── _generate_missing_figures.py  # (inactive) Missing figure generation
├── _generate_scientific_figures.py # (inactive) Scientific figure generation
├── _literature_analysis_pipeline.py # (inactive) Literature mining pipeline
├── _manuscript_preflight.py      # (inactive) Manuscript validation
├── _quality_report.py            # (inactive) Quality metrics report
├── _register_manuscript_figures.py # (inactive) Figure registry updates
├── _render_pdf_override.py       # (inactive) Custom PDF rendering
└── _scientific_simulation.py     # (inactive) Simulation workflows
```

Active scripts (`01_`, `02_` prefixed) are executed by the pipeline. Scripts prefixed with `_` are inactive helpers preserved for reference.

### Manuscript (manuscript/)

Ento-Linguistic research content in Markdown:

```
manuscript/
├── 01_abstract.md                # Research overview and contributions
├── 02_introduction.md            # Speech/thought entanglement motivation
├── 03_methodology.md             # Mixed-methodology framework
├── 04_experimental_results.md    # Computational analysis results
├── 05_discussion.md              # Theoretical implications
├── 06_conclusion.md              # Future directions and recommendations
├── 07_related_work.md            # Literature review and positioning
├── 08_acknowledgments.md         # Funding and acknowledgments
├── S01_supplemental_methods.md   # Detailed computational methods
├── S02_supplemental_results.md   # Extended domain analyses
├── S03_supplemental_analysis.md  # Theoretical frameworks
├── S04_supplemental_applications.md # Case studies and examples
├── 98_symbols_glossary.md        # Terminology glossary
├── 99_references.md              # Bibliography
├── references.bib                # BibTeX bibliography database
├── config.yaml                   # Publication metadata
├── config.yaml.example           # Configuration template
├── preamble.md                   # LaTeX preamble (markdown wrapped)
└── preamble.tex                  # LaTeX preamble (raw)
```

### Output (output/)

Generated results (disposable):

```
output/
├── figures/           # PNG figures
├── logs/              # Pipeline logs
├── reports/           # Generated reports
├── .checkpoints/      # Pipeline checkpoint state
└── pdf/               # Generated PDFs (when rendered)
```

These files are regenerated on each build and can be deleted safely.

## Testing

### Running Tests

```bash
# All tests with coverage
pytest tests/ --cov=src --cov-fail-under=90

# Specific test file
pytest tests/test_module_name.py -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
```

### Test Rules

- Write tests first (TDD)
- Test with real data (no mocks)
- Cover edge cases
- Maintain 90%+ coverage

## Building the Manuscript

From template root:

```bash
python3 scripts/03_render_pdf.py
```

Or use the full pipeline:

```bash
python3 scripts/execute_pipeline.py --core-only
```

## See Also

- Root AGENTS.md - Template architecture
- Root README.md - Template overview
- scripts/AGENTS.md - Script documentation
- src/AGENTS.md - Source code documentation
- manuscript/AGENTS.md - Manuscript documentation
