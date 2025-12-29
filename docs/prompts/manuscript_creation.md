# Manuscript Creation Prompt

## Purpose

Create a complete, compliant research manuscript from scratch based on a research description, ensuring full compliance with the Research Project Template standards and architecture.

## Context

This prompt leverages extensive project documentation to create manuscripts that follow professional academic standards:

- [`../../projects/project/docs/manuscript_style_guide.md`](../../projects/project/docs/manuscript_style_guide.md) - Section numbering, cross-references, equations, figures
- [`../../projects/project/docs/standards_compliance.md`](../../projects/project/docs/standards_compliance.md) - Manuscript formatting standards
- [`../../projects/project/docs/development_workflow.md`](../../projects/project/docs/development_workflow.md) - Research workflow integration
- [`../../.cursorrules/manuscript_style.md`](../../.cursorrules/manuscript_style.md) - Manuscript style standards

## Prompt Template

```
You are creating a complete research manuscript from scratch using the Research Project Template. The manuscript must be fully compliant with all template standards and include a complete research project structure.

RESEARCH TOPIC: [Describe your research topic, objectives, methods, and expected contributions]

Create a complete manuscript with the following structure:

## 1. Manuscript Structure (Complete File Set)

Create all required manuscript files following the section numbering system:

### Main Sections (01-09)
- `01_abstract.md` - Research overview and key contributions
- `02_introduction.md` - Project structure and motivation
- `03_methodology.md` - Mathematical framework and algorithms
- `04_experimental_results.md` - Performance evaluation and validation
- `05_discussion.md` - Theoretical implications and comparisons
- `06_conclusion.md` - Summary and future directions
- `08_acknowledgments.md` - Funding, collaborators, acknowledgments
- `09_appendix.md` - Technical details, proofs, derivations

### Supplemental Sections (S01-S0N)
- `S01_supplemental_methods.md` - Extended methodological details
- `S02_supplemental_results.md` - Additional experimental results
- `S03_supplemental_analysis.md` - Extended theoretical analysis

### Reference Sections (98-99)
- `98_symbols_glossary.md` - Mathematical symbols and notation
- `99_references.md` - Complete bibliography

### Configuration Files
- `config.yaml` - Paper metadata, authors, publication info
- `references.bib` - BibTeX bibliography database
- `preamble.md` - LaTeX preamble customizations

## 2. Cross-Referencing System

Implement complete cross-referencing throughout the manuscript:

### Section References
Use `\ref{sec:name}` with `{#sec:name}` labels:
```markdown
# Introduction {#sec:introduction}

As discussed in Section \ref{sec:methodology}, our approach...
```

### Equation References
Use `\eqref{eq:name}` with `\label{eq:name}` in equation environments:
```latex
\begin{equation}\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}

The objective function \eqref{eq:objective} defines...
```

### Figure References
Use `\ref{fig:name}` with proper figure formatting:
```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/results.png}
\caption{Experimental results visualization.}
\label{fig:results}
\end{figure}

See Figure \ref{fig:results} for detailed results.
```

## 3. Research Code Implementation

Create a complete `src/` directory with research algorithms:

### Core Modules
- `example.py` - Basic operations and utilities
- `simulation.py` - Research simulation framework
- `data_generator.py` - Synthetic data generation
- `data_processing.py` - Data preprocessing and cleaning
- `statistics.py` - Statistical analysis methods
- `metrics.py` - Performance evaluation metrics
- `validation.py` - Result validation and error checking
- `visualization.py` - Publication-quality plotting

### Algorithm Implementation Requirements
- Type hints on all public APIs
- Comprehensive docstrings (Google style)
- Error handling with custom exceptions
- Logging using `get_logger(__name__)`
- Pure functions where possible
- Reproducible results (fixed seeds)

## 4. Analysis Scripts

Create `scripts/` directory with thin orchestrators:

### Analysis Pipelines
- `analysis_pipeline.py` - Complete research workflow
- `example_figure.py` - Figure generation examples
- Additional scripts for specific analyses

### Script Requirements
- Import from `src/` modules (no business logic in scripts)
- Handle I/O and configuration
- Use infrastructure modules for logging and validation
- Generate figures integrated with manuscript

## 5. Comprehensive Testing

Create `tests/` directory with complete test coverage:

### Test Structure
- `test_*.py` files matching `src/` modules
- 90% minimum coverage requirement
- **NO MOCKS** - use real data only
- Integration tests for end-to-end workflows

### Testing Patterns
```python
def test_research_algorithm():
    """Test research algorithm with real data."""
    # Generate or load actual test data
    test_data = generate_test_dataset()

    # Run algorithm
    result = research_algorithm(test_data)

    # Validate results with real assertions
    assert result.accuracy > 0.85
    assert result.is_valid
```

## 6. Documentation

Create complete documentation following standards:

### AGENTS.md Files
- `src/AGENTS.md` - Technical documentation for algorithms
- `scripts/AGENTS.md` - Script documentation
- `tests/AGENTS.md` - Testing documentation

### README.md Files
- Project `README.md` with Mermaid diagrams
- Clear navigation and quick reference

## 7. Configuration and Metadata

### config.yaml Structure
```yaml
paper:
  title: "Research Title"
  subtitle: "Optional Subtitle"
  version: "1.0"

authors:
  - name: "Dr. Researcher Name"
    orcid: "0000-0000-0000-1234"
    email: "researcher@university.edu"
    affiliation: "University Name"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"
```

### Bibliography Management
- Complete `references.bib` with all cited works
- Consistent citation style
- DOI inclusion where available

## 8. Quality Assurance

Ensure all output meets standards:

### Validation Requirements
- Markdown validation (cross-references, image links)
- PDF generation and validation
- Code linting and type checking
- Test coverage verification

### Manuscript Standards
- Professional academic formatting
- Consistent notation and terminology
- Complete mathematical derivations
- Clear figure and table presentation

## Key Requirements

- [ ] Complete manuscript structure (01-09, S01-S0N, 98-99)
- [ ] Proper cross-referencing (\ref{}, \eqref{}, \cite{})
- [ ] Mathematical equations with proper formatting
- [ ] Figures and tables with captions and labels
- [ ] Complete research code in `src/` (90% coverage)
- [ ] Thin orchestrator scripts in `scripts/`
- [ ] Comprehensive testing (real data, no mocks)
- [ ] Full documentation (AGENTS.md, README.md)
- [ ] Configuration files (config.yaml, references.bib)
- [ ] Validation and quality assurance
- [ ] Two-layer architecture compliance
- [ ] Thin orchestrator pattern implementation

## Standards Compliance Checklist

### Manuscript Standards ([`../../.cursorrules/manuscript_style.md`](../../.cursorrules/manuscript_style.md))
- [ ] Section numbering (01-09, S01-S0N, 98-99)
- [ ] Cross-references with proper labels
- [ ] Equation environments with labels
- [ ] Figure/table formatting with captions
- [ ] Citation format before punctuation
- [ ] Consistent terminology and notation

### Code Standards ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] Type hints on all public APIs
- [ ] Black formatting and isort imports
- [ ] Google-style docstrings
- [ ] Error handling with custom exceptions
- [ ] Unified logging system

### Testing Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] No mocks policy (real data only)
- [ ] 90% minimum coverage
- [ ] Test-driven development approach
- [ ] Integration testing for workflows

### Documentation Standards ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))
- [ ] AGENTS.md with complete technical documentation
- [ ] README.md with Mermaid diagrams
- [ ] Cross-references between documents
- [ ] Examples over explanations

## NOW HERE IS THE RESEARCH TOPIC AND OTHER CONTEXT:

...