# Manuscript — Template Meta-Project

## Overview

Self-referential publication describing the Docxology Template architecture, published as the `template` project within the template itself.

## Chapters (8 files)

| File | Section | Content |
|------|---------|---------|
| `01_abstract.md` | Abstract | Dense single-paragraph summary with metrics |
| `02_introduction.md` | §1 Introduction | Reproducibility crisis, Related Work (6 tools), 4 pillars |
| `03_methods.md` | §2 Methods | Two-Layer Architecture, pipeline stages, AI collaboration |
| `04_results.md` | §3 Results | Multi-project metrics, module inventory, comparative feature matrix |
| `05_discussion.md` | §4 Discussion + Conclusion | Zero-Mock tradeoff, scalability, AI model, limitations |
| `06_infrastructure_modules.md` | §5 Module Reference | All 10 modules with file counts and key exports |
| `07_security_provenance.md` | §6 Security | Threat model, 4 steganographic layers, tamper detection |
| `08_appendices.md` | §7 Appendices | Pipeline reference, config, directory tree, tool comparison |

## References

21 BibTeX entries in `references.bib` covering: reproducibility crisis (Baker 2016, Freedman 2015, Peng 2011, Stodden 2016, Barba 2018), best practices (Sandve 2013, Wilson 2017), foundational (Knuth 1984, Gamma 1995), workflow tools (Snakemake, Nextflow, CWL), publication tools (R Markdown, Jupyter, Quarto), software engineering (Martin 2008), research compendia (Gentleman 2007, Boettiger 2015, Nüst 2017), FAIR principles (Wilkinson 2016, Barker 2022 FAIR4RS, Garijo 2024 FAIRsoft), research software definitions (Gruenpeter 2021), provenance (Moreau 2013 W3C PROV), supply chain integrity (Torres-Arias 2019 in-toto), AI coding (Lau 2025), literate programming (Schulte 2012).

## Key Metrics

- 3 exemplar projects: code_project (58 tests), cognitive_case_diagrams (257 tests), template (36 tests)
- 10 infrastructure modules, 137 Python files, 3,053 infrastructure tests
- 8 pipeline stages (00–07)
