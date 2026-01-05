# Manuscript Directory Documentation

## Overview

This directory contains the complete research manuscript for "Active Inference as a Meta-Pragmatic and Meta-Epistemic Method". The manuscript is structured with numbered sections, cross-references, and comprehensive documentation.

## File Structure

### Main Sections (01-09)
- `01_abstract.md` - Research overview and key contributions
- `02_introduction.md` - Motivation, background, and research questions
- `03_methodology.md` - Core \(2 \times 2\) framework and theoretical development
- `04_experimental_results.md` - Quadrant demonstrations and validation
- `05_discussion.md` - Theoretical implications and interpretations
- `06_conclusion.md` - Summary, contributions, and future directions
- `08_acknowledgments.md` - Funding and acknowledgments
- `09_appendix.md` - Technical details and extended derivations

### Supplemental Sections (S01-S03)
- `S01_supplemental_methods.md` - Extended methodological details
- `S02_supplemental_results.md` - Additional examples and analysis
- `S03_supplemental_analysis.md` - Advanced theoretical analysis

### Reference Sections (98-99)
- `98_symbols_glossary.md` - Mathematical notation and symbols
- `99_references.bib` - Bibliography in BibTeX format

### Configuration Files
- `config.yaml` - Paper metadata and rendering configuration
- `preamble.md` - LaTeX preamble customizations

## Section Numbering Convention

- **01-09**: Main manuscript sections
- **S01-S99**: Supplemental sections
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