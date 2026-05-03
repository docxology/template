# Manuscript Creation Prompt

## Purpose

Create a compliant research manuscript and project layout from a research description, aligned with this template’s architecture and rendering pipeline.

## Context

- [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) — **Canonical** Pandoc citation (`[@key]`) and `pandoc-crossref` (`@fig:`, `@eq:`, `@sec:`) semantics for the three exemplar projects.
- [`manuscript_cross_references.md`](manuscript_cross_references.md) — Projects that use **`manuscript/refs/labels.yaml`** and body tokens such as `[[FIG:…]]`, `[[THMREF:…]]` instead of (or as well as) `@fig:` / `\ref{}`.
- [`../rules/manuscript_style.md`](../rules/manuscript_style.md) — Sectioning, math, figures, tone.
- [`../rules/testing_standards.md`](../rules/testing_standards.md) — Project test policy (90%, no mocks).
- [`../core/workflow.md`](../core/workflow.md) — How manuscript, scripts, and pipeline connect.
- [`../usage/markdown-template-guide.md`](../usage/markdown-template-guide.md) — Markdown authoring details.

**Before choosing filenames:** copy the closest exemplar under [`projects/template_code_project/`](../../projects/template_code_project/), [`projects/template_prose_project/`](../../projects/template_prose_project/), or [`projects/template_search_project/`](../../projects/template_search_project/); do not assume the generic `01_abstract` / `02_introduction` skeleton below if your exemplar uses different numbering (`00_abstract`, themed sections, etc.).

## Prompt Template

```
You are creating a research manuscript from scratch using the Research Project Template. The manuscript must be compliant with all template standards and include a research project structure.

RESEARCH TOPIC: [Describe your research topic, objectives, methods, and expected contributions]

Create a manuscript with the following structure:

## 1. Manuscript Structure (File Set)

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
- `99_references.md` - bibliography

### Configuration Files
- `config.yaml` - Paper metadata, authors, publication info
- `references.bib` - BibTeX bibliography database
- `preamble.md` - LaTeX preamble customizations

## 2. Cross-referencing system

Prefer **Pandoc-crossref** field syntax and `[@citekey]` in Markdown source as in [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) (`@fig:`, `@eq:`, `@sec:`)—not raw `\ref{}` in prose, so HTML/EPUB stay coherent.

If the project uses **`refs/labels.yaml` + `[[FIG:]]` / `[[THMREF:]]` tokens**, follow [`manuscript_cross_references.md`](manuscript_cross_references.md) instead of duplicating numbering by hand.

Legacy LaTeX-style examples (for drafts that still emit `\ref` from Pandoc or appendices):

### Section references (illustrative)

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

Create a `src/` directory with research algorithms:

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
- docstrings (Google style)
- Error handling with custom exceptions
- Logging using `get_logger(__name__)`
- Pure functions where possible
- Reproducible results (fixed seeds)

## 4. Analysis Scripts

Create `scripts/` directory with thin orchestrators:

### Analysis Pipelines
- `analysis_pipeline.py` - research workflow
- `example_figure.py` - Figure generation examples
- Additional scripts for specific analyses

### Script Requirements
- Import from `src/` modules (no business logic in scripts)
- Handle I/O and configuration
- Use infrastructure modules for logging and validation
- Generate figures integrated with manuscript

## 5. Testing

Create `tests/` directory with test coverage:

### Test Structure
- `test_*.py` files matching `src/` modules
- 90% minimum coverage requirement
- **NO MOCKS** - use data only
- Integration tests for end-to-end workflows

### Testing Patterns
```python
def test_research_algorithm():
    """Test research algorithm with data."""
    # Generate or load actual test data
    test_data = generate_test_dataset()

    # Run algorithm
    result = research_algorithm(test_data)

    # Validate results with real assertions
    assert result.accuracy > 0.85
    assert result.is_valid
```

## 6. Documentation

Create documentation following standards:

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
- `references.bib` with all cited works
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
- mathematical derivations
- Clear figure and table presentation

## Key requirements

- [ ] Manuscript file set consistent with chosen exemplar (not necessarily generic 01–09)
- [ ] Cross-references per [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) and/or [`manuscript_cross_references.md`](manuscript_cross_references.md)
- [ ] Mathematical display and numbering per manuscript_style / exemplar
- [ ] Figures and tables with captions and resolvable references
- [ ] Research code in `projects/{name}/src/` (90% coverage) unless the change is infrastructure-layer
- [ ] Thin orchestrator scripts under `projects/{name}/scripts/`
- [ ] Tests with real data (no mocks of the unit under test)
- [ ] AGENTS.md and README.md where the template expects them
- [ ] `config.yaml` and bibliography sources (`references.bib` / `refs/citations.yaml`) aligned with body cites
- [ ] Pre-flight validation (markdown) and pipeline-aligned checks before declaring done

### Manuscript Standards ([`../rules/manuscript_style.md`](../rules/manuscript_style.md))
- [ ] Section numbering (01-09, S01-S0N, 98-99)
- [ ] Cross-references with proper labels
- [ ] Equation environments with labels
- [ ] Figure/table formatting with captions
- [ ] Citation format before punctuation
- [ ] Consistent terminology and notation

### Code Standards ([`../rules/code_style.md`](../rules/code_style.md))
- [ ] Type hints on all public APIs
- [ ] Black formatting and isort imports
- [ ] Google-style docstrings
- [ ] Error handling with custom exceptions
- [ ] Unified logging system

### Testing Standards ([`../rules/testing_standards.md`](../rules/testing_standards.md))
- [ ] No mocks policy (data only)
- [ ] 90% minimum coverage
- [ ] Test-driven development approach
- [ ] Integration testing for workflows

### Documentation Standards ([`../rules/documentation_standards.md`](../rules/documentation_standards.md))
- [ ] AGENTS.md with technical documentation
- [ ] README.md with Mermaid diagrams
- [ ] Cross-references between documents
- [ ] Examples over explanations

## NOW HERE IS THE RESEARCH TOPIC AND OTHER CONTEXT:

...