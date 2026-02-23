# Manuscript Directory Documentation

## Overview

This directory contains the research manuscript for "Active Inference as a Meta-Pragmatic and Meta-Epistemic Method". The manuscript is structured with numbered sections, cross-references, and documentation.

## File Structure

### Main Sections (01-07)

- `01_abstract.md` - Research overview and key contributions
- `02_background.md` - FEP foundations, EFE formulation, generative models, meta-aspects
- `03_quadrant_model.md` - Core 2×2 framework with Q1–Q4 demonstrations
- `04_security_implications.md` - Cognitive security, AI safety, defense strategies
- `05_discussion.md` - Theoretical contributions, implications, limitations, conclusions
- `06_acknowledgments.md` - Credits and acknowledgments
- `07_appendix.md` - Mathematical foundations, algorithms, benchmarks

### Reference Sections (98-99)

- `98_symbols_glossary.md` - Mathematical notation and symbols
- `99_references.md` - Bibliography references

### Configuration Files

- `config.yaml` - Paper metadata and rendering configuration
- `preamble.md` - LaTeX preamble customizations
- `references.bib` - BibTeX bibliography

## Section Numbering Convention

- **01-07**: Main manuscript sections
- **98-99**: Reference and glossary sections

## Cross-Reference System

The manuscript uses LaTeX-style cross-references:

- `\\ref{sec:methodology}` - Section references
- `\\ref{fig:quadrant_matrix}` - Figure references
- `\\eqref{eq:efe}` - Equation references
- `\\cite{friston2010free}` - Citation references

## Rendering Pipeline

The manuscript can be processed through standard rendering pipelines:

1. Markdown files combined into single document
2. Cross-references resolved
3. LaTeX generated with proper formatting
4. PDF rendered with bibliography and figures
5. Validation checks performed

## Quality Assurance

- **Cross-reference validation**: All references must resolve
- **Figure integration**: All figures properly registered and linked
- **Bibliography formatting**: Consistent citation style
- **Mathematical notation**: Proper LaTeX rendering
- **Section numbering**: Sequential and consistent

## Maintenance

When modifying the manuscript:

1. Update cross-references if section numbers change
2. Register new figures with the figure manager
3. Update bibliography for new citations
4. Validate rendering after changes
5. Update this documentation as needed
