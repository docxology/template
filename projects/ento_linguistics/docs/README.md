# Ento-Linguistics Project Documentation

Reference materials and guides for the **Ento-Linguistic Domains** research project — studying how entomological metaphors permeate and shape scientific discourse across six analytical domains.

## Key Documents

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Technical overview of every doc in this directory |
| [development_workflow.md](development_workflow.md) | Environment setup, test commands (923 tests), script names, module paths |
| [manuscript_style_guide.md](manuscript_style_guide.md) | Figures, citations, equations, and cross-reference examples from the actual manuscript |
| [refactor_playbook.md](refactor_playbook.md) | Module dependency map, hotspots, and safe-change recipes |
| [standards_compliance.md](standards_compliance.md) | Compliance matrix with current project metrics (923 tests, 11 figures, live corpus stats) |
| [testing_expansion_plan.md](testing_expansion_plan.md) | Targeted testing additions across 40 test files |
| [validation_guide.md](validation_guide.md) | Preflight, figure, and manuscript validation commands |

## Quick Access

```bash
# Run the full test suite (923 tests)
uv run pytest tests/ -x -q

# Clean-slate figure regeneration (clears output/, rebuilds all 11 figures)
uv run python scripts/02_generate_figures.py

# Build corpus (stage 1)
uv run python scripts/01_build_corpus.py

# Validate manuscript figures and references
uv run python scripts/_manuscript_preflight.py --strict

# Run the full analysis pipeline
uv run python scripts/_analysis_pipeline.py
```

## Project Architecture

```
src/
├── analysis/          # term_extraction, text_analysis, semantic_entropy, cace_scoring,
│                      # discourse_analysis, discourse_patterns, domain_analysis,
│                      # conceptual_mapping, persuasive_analysis, rhetorical_analysis,
│                      # statistics, performance
├── core/              # exceptions, logging, metrics, parameters, validation,
│                      # validation_utils, markdown_integration, example
├── data/              # literature_mining, loader, data_generator, data_processing
├── pipeline/          # simulation, reporting
└── visualization/     # concept_visualization, statistical_visualization, figure_manager,
                       # plots, visualization
```

## Live Pipeline Stats (2026-02-24)

| Metric | Value |
|--------|-------|
| Tests | 953 pass |
| Figures generated | 11 |
| Corpus documents | 369 |
| Tokens | 48,952 |
| Unique token types | 7,067 |
| Extracted terms | 871 (223 domain-assigned) |

## See Also

- [`../src/AGENTS.md`](../src/AGENTS.md) — Source code documentation
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — Scripts documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — Test suite documentation
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
