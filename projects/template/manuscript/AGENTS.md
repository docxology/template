# Manuscript — `template/` Meta-Project

## Overview

Self-referential publication describing the `template/` architecture, published as the `template` project within the template itself. This manuscript is built by the same pipeline it documents, serving as a live proof-of-concept for the system's self-referential capability.

## Chapters (21 files)

| File | Section | Content |
|------|---------|---------| 
| `01_abstract.md` | Abstract | Dense single-paragraph summary with key metrics |
| `02_introduction.md` | Introduction | Reproducibility crisis, Related Work (6 tool categories), gap analysis, 4 pillars |
| `03a_architecture.md` | Methods: Architecture | Two-Layer Architecture, Standalone Project Paradigm, Thin Orchestrator pattern |
| `03b_pipeline.md` | Methods: Pipeline | Ten-stage DAG pipeline (Stages 00–07) + interactive orchestrators |
| `03c_documentation.md` | Methods: Documentation | Documentation Duality, agentic skill architecture, MCP server mapping |
| `03d_fair_iac.md` | Methods: FAIR & IaC | FAIR4RS alignment, Infrastructure as Code for research |
| `03e_quality.md` | Methods: Quality | Zero-Mock testing policy, visualization standards |
| `04_results.md` | Results | Multi-project metrics, module inventory, steganographic benchmarks, comparative feature matrix |
| `05a_zeromock_tradeoff.md` | Discussion: Zero-Mock | Zero-Mock tradeoff analysis with philosophical grounding |
| `05b_scalability.md` | Discussion: Scalability | Scalability from 1 to N projects |
| `05c_comparison.md` | Discussion: Comparison | Tool comparison, FAIR4RS 2024-2026 update, research compendia |
| `05d_ai_collaboration.md` | Discussion: AI | AI collaboration model, learning curve, limitations |
| `05e_future_conclusion.md` | Discussion: Future | 10 future directions + conclusion |
| `06_infrastructure_modules.md` | Module Reference | All 14 modules with file counts, key components, and pipeline integration points |
| `07_security_provenance.md` | Security | Threat model, 4 steganographic layers, tamper detection, FAIR and PROV alignment |
| `08a_appendix_pipeline.md` | Appendix: Pipeline | Pipeline stage reference table |
| `08b_appendix_config.md` | Appendix: Configuration | `config.yaml` schema reference |
| `08c_appendix_directory.md` | Appendix: Directory | Repository directory structure |
| `08d_appendix_exemplars.md` | Appendix: Exemplars | Exemplar project summary table |
| `08e_appendix_docs.md` | Appendix: Documentation | Documentation inventory across five layers |
| `08f_appendix_matrix.md` | Appendix: Matrix | Comparative 14×10 tool matrix |

## References

62 BibTeX entries in `references.bib` covering: reproducibility crisis (Baker 2016, Freedman 2015, Peng 2011, Stodden 2016, Barba 2018), best practices (Sandve 2013, Wilson 2017, Piccolo 2016), foundational (Knuth 1984, Gamma 1995), workflow tools (Snakemake, Nextflow, CWL), publication tools (R Markdown, Jupyter, Quarto), software engineering (Martin 2008), research compendia (Gentleman 2007, Boettiger 2015, Nüst 2017), FAIR principles (Wilkinson 2016, Lamprecht 2020, Barker 2022 FAIR4RS, Goble 2020 FAIR-workflows, Garijo 2024 FAIRsoft, Honeyman 2024 FAIR4RS-review, ReSA 2024 actionable-FAIR4RS), research software engineering (Cohen 2021 four-pillars, Katz 2021 software-citation), provenance (Moreau 2013 W3C PROV), supply chain integrity (Torres-Arias 2019 in-toto, OpenSSF 2023 SLSA, NTIA 2021 SBOM), AI coding (Lau 2025, Zhao 2023 LLM-survey), literate programming (Schulte 2012).

## Key Metrics

- 3 exemplar projects: `code_project` (39 tests), `act_inf_metaanalysis` (505 tests), `template` (65 tests)
- ${module_count} infrastructure modules, ~${total_infra_python_files} Python files, ~${infra_test_count_approx} infrastructure tests
- 9 pipeline stages (Stages 00–07 plus clean step)
- 100% Documentation Duality coverage (all modules have both `AGENTS.md` and `README.md`)
