# Manuscript Source

*A Configurable Advanced Literature Review (default search term: `{{SEARCH_TERM}}`) — phase-aware retrieval, de-duplication, bibliometrics, evidence, and reproducibility checks*

Author: Daniel Ari Friedman (Active Inference Institute)
License: CC-BY-4.0

---

## Section Map

| File | Section | Key Variables Injected | Generating Script |
| --- | --- | --- | --- |
| `00_abstract.md` | Abstract | `{{CORPUS_SIZE}}`, `{{YEAR_START}}`, `{{YEAR_END}}`, `{{CAGR_PCT}}`, `{{CITATION_EDGES}}`, `{{CITATION_RESOLUTION_PCT}}` | Stage 5 |
| `01_introduction.md` | Introduction | — | — |
| `02_methods_overview.md` | Methods overview | `{{CORPUS_SIZE}}` | Stage 5 |
| `02a_methods_retrieval.md` | Stage 1: retrieval | `{{CORPUS_SIZE}}`, `{{YEAR_START}}`, `{{YEAR_END}}` | Stage 1 + 5 |
| `02b_methods_extraction.md` | Stage 2: LLM extraction | `{{TOTAL_ASSERTIONS}}` | Stage 3 + 5 |
| `02c_methods_bibliometrics.md` | Stage 2: bibliometrics | `{{NUM_TOPICS}}`, `{{NUM_VOCAB_FEATURES}}` | Stage 2 + 5 |
| `02d_methods_knowledge_graph.md` | Stage 3: knowledge graph | `{{TOTAL_ASSERTIONS}}`, `{{CITATION_RESOLUTION_PCT}}` | Stage 3 + 5 |
| `02e_methods_viz_injection.md` | Stages 4–5 | `{{NUM_FIGURES}}` | Stage 4 + 5 |
| `03_results_hypothesis.md` | Hypothesis results | `{{N_HYPOTHESES}}`, `{{HYPOTHESIS_TABLE}}` and configuration-keyed score variables | Stage 3 + 5 |
| `03a_results_field_overview.md` | Field overview | generated corpus, temporal, and configured-subfield variables | Stage 2 + 5 |
| `03b_results_subfields.md` | Subfield analysis | counts and percentages for configured subfields | Stage 2 + 5 |
| `03c_results_text_analytics.md` | Text analytics | `{{NUM_TOPICS}}`, `{{NUM_VOCAB_FEATURES}}` | Stage 2 + 5 |
| `03d_results_citation_network.md` | Citation network | `{{CITATION_NODES}}`, `{{CITATION_EDGES}}`, `{{CITATION_DENSITY_PCT}}` | Stage 2 + 5 |
| `03e_results_reproducibility.md` | Reproducibility assessment | `{{REPRODUCIBILITY_MEAN_SCORE}}`, `{{REPRODUCIBILITY_N_PAPERS_SCORED}}`, `{{REPRODUCIBILITY_LOW_SCORE_COUNT}}` | Stage 5 |
| `04_discussion.md` | Discussion | — | — |
| `05_conclusion.md` | Conclusion | `{{CORPUS_SIZE}}`, `{{TOTAL_ASSERTIONS}}` | Stage 5 |
| `06_appendix_tooling.md` | Tooling appendix | — | — |
| `07_appendix_technical.md` | Technical appendix | — | — |
| `08_appendix_accessibility.md` | Accessibility appendix | — | — |
| `98_symbols_glossary.md` | Notation + glossary | — | — |
| `99_references.md` | Bibliography | — | — |

---

## Running Stage 5 (Variable Injection)

```bash
# From project root
PYTHONPATH=/path/to/template python scripts/05_inject_variables.py

# The source manuscript is never overwritten
PYTHONPATH=/path/to/template python scripts/05_inject_variables.py
```

Output goes to `output/manuscript/`. Source files in `manuscript/` are never overwritten.

---

## Adding New Citations

1. Add a BibTeX entry to `references.bib`
2. Use `\citep{key}` or `\citet{key}` in the relevant `.md` section
3. The build system resolves citations via the `references.bib` file during PDF rendering

---

## Configuration

All paper metadata, hypothesis definitions, subfield keywords, and pipeline parameters live in `config.yaml`. Editing `config.yaml` is the primary way to customize the pipeline without touching Python source code.

Key sections:
- `paper` — title, version
- `authors` — name, ORCID, affiliation
- `publication` — DOI, journal, year, license
- `hypothesis_definitions` — configuration-keyed review questions (controls LLM extraction)
- `subfield_keywords` — A1–C5 keyword lists (controls domain classification)
- `project_config.search` — arXiv queries, max results, resume behavior
- `project_config.knowledge_graph` — checkpointing, LLM model, temperature
